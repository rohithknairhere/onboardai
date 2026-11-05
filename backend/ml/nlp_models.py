"""Inference for the intent and sentiment classifiers."""
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
INTENT_PATH = ARTIFACTS / "intent_classifier.joblib"
SENTIMENT_PATH = ARTIFACTS / "sentiment_classifier.joblib"

# Below this the router should not commit to a specialist; a vague "any update?"
# is genuinely ambiguous and belongs with the general assistant.
INTENT_CONFIDENCE_FLOOR = 0.45

# Which specialist handles each intent. Shown in the UI and used for routing.
INTENT_TO_AGENT = {
    "document_help": "Document Agent",
    "it_access": "IT Provisioning Agent",
    "kt_schedule": "Knowledge Transfer Agent",
    "policy_question": "Policy Agent",
    "status_check": "Onboarding Agent",
    # Pay and benefits questions are answered from the same policy corpus, so
    # they go to the Policy agent rather than to a separate agent that would
    # hold identical tools.
    "payroll_benefits": "Policy Agent",
    "escalation": "Escalation Agent",
    "smalltalk": "Onboarding Agent",
}

_lock = threading.Lock()
_cache: dict[str, object] = {}
_attempted: set[str] = set()


def _load(path: Path, key: str):
    with _lock:
        if key in _attempted:
            return _cache.get(key)
        _attempted.add(key)
        if not path.exists():
            logger.warning("%s missing. Run: python -m ml.train_nlp", path.name)
            return None
        try:
            import joblib
            _cache[key] = joblib.load(path)
        except Exception:
            logger.exception("Failed to load %s", path.name)
            return None
        return _cache[key]


def is_available() -> bool:
    return _load(INTENT_PATH, "intent") is not None


def _predict(bundle, text):
    pipeline = bundle["pipeline"]
    probabilities = pipeline.predict_proba([text])[0]
    scores = {c: float(p) for c, p in zip(pipeline.classes_, probabilities)}
    label = max(scores, key=scores.get)
    return label, scores[label], scores


def analyse(text: str) -> dict:
    """Classify a message's intent and sentiment.

    `sentiment_score` is p(positive) - p(negative), which is smoother than the
    hard label and is what the risk model consumes as a feature.
    """
    result = {
        "intent": None, "intent_confidence": None, "agent": "Onboarding Agent",
        "sentiment": None, "sentiment_confidence": None, "sentiment_score": None,
        "available": False,
    }
    if not text or not text.strip():
        return result

    intent_bundle = _load(INTENT_PATH, "intent")
    sentiment_bundle = _load(SENTIMENT_PATH, "sentiment")
    if not intent_bundle or not sentiment_bundle:
        return result

    try:
        intent, intent_conf, _ = _predict(intent_bundle, text)
        sentiment, sentiment_conf, sentiment_scores = _predict(sentiment_bundle, text)
    except Exception:
        logger.exception("NLP inference failed")
        return result

    confident = intent_conf >= INTENT_CONFIDENCE_FLOOR
    result.update({
        "available": True,
        "intent": intent,
        "intent_confidence": intent_conf,
        "agent": INTENT_TO_AGENT.get(intent, "Onboarding Agent") if confident else "Onboarding Agent",
        "routed": confident,
        "sentiment": sentiment,
        "sentiment_confidence": sentiment_conf,
        "sentiment_score": sentiment_scores.get("positive", 0.0) - sentiment_scores.get("negative", 0.0),
    })
    return result
