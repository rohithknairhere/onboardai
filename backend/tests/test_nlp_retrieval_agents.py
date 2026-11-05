"""TC-27 to TC-34: NLP outputs, access-controlled retrieval and agent boundaries.

No language model is called anywhere in this file. Everything asserted here is
deterministic: trained classifiers, a vector index, and tool registries.
"""
import time

import pytest


# --- TC-27 --------------------------------------------------------------------
@pytest.mark.parametrize("message,expected_intent,expected_agent", [
    ("where do I upload my passport", "document_help", "Document Agent"),
    ("I still don't have access to AWS", "it_access", "IT Provisioning Agent"),
    ("when is my knowledge transfer session", "kt_schedule", "Knowledge Transfer Agent"),
    ("how many days of annual leave do I get", "policy_question", "Policy Agent"),
    ("this is the third time I've asked and nobody has replied", "escalation", "Escalation Agent"),
])
def test_tc27_intent_routing(message, expected_intent, expected_agent):
    """Input: a representative message per intent. Expect the right specialist."""
    from ml import nlp_models
    if not nlp_models.is_available():
        pytest.skip("NLP models not trained; run: python -m ml.train_nlp")

    a = nlp_models.analyse(message)
    assert a["intent"] == expected_intent, f"got {a['intent']} @ {a['intent_confidence']:.0%}"
    assert a["agent"] == expected_agent


# --- TC-28 (boundary) ---------------------------------------------------------
def test_tc28_ambiguous_message_is_not_confidently_routed():
    """Input: 'any update?'. Expect low confidence and no specialist routing.

    A message that carries no intent must not be forced into one.
    """
    from ml import nlp_models
    if not nlp_models.is_available():
        pytest.skip("NLP models not trained")

    a = nlp_models.analyse("any update?")
    assert a["routed"] is False, f"vague text routed to {a['agent']} @ {a['intent_confidence']:.0%}"


# --- TC-29 --------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("Thanks so much, everyone has been lovely!", "positive"),
    ("where do I upload my passport", "neutral"),
    ("I'm frustrated, nobody has replied and I'm losing patience.", "negative"),
])
def test_tc29_sentiment_classification(text, expected):
    """Input: one message per sentiment class. Expect the matching label."""
    from ml import nlp_models
    if not nlp_models.is_available():
        pytest.skip("NLP models not trained")
    assert nlp_models.analyse(text)["sentiment"] == expected


# --- TC-30 --------------------------------------------------------------------
def test_tc30_pii_is_removed_before_text_leaves_the_system():
    """Input: a message containing six identifier types. Expect all values stripped."""
    from ml import pii
    raw = ("email shreya.nair@example.com, phone 9876543210, Aadhaar 1234 5678 9012, "
           "PAN ABCDE1234F, account 50100234519987, IFSC HDFC0004512")
    clean, types = pii.redact(raw)

    for secret in ["shreya.nair@example.com", "9876543210", "1234 5678 9012",
                   "ABCDE1234F", "50100234519987", "HDFC0004512"]:
        assert secret not in clean, f"{secret} survived redaction"
    assert {"EMAIL", "AADHAAR", "IFSC", "ACCOUNT"} <= set(types)


# --- TC-31 --------------------------------------------------------------------
def test_tc31_retrieval_is_isolated_between_organisations():
    """Input: the same question from two organisations. Expect different, correct policies."""
    from ml import rag
    question = "how many days of annual leave do I get"

    a = rag.search(question, org_id="org_1", department="Engineering")
    b = rag.search(question, org_id="org_2", department="Operations")
    assert a and b, "retrieval returned nothing; run: python -m ml.knowledge_seed"

    assert "Nimbus" in a[0]["doc_title"]
    assert "Veltrix" in b[0]["doc_title"]
    assert all("Veltrix" not in r["doc_title"] for r in a), "org_1 saw org_2 documents"
    assert all("Nimbus" not in r["doc_title"] for r in b), "org_2 saw org_1 documents"


# --- TC-32 (access control) ---------------------------------------------------
def test_tc32_department_restricted_document_is_not_retrievable():
    """Input: a security question from a permitted and a non-permitted department."""
    from ml import rag
    q = "who can access production customer data"

    allowed = rag.search(q, org_id="org_1", department="Engineering")
    denied = rag.search(q, org_id="org_1", department="Sales")

    assert any("Information Security" in r["doc_title"] for r in allowed)
    assert all("Information Security" not in r["doc_title"] for r in denied), (
        "Sales retrieved an Engineering-restricted document")


# --- TC-33 --------------------------------------------------------------------
def test_tc33_specialist_tool_boundaries_are_enforced():
    """Input: each specialist's tool registry. Expect capabilities to be disjoint.

    Enforced by construction, so a prompt cannot talk an agent past it.
    """
    from agents import specialists
    from agents.specialists import Context, Handoff

    ctx = Context(emp_id="emp_1", org_id="org_1", department="Engineering")
    tools = {name: {t.name for t in specialists.build_tools(name, ctx, Handoff())}
             for name in specialists.SPECIALISTS}

    assert "complete_task" not in tools["Policy Agent"]
    assert "search_company_policy" not in tools["Onboarding Agent"]
    assert "raise_it_request" not in tools["Document Agent"]
    assert [n for n, t in tools.items() if "escalate_to_hr" in t] == ["Escalation Agent"]
    assert all("transfer_to_specialist" in t for t in tools.values())


# --- TC-34 (performance) ------------------------------------------------------
def test_tc34_classifier_and_retrieval_latency():
    """Input: 50 classifications and 50 retrievals. Expect a low per-call mean.

    These run inside the request path, so a regression is user-visible.
    """
    from ml import nlp_models, rag
    if not nlp_models.is_available():
        pytest.skip("NLP models not trained")

    nlp_models.analyse("warm up")
    rag.search("warm up", org_id="org_1", department="Engineering")

    t0 = time.perf_counter()
    for _ in range(50):
        nlp_models.analyse("where do I upload my passport")
    nlp_ms = (time.perf_counter() - t0) / 50 * 1000

    t0 = time.perf_counter()
    for _ in range(50):
        rag.search("annual leave", org_id="org_1", department="Engineering")
    rag_ms = (time.perf_counter() - t0) / 50 * 1000

    assert nlp_ms < 150, f"intent+sentiment averaged {nlp_ms:.1f}ms"
    assert rag_ms < 150, f"retrieval averaged {rag_ms:.1f}ms"
