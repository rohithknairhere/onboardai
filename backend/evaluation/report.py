"""Run the whole held-out evaluation and write docs/FINAL_EVALUATION.md.

Run from the backend directory:
    python -m evaluation.report            # everything, including the language model
    python -m evaluation.report --no-llm   # skip the slow full-answer layer, reuse the cache

The report is the backup for the live demo: if the laptop, the network or the
model misbehaves on the day, these are the same numbers from the same cases.
"""
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND / ".env")

from evaluation import chat_cases, runner  # noqa: E402

OUTPUT = BACKEND.parent / "docs" / "FINAL_EVALUATION.md"


def _pct(v):
    return "-" if v is None else f"{v * 100:.1f}%"


def _yes(b):
    return "pass" if b else "FAIL"


def main(run_llm: bool = True):
    print("Routing ...")
    routing = runner.run_routing()
    print("Retrieval ...")
    retrieval = runner.run_retrieval()
    print("Documents ...")
    documents = runner.run_documents()

    if run_llm:
        for case in chat_cases.POLICY_CASES:
            print(f"Answer {case['id']}: {case['question']}")
            row = runner.answer_case(case["id"])
            print(f"   {_yes(row['passed'])} in {row['seconds']}s via {row['specialist']}")
    answers = runner.answers_summary()

    out = []
    w = out.append
    w("# OnboardAI: Final Review Evaluation")
    w("")
    w(f"Generated {datetime.now():%d %B %Y, %H:%M} by `python -m evaluation.report`.")
    w("")
    w("Every case below was written by hand after the models were trained, in wording that does "
      "not come from the training data generators. The same cases run live in the app under "
      "**HR login > Evaluation Lab**.")
    w("")
    w("## Summary")
    w("")
    w("| What was tested | Cases | Result |")
    w("| --- | --- | --- |")
    w(f"| Chatbot routing: intent of a hand-written message | {routing['n']} | {_pct(routing['intent_accuracy'])} correct (93.7% on the synthetic test set) |")
    w(f"| Chatbot sentiment | {routing['n']} | {_pct(routing['sentiment_accuracy'])} correct |")
    w(f"| Policy search: right section ranked first | {sum(1 for r in retrieval['rows'] if r['kind'] == 'answer')} | {_pct(retrieval['hit_at_1'])} (top 3: {_pct(retrieval['hit_at_3'])}) |")
    w(f"| Policy search: finds nothing when the handbook has no answer | {retrieval['declines_total']} | {retrieval['declines_correct']} of {retrieval['declines_total']} |")
    w(f"| Policy search: never shows another company's handbook | {retrieval['isolation_total']} | {retrieval['isolation_correct']} of {retrieval['isolation_total']} |")
    w(f"| Full assistant answers: correct fact with citation, or honest decline | {answers['n']} | {_pct(answers['pass_rate'])}, mean {answers['mean_seconds'] or 0:.1f}s per reply ({answers['model']}) |")
    w(f"| Full answers: correct fact (handbook covers it) | {answers['fact_correct']['total']} | {answers['fact_correct']['passed']} of {answers['fact_correct']['total']} |")
    w(f"| Full answers: cites the handbook section | {answers['cited']['total']} | {answers['cited']['passed']} of {answers['cited']['total']} |")
    w(f"| Full answers: declines when it should (no answer, or other company only) | {answers['declined']['total']} | {answers['declined']['passed']} of {answers['declined']['total']} |")
    w(f"| Document verification: correct verdict | {documents['n']} | {_pct(documents['accuracy'])} |")
    w(f"| Document verification: bad documents wrongly approved | {documents['n']} | {len(documents['wrongly_approved'])} |")
    w("")
    w("## Main finding")
    w("")
    w(f"The intent classifier scores 93.7% on held-out synthetic messages but {_pct(routing['intent_accuracy'])} "
      "on messages written naturally by a person. The model learned the templates' vocabulary, so "
      "unfamiliar phrasing costs accuracy. The system tolerates this because every specialist agent "
      "can hand a conversation to the right one, and low-confidence messages go to the general "
      "Onboarding Agent instead of being forced into a specialist. The fix for the next version is "
      "training on real or more varied messages, not more of the same templates.")
    w("")

    w("## 1. Chatbot routing")
    w("")
    w("| Intent | Correct |")
    w("| --- | --- |")
    for intent, v in routing["per_intent"].items():
        w(f"| {intent.replace('_', ' ')} | {v['correct']} / {v['n']} |")
    w("")
    w("Misses:")
    w("")
    w("| Message | Expected | Predicted | Confidence |")
    w("| --- | --- | --- | --- |")
    for r in routing["rows"]:
        if not r["intent_correct"]:
            w(f"| {r['message']} | {r['expected_intent']} | {r['predicted_intent']} | {_pct(r['intent_confidence'])} |")
    w("")

    w("## 2. Policy search")
    w("")
    w("| Question | Asked by | Expected | Top result | Result |")
    w("| --- | --- | --- | --- | --- |")
    for r in retrieval["rows"]:
        top = f"{r['results'][0]['doc_title']} / {r['results'][0]['section']} ({r['results'][0]['score']})" if r["results"] else "nothing"
        w(f"| {r['question']} | {r['org']} | {r['expected']} | {top} | {_yes(r['passed'])} |")
    w("")

    w("## 3. Full assistant answers")
    w("")
    if answers["rows"]:
        for r in answers["rows"]:
            w(f"**{r['id']} ({_yes(r['passed'])}, {r['seconds']}s, {r['specialist']})**: {r['question']} *({r['org']})*")
            w("")
            w("> " + r["response"].replace("\n", "\n> "))
            w("")
    else:
        w("Not run. Use `python -m evaluation.report` without `--no-llm`.")
        w("")

    w("## 4. Document verification")
    w("")
    w("| Document | Uploaded as | Expected | Given | Reason |")
    w("| --- | --- | --- | --- | --- |")
    for r in documents["rows"]:
        w(f"| {r['title']} | {r['requirement']} | {r['expected']} | {r['verdict']} | {r['reason']} |")
    w("")
    w("The files are in `backend/demo_documents/final_review/` and can be uploaded by hand.")
    w("")

    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main(run_llm="--no-llm" not in sys.argv)
