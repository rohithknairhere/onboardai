"""Synthetic onboarding journeys for the stall-risk model.

Rather than sampling features independently and deriving a label from them --
which produces an unrealistically separable problem -- this models three latent
traits per hire and treats the observable features as noisy measurements of
them:

    engagement  how proactively the hire works through onboarding
    friction    how much the process itself obstructs them
    support     quality of their manager, buddy and HR contact

The outcome depends on those latents plus a genuinely unobserved component, so
no feature set can predict it perfectly. That ceiling is the point: a model that
scores 1.0 here would mean the generator leaked the answer.
"""
import numpy as np

FEATURES = [
    "days_since_start",
    "stage",
    "progress",
    "pct_tasks_complete",
    "days_since_last_activity",
    "docs_pending",
    "docs_rejected",
    "doc_resubmissions",
    "kt_completed_pct",
    "chat_messages",
    "avg_sentiment",
    "seniority",
]

# `response_latency_hours` and `is_remote` were previously in FEATURES. Neither is
# recoverable from the production data model -- there is no remote-working field,
# and employee reply timings are not recorded -- so at serving time both arrived
# as hardcoded constants while the model had been trained on varying values.
# That is train/serve skew: two coefficients were being applied to information
# the model never actually received.
#
# They are still simulated below and still influence the outcome, they are simply
# no longer offered as observable inputs. That is the more faithful arrangement:
# real causes the system cannot measure belong in the unobserved component, not
# in the feature vector.

TARGET = "stalled"

# Departments differ in how document-heavy and regulated their onboarding is.
DEPARTMENT_FRICTION = {
    "Engineering": -0.15,
    "Design": -0.25,
    "Operations": 0.45,
    "Supply Chain": 0.20,
    "Legal": 0.35,
    "Sales": -0.05,
}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def generate(n=6000, seed=42):
    """Return (X, y, feature_names, departments) as numpy arrays."""
    rng = np.random.default_rng(seed)

    departments = rng.choice(list(DEPARTMENT_FRICTION), size=n)
    dept_effect = np.array([DEPARTMENT_FRICTION[d] for d in departments])

    engagement = rng.normal(0, 1, n)
    friction = rng.normal(0, 1, n) + dept_effect
    support = rng.normal(0, 1, n)

    seniority = rng.integers(0, 3, n)          # 0 junior, 1 mid, 2 senior
    is_remote = rng.binomial(1, 0.35, n)

    # Remote hires with weak support drift more easily.
    engagement = engagement - 0.25 * is_remote * (support < 0)

    days_since_start = rng.integers(3, 61, n)
    elapsed = days_since_start / 60.0

    pct_tasks_complete = np.clip(
        _sigmoid(1.1 * engagement - 0.5 * friction + rng.normal(0, 0.55, n)) * (0.35 + 0.75 * elapsed),
        0, 1,
    )
    progress = np.clip(pct_tasks_complete * 100 + rng.normal(0, 9, n), 0, 100)
    stage = np.clip(np.round(progress / 20), 0, 5)

    days_since_last_activity = np.clip(
        rng.exponential(np.exp(0.75 - 0.65 * engagement + 0.30 * friction)), 0, 30,
    )

    # Most onboardings have no rejected document at all (mean ~0.27), so a
    # rejection is a genuine anomaly rather than the norm.
    docs_rejected = rng.poisson(np.clip(np.exp(-1.6 + 0.75 * friction), 0.01, 6))
    doc_resubmissions = np.clip(
        docs_rejected + rng.poisson(np.clip(0.25 * friction + 0.3, 0.02, 4)), 0, 9,
    )
    docs_pending = np.clip(
        rng.poisson(np.clip(np.exp(0.35 + 0.55 * friction - 0.75 * engagement), 0.05, 7)), 0, 9,
    )

    kt_completed_pct = np.clip(
        _sigmoid(0.9 * engagement + 0.6 * support - 0.3 * friction + rng.normal(0, 0.6, n)) * (0.2 + 0.85 * elapsed),
        0, 1,
    ) * 100

    chat_messages = rng.poisson(np.clip(np.exp(1.5 + 0.45 * engagement + 0.25 * friction), 0.5, 60))
    response_latency_hours = np.clip(
        rng.gamma(2.0, np.clip(3.0 - 1.0 * engagement + 0.8 * friction, 0.5, 14)), 0.2, 96,
    )

    # Sentiment is the strongest single signal, but deliberately noisy: people
    # are polite in writing even when an onboarding is going badly.
    avg_sentiment = np.clip(
        np.tanh(0.55 * engagement - 0.85 * friction + 0.45 * support + rng.normal(0, 0.75, n)),
        -1, 1,
    )

    unobserved = rng.normal(0, 1, n)
    stall_logit = (
        -0.75
        + 1.10 * friction
        - 1.05 * engagement
        - 0.55 * support
        + 0.85 * unobserved
        + 0.35 * is_remote
        - 0.20 * seniority
        # Direct blocking effects, not mediated by the latents: a rejected
        # document and a silent hire each stall onboarding on their own.
        + 0.42 * np.minimum(docs_rejected, 3)
        + 0.055 * days_since_last_activity
    )
    stalled = rng.binomial(1, _sigmoid(stall_logit))

    X = np.column_stack([
        days_since_start, stage, progress, pct_tasks_complete,
        days_since_last_activity, docs_pending, docs_rejected, doc_resubmissions,
        kt_completed_pct, chat_messages, avg_sentiment, seniority,
    ]).astype(float)

    return X, stalled.astype(int), list(FEATURES), departments
