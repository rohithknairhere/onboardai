"""Run the held-out evaluation and score it.

Routing, retrieval and document checks need no language model and finish in
seconds, so they can be run live in front of an audience. Full assistant
answers take roughly 20-45 seconds each on a local model, so those are run one
at a time and the last full run is cached to disk.
"""
import json
import shutil
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from evaluation import chat_cases, doc_cases

BACKEND = Path(__file__).resolve().parent.parent
GENERATED_DIR = Path(__file__).resolve().parent / "_generated"
# Copies an examiner can drag into the upload box by hand.
DEMO_COPY_DIR = BACKEND / "demo_documents" / "final_review"
ANSWERS_CACHE = BACKEND / "ml" / "artifacts" / "eval_answers.json"

INTENTS = ["document_help", "it_access", "kt_schedule", "policy_question",
           "status_check", "payroll_benefits", "escalation", "smalltalk"]
VERDICTS = ["auto_approved", "needs_review", "auto_rejected"]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Chatbot layer 1: routing
# ---------------------------------------------------------------------------

def run_routing() -> dict:
    from ml import nlp_models

    rows = []
    for case_id, text, intent, sentiment in chat_cases.ROUTING_CASES:
        started = time.perf_counter()
        a = nlp_models.analyse(text)
        ms = (time.perf_counter() - started) * 1000
        expected_agent = nlp_models.INTENT_TO_AGENT[intent]
        rows.append({
            "id": case_id, "message": text,
            "expected_intent": intent, "predicted_intent": a.get("intent"),
            "intent_confidence": a.get("intent_confidence"),
            "expected_agent": expected_agent, "routed_agent": a.get("agent"),
            "expected_sentiment": sentiment, "predicted_sentiment": a.get("sentiment"),
            "intent_correct": a.get("intent") == intent,
            "routing_correct": a.get("agent") == expected_agent,
            "sentiment_correct": a.get("sentiment") == sentiment,
            "ms": round(ms, 1),
        })

    n = len(rows)
    per_intent = {}
    for intent in INTENTS:
        subset = [r for r in rows if r["expected_intent"] == intent]
        per_intent[intent] = {
            "n": len(subset),
            "correct": sum(r["intent_correct"] for r in subset),
        }

    matrix = {e: {p: 0 for p in INTENTS} for e in INTENTS}
    for r in rows:
        if r["predicted_intent"] in INTENTS:
            matrix[r["expected_intent"]][r["predicted_intent"]] += 1

    return {
        "ran_at": _now(),
        "n": n,
        "intent_accuracy": sum(r["intent_correct"] for r in rows) / n,
        "routing_accuracy": sum(r["routing_correct"] for r in rows) / n,
        "sentiment_accuracy": sum(r["sentiment_correct"] for r in rows) / n,
        "mean_ms": sum(r["ms"] for r in rows) / n,
        "per_intent": per_intent,
        "confusion": {"labels": INTENTS, "matrix": matrix},
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Chatbot layer 2: retrieval
# ---------------------------------------------------------------------------

def _org_of(doc_id: str) -> str:
    return doc_id.split("__", 1)[0]


def run_retrieval() -> dict:
    from ml import rag

    rows = []
    for case in chat_cases.POLICY_CASES:
        emp = chat_cases.EMPLOYEES[case["emp_id"]]
        results = rag.search(case["question"], org_id=emp["org_id"],
                             department=emp["department"], k=3)
        top = results[0] if results else None
        top_score = top["score"] if top else 0.0
        found = [{"doc_id": r["doc_id"], "doc_title": r["doc_title"],
                  "section": r["section"], "score": round(r["score"], 3)} for r in results]

        if case["kind"] == "answer":
            hit1 = bool(top) and top["doc_id"] == case["doc"] and top["section"] == case["section"]
            hit3 = any(r["doc_id"] == case["doc"] and r["section"] == case["section"] for r in results)
            passed = hit1
            detail = ("Top result is the right section." if hit1 else
                      "Right section is in the top 3." if hit3 else "Right section not retrieved.")
        elif case["kind"] == "no_answer":
            hit1 = hit3 = None
            passed = top_score < rag.WEAK_MATCH_SCORE
            detail = (f"Best match {top_score:.2f} is below the {rag.WEAK_MATCH_SCORE} "
                      f"confidence bar, so the assistant is told to decline."
                      if passed else f"Best match {top_score:.2f} looks like an answer.")
        else:  # isolation
            hit1 = hit3 = None
            leaked = [r for r in results if _org_of(r["doc_id"]) == case["forbidden_org"]]
            passed = not leaked
            detail = ("No document from the other company was returned." if passed
                      else f"Leaked {leaked[0]['doc_title']}.")

        rows.append({
            "id": case["id"], "emp_id": case["emp_id"], "org": emp["org"],
            "kind": case["kind"], "question": case["question"],
            "expected": (f"{case['doc']} / {case['section']}" if case["kind"] == "answer"
                         else "decline" if case["kind"] == "no_answer"
                         else f"nothing from {case['forbidden_org']}"),
            "results": found, "top_score": round(top_score, 3),
            "hit_at_1": hit1, "hit_at_3": hit3, "passed": passed, "detail": detail,
        })

    answer_rows = [r for r in rows if r["kind"] == "answer"]
    return {
        "ran_at": _now(),
        "n": len(rows),
        "pass_rate": sum(r["passed"] for r in rows) / len(rows),
        "hit_at_1": sum(bool(r["hit_at_1"]) for r in answer_rows) / len(answer_rows),
        "hit_at_3": sum(bool(r["hit_at_3"]) for r in answer_rows) / len(answer_rows),
        "declines_correct": sum(r["passed"] for r in rows if r["kind"] == "no_answer"),
        "declines_total": sum(1 for r in rows if r["kind"] == "no_answer"),
        "isolation_correct": sum(r["passed"] for r in rows if r["kind"] == "isolation"),
        "isolation_total": sum(1 for r in rows if r["kind"] == "isolation"),
        "weak_match_score": rag.WEAK_MATCH_SCORE,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Chatbot layer 3: full answers from the language model
# ---------------------------------------------------------------------------

def _score_answer(case: dict, text: str) -> dict:
    lowered = (text or "").lower()
    declined = any(p in lowered for p in chat_cases.DECLINE_PHRASES)

    if case["kind"] == "answer":
        has_fact = any(f.lower() in lowered for f in case["facts"])
        section = case["section"].lower()
        cited = section in lowered or "policy" in lowered or "(" in lowered and "—" in lowered
        passed = has_fact and cited
        checks = [
            {"check": "Correct fact", "passed": has_fact,
             "detail": f"Looked for: {' / '.join(case['facts'])}"},
            {"check": "Cites the handbook", "passed": cited,
             "detail": f"Expected a reference to '{case['section']}'"},
        ]
    else:
        passed = declined
        checks = [{"check": "Declines instead of guessing", "passed": declined,
                   "detail": "The handbook has no answer for this employee."}]
    return {"passed": passed, "checks": checks}


def answer_case(case_id: str) -> dict:
    """Run one policy case through the full assistant and score the reply."""
    from agents import chatbot

    case = next((c for c in chat_cases.POLICY_CASES if c["id"] == case_id), None)
    if case is None:
        raise KeyError(case_id)

    started = time.perf_counter()
    # A separate conversation thread per case, so one case's history cannot
    # help or hurt the next, and the employee's own chat is left untouched.
    result = chatbot.process_chat_message(case["question"], case["emp_id"],
                                          thread_tag=f"eval:{case_id}:{time.time()}")
    seconds = time.perf_counter() - started
    scored = _score_answer(case, result["response"])

    row = {
        "id": case_id, "emp_id": case["emp_id"],
        "org": chat_cases.EMPLOYEES[case["emp_id"]]["org"],
        "kind": case["kind"], "question": case["question"],
        "response": result["response"], "specialist": result["specialist"],
        "transferred_from": result.get("transferred_from"),
        "seconds": round(seconds, 1), "ran_at": _now(), **scored,
    }
    _cache_answer(row)
    return row


def _cache_answer(row: dict):
    cache = cached_answers()
    cache["rows"][row["id"]] = row
    cache["updated_at"] = _now()
    ANSWERS_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def cached_answers() -> dict:
    if ANSWERS_CACHE.exists():
        try:
            return json.loads(ANSWERS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"updated_at": None, "rows": {}}


def answers_summary() -> dict:
    import llm_provider

    cache = cached_answers()
    rows = [cache["rows"][c["id"]] for c in chat_cases.POLICY_CASES if c["id"] in cache["rows"]]

    def check_count(kind, check):
        subset = [r for r in rows if r["kind"] == kind]
        hits = sum(any(ch["check"] == check and ch["passed"] for ch in r["checks"]) for r in subset)
        return {"passed": hits, "total": len(subset)}

    return {
        "fact_correct": check_count("answer", "Correct fact"),
        "cited": check_count("answer", "Cites the handbook"),
        "declined": {"passed": sum(r["passed"] for r in rows if r["kind"] != "answer"),
                     "total": sum(1 for r in rows if r["kind"] != "answer")},
        "updated_at": cache.get("updated_at"),
        "provider": llm_provider.active_provider(),
        "model": llm_provider.active_model(),
        "n": len(rows),
        "total_cases": len(chat_cases.POLICY_CASES),
        "pass_rate": (sum(r["passed"] for r in rows) / len(rows)) if rows else None,
        "mean_seconds": (sum(r["seconds"] for r in rows) / len(rows)) if rows else None,
        "cases": [{"id": c["id"], "emp_id": c["emp_id"], "kind": c["kind"],
                   "question": c["question"],
                   "org": chat_cases.EMPLOYEES[c["emp_id"]]["org"]}
                  for c in chat_cases.POLICY_CASES],
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Document verification
# ---------------------------------------------------------------------------

def _write_pdf(text: str, path: Path):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
        pdf.multi_cell(w=0, h=6, text=line if line.strip() else " ",
                       new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def _write_photo(path: Path):
    """A stand-in for a phone photo: an image with no text layer at all."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (900, 600), (236, 232, 220))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 860, 560], outline=(90, 70, 60), width=6)
    draw.rectangle([80, 120, 300, 400], fill=(180, 170, 160))
    for y in range(140, 420, 40):
        draw.line([340, y, 800, y], fill=(120, 110, 100), width=8)
    img.save(path)


def _filename(case: dict) -> str:
    slug = "".join(ch if ch.isalnum() else "_" for ch in case["title"].lower()).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    ext = "png" if case["text"] is None else "pdf"
    return f"{case['id']}_{slug}_EXPECT_{case['expected'].upper()}.{ext}"


def generate_documents() -> list[dict]:
    """Write every test document to disk and return the cases with paths."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_COPY_DIR.mkdir(parents=True, exist_ok=True)
    cases = doc_cases.build_cases()
    for case in cases:
        path = GENERATED_DIR / _filename(case)
        if case["text"] is None:
            _write_photo(path)
            case["content_type"] = "image/png"
        else:
            _write_pdf(case["text"], path)
            case["content_type"] = "application/pdf"
        case["path"] = path
        shutil.copyfile(path, DEMO_COPY_DIR / path.name)
    return cases


def run_documents() -> dict:
    from ml import pipeline

    rows = []
    for case in generate_documents():
        started = time.perf_counter()
        a = pipeline.analyse(case["path"], case["content_type"],
                             requirement_name=case["requirement"],
                             employee_name=case["employee"])
        ms = (time.perf_counter() - started) * 1000
        rows.append({
            "id": case["id"], "title": case["title"], "file": case["path"].name,
            "employee": case["employee"], "requirement": case["requirement"],
            "teaches": case["teaches"],
            "expected": case["expected"], "verdict": a["verdict"], "reason": a["reason"],
            "passed": a["verdict"] == case["expected"],
            "predicted_type": a["predicted_type"],
            "confidence": a["predicted_confidence"],
            "checks": a["checks"],
            "fields": {
                "names": a["extracted_fields"].get("names", []),
                "expiry": a["extracted_fields"].get("dates", {}).get("expiry"),
                "signature": a["extracted_fields"].get("signature_state"),
                "identifiers": a["extracted_fields"].get("identifiers", {}),
            },
            "extraction": a["extraction"]["method"],
            "ms": round(ms, 1),
        })

    matrix = {e: {p: 0 for p in VERDICTS} for e in VERDICTS}
    for r in rows:
        matrix[r["expected"]][r["verdict"]] += 1

    wrongly_approved = [r["id"] for r in rows
                        if r["verdict"] == "auto_approved" and r["expected"] != "auto_approved"]
    return {
        "ran_at": _now(),
        "n": len(rows),
        "accuracy": sum(r["passed"] for r in rows) / len(rows),
        "wrongly_approved": wrongly_approved,
        "mean_ms": sum(r["ms"] for r in rows) / len(rows),
        "confusion": {"labels": VERDICTS, "matrix": matrix},
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Live probes for "type anything" demos
# ---------------------------------------------------------------------------

def probe_message(text: str) -> dict:
    """Everything the classifiers decide about a message, without calling the LLM."""
    from ml import nlp_models, pii

    started = time.perf_counter()
    a = nlp_models.analyse(text)
    intent_scores, sentiment_scores = {}, {}
    if a.get("available"):
        intent_bundle = nlp_models._load(nlp_models.INTENT_PATH, "intent")
        sentiment_bundle = nlp_models._load(nlp_models.SENTIMENT_PATH, "sentiment")
        _, _, intent_scores = nlp_models._predict(intent_bundle, text)
        _, _, sentiment_scores = nlp_models._predict(sentiment_bundle, text)
    redacted, types = pii.redact(text)
    return {
        "intent": a.get("intent"), "intent_confidence": a.get("intent_confidence"),
        "agent": a.get("agent"), "routed": a.get("routed", False),
        "confidence_floor": nlp_models.INTENT_CONFIDENCE_FLOOR,
        "sentiment": a.get("sentiment"), "sentiment_score": a.get("sentiment_score"),
        "intent_scores": dict(sorted(intent_scores.items(), key=lambda kv: -kv[1])),
        "sentiment_scores": sentiment_scores,
        "redacted_text": redacted, "redacted_types": types,
        "ms": round((time.perf_counter() - started) * 1000, 1),
    }


def probe_retrieval(question: str, emp_id: str) -> dict:
    from ml import rag

    emp = chat_cases.EMPLOYEES.get(emp_id) or chat_cases.EMPLOYEES["emp_1"]
    results = rag.search(question, org_id=emp["org_id"], department=emp["department"], k=3)
    return {
        "org": emp["org"], "weak_match_score": rag.WEAK_MATCH_SCORE,
        "relevance_floor": rag.RELEVANCE_FLOOR,
        "results": [{"doc_title": r["doc_title"], "section": r["section"],
                     "score": round(r["score"], 3), "text": r["text"]} for r in results],
    }


def summary_counts(rows, key) -> dict:
    return dict(Counter(r[key] for r in rows))


__all__ = ["run_routing", "run_retrieval", "answer_case", "answers_summary",
           "run_documents", "generate_documents", "probe_message", "probe_retrieval"]
