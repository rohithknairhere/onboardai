"""Score a real employee's onboarding stall risk and explain the score.

Features are assembled from the live database and the event stream, so this
reads the same signals the model was trained on rather than a separate view.
"""
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dateutil import parser as date_parser

import models
from ml.risk_synth import FEATURES

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "risk_model.joblib"

_lock = threading.Lock()
_bundle = None
_load_attempted = False

# The training corpus spans 3-60 days; clamping keeps live inputs in range.
MIN_DAYS, MAX_DAYS = 3, 60

BANDS = ((0.65, "high"), (0.35, "moderate"), (0.0, "low"))

SENIORITY_KEYWORDS = {
    2: ("senior", "lead", "principal", "head", "manager", "director", "officer"),
    1: ("engineer", "designer", "analyst", "coordinator", "specialist"),
}

FEATURE_LABELS = {
    "days_since_start": "days since start date",
    "stage": "onboarding stage",
    "progress": "overall progress",
    "pct_tasks_complete": "share of tasks completed",
    "days_since_last_activity": "days since last activity",
    "docs_pending": "documents still pending",
    "docs_rejected": "documents rejected",
    "doc_resubmissions": "document resubmissions",
    "kt_completed_pct": "knowledge-transfer completion",
    "chat_messages": "assistant messages sent",
    "avg_sentiment": "sentiment of their messages",
    "seniority": "role seniority",
}


def _load():
    global _bundle, _load_attempted
    with _lock:
        if _load_attempted:
            return _bundle
        _load_attempted = True
        if not MODEL_PATH.exists():
            logger.warning("Risk model missing. Run: python -m ml.train_risk")
            return None
        try:
            import joblib
            _bundle = joblib.load(MODEL_PATH)
        except Exception:
            logger.exception("Failed to load risk model")
            _bundle = None
        return _bundle


def is_available() -> bool:
    return _load() is not None


def model_version() -> str | None:
    bundle = _load()
    return bundle.get("model_version") if bundle else None


def _seniority(role: str) -> int:
    lowered = (role or "").lower()
    for score, keywords in SENIORITY_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return score
    return 0


def _days_since(value, default):
    if not value:
        return default
    try:
        parsed = value if isinstance(value, datetime) else date_parser.parse(str(value))
    except (ValueError, OverflowError, TypeError):
        return default
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed).days


def build_features(db, employee) -> tuple[np.ndarray, dict]:
    tasks = employee.tasks or []
    docs = employee.requiredDocuments or []
    kt = employee.ktSections or []

    pct_tasks = (sum(1 for t in tasks if t.completed) / len(tasks)) if tasks else 0.0
    docs_pending = sum(1 for d in docs if d.status == "pending")
    docs_rejected = sum(1 for d in docs if d.status == "rejected")
    kt_pct = (sum(1 for k in kt if k.status == "completed") / len(kt) * 100) if kt else 0.0

    uploads = (
        db.query(models.DocumentUpload)
        .filter(models.DocumentUpload.empId == employee.id)
        .all()
    )
    # A resubmission is any upload beyond the first for a given requirement.
    per_requirement = {}
    for upload in uploads:
        per_requirement[upload.requiredDocId] = per_requirement.get(upload.requiredDocId, 0) + 1
    resubmissions = sum(max(0, n - 1) for n in per_requirement.values())

    events = (
        db.query(models.Event)
        .filter(models.Event.empId == employee.id)
        .order_by(models.Event.created_at.desc())
        .all()
    )
    chat_events = [e for e in events if e.event_type.startswith("chat.")]
    sentiments = [
        e.payload.get("sentiment") for e in chat_events
        if isinstance(e.payload, dict) and e.payload.get("sentiment") is not None
    ]

    days_since_activity = _days_since(events[0].created_at if events else None, default=7)
    days_since_start = _days_since(employee.startDate, default=MIN_DAYS)

    raw = {
        "days_since_start": float(np.clip(days_since_start, MIN_DAYS, MAX_DAYS)),
        "stage": float(employee.stage or 0),
        "progress": float(employee.progress or 0),
        "pct_tasks_complete": float(pct_tasks),
        "days_since_last_activity": float(np.clip(days_since_activity, 0, 30)),
        "docs_pending": float(docs_pending),
        "docs_rejected": float(docs_rejected),
        "doc_resubmissions": float(resubmissions),
        "kt_completed_pct": float(kt_pct),
        "chat_messages": float(len(chat_events)),
        "avg_sentiment": float(np.mean(sentiments)) if sentiments else 0.0,
        "seniority": float(_seniority(employee.role)),
    }
    vector = np.array([[raw[f] for f in FEATURES]], dtype=float)
    return vector, raw


def _contributions(model, vector) -> dict[str, float]:
    """Per-feature contribution to the log-odds.

    For a standardised linear model these are exactly the SHAP values, since
    coef * (x - mean) / std is the marginal contribution of each feature.
    """
    try:
        if hasattr(model, "named_steps") and "scale" in model.named_steps:
            scaler = model.named_steps["scale"]
            clf = model.named_steps["clf"]
            scaled = scaler.transform(vector)[0]
            return {f: float(c * v) for f, c, v in zip(FEATURES, clf.coef_[0], scaled)}

        import shap
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(vector)
        row = values[0] if not isinstance(values, list) else values[1][0]
        return {f: float(v) for f, v in zip(FEATURES, np.ravel(row))}
    except Exception:
        logger.exception("Risk explanation failed")
        return {}


def predict(db, employee) -> dict:
    bundle = _load()
    if not bundle:
        return {"available": False, "detail": "Risk model not trained. Run: python -m ml.train_risk"}

    vector, raw = build_features(db, employee)
    model = bundle["model"]

    try:
        probability = float(model.predict_proba(vector)[0, 1])
    except Exception:
        logger.exception("Risk scoring failed")
        return {"available": False, "detail": "Risk scoring failed."}

    band = next(name for threshold, name in BANDS if probability >= threshold)
    contributions = _contributions(model, vector)

    drivers = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    return {
        "available": True,
        "probability": probability,
        "band": band,
        "model_version": bundle.get("model_version"),
        "features": raw,
        "drivers": [
            {
                "feature": name,
                "label": FEATURE_LABELS.get(name, name),
                "value": raw.get(name),
                "contribution": value,
                "direction": "increases" if value > 0 else "reduces",
            }
            for name, value in drivers
        ],
    }
