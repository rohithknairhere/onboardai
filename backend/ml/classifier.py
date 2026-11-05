"""Loads the trained document-type classifier and serves predictions."""
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "doc_classifier.joblib"

_lock = threading.Lock()
_bundle = None
_load_attempted = False


def _load():
    global _bundle, _load_attempted
    with _lock:
        if _load_attempted:
            return _bundle
        _load_attempted = True
        if not MODEL_PATH.exists():
            logger.warning("Classifier artifact missing at %s. Run: python -m ml.train_classifier", MODEL_PATH)
            return None
        try:
            import joblib
            _bundle = joblib.load(MODEL_PATH)
        except Exception:
            logger.exception("Failed to load document classifier")
            _bundle = None
        return _bundle


def is_available() -> bool:
    return _load() is not None


def model_version() -> str | None:
    bundle = _load()
    return bundle.get("model_version") if bundle else None


def predict(text: str) -> dict:
    """Return {label, confidence, scores, model_version} or a null prediction."""
    empty = {"label": None, "confidence": None, "scores": {}, "model_version": None}
    if not text or not text.strip():
        return empty

    bundle = _load()
    if not bundle:
        return empty

    pipeline = bundle["pipeline"]
    try:
        probabilities = pipeline.predict_proba([text])[0]
    except Exception:
        logger.exception("Classifier inference failed")
        return empty

    classes = list(pipeline.classes_)
    scores = {cls: float(p) for cls, p in zip(classes, probabilities)}
    label = max(scores, key=scores.get)

    return {
        "label": label,
        "confidence": scores[label],
        "scores": dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True)),
        "model_version": bundle.get("model_version"),
    }
