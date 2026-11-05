"""Train and evaluate the onboarding stall-risk model.

Run from the backend directory:
    python -m ml.train_risk
"""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    classification_report, roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml import risk_synth

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS / "risk_model.joblib"
METRICS_PATH = ARTIFACTS / "risk_metrics.json"
REPORT_PATH = ARTIFACTS / "risk_report.md"

MODEL_VERSION = "risk-v1"

# Features whose individual contribution is worth measuring. Sentiment is the
# NLP layer's contribution to the ML layer, so its ablation is the evidence
# that the pillars actually depend on each other.
ABLATION_TARGETS = ["avg_sentiment", "days_since_last_activity", "docs_rejected"]


def candidates():
    return {
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
            l2_regularization=1.0, random_state=42,
        ),
        "logistic_regression": Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, C=1.0)),
        ]),
    }


def _evaluate(model, X_test, y_test):
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    return {
        "roc_auc": roc_auc_score(y_test, proba),
        "pr_auc": average_precision_score(y_test, proba),
        "brier": brier_score_loss(y_test, proba),
        "accuracy": accuracy_score(y_test, preds),
    }, proba


def _calibration(y_test, proba, bins=5):
    edges = np.linspace(0, 1, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (proba >= lo) & (proba < hi if hi < 1 else proba <= hi)
        if mask.sum() == 0:
            continue
        rows.append({
            "bucket": f"{lo:.1f}-{hi:.1f}",
            "n": int(mask.sum()),
            "predicted": float(proba[mask].mean()),
            "observed": float(y_test[mask].mean()),
        })
    return rows


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic onboarding journeys...")
    X, y, feature_names, _ = risk_synth.generate()
    print(f"  {len(X)} journeys, stall rate {y.mean():.1%}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    results, fitted = {}, {}
    for name, model in candidates().items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        metrics, _ = _evaluate(model, X_test, y_test)
        results[name] = metrics
        fitted[name] = model
        print(f"  ROC-AUC={metrics['roc_auc']:.4f}  PR-AUC={metrics['pr_auc']:.4f} "
              f" Brier={metrics['brier']:.4f}")

    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best = fitted[best_name]
    print(f"\nBest model: {best_name}")

    _, proba = _evaluate(best, X_test, y_test)
    preds = (proba >= 0.5).astype(int)

    print("Running 5-fold cross-validation...")
    cv = cross_val_score(best, X, y, cv=5, scoring="roc_auc", n_jobs=-1)
    print(f"  cv ROC-AUC: {cv.mean():.4f} (+/- {cv.std():.4f})")

    print("Computing permutation importance...")
    perm = permutation_importance(best, X_test, y_test, n_repeats=8,
                                  random_state=42, scoring="roc_auc", n_jobs=-1)
    importance = sorted(
        ({"feature": f, "importance": float(m), "std": float(s)}
         for f, m, s in zip(feature_names, perm.importances_mean, perm.importances_std)),
        key=lambda r: r["importance"], reverse=True,
    )

    print("Running ablations...")
    ablations = {}
    base_auc = results[best_name]["roc_auc"]
    for feature in ABLATION_TARGETS:
        idx = feature_names.index(feature)
        keep = [i for i in range(len(feature_names)) if i != idx]
        model = candidates()[best_name]
        model.fit(X_train[:, keep], y_train)
        auc = roc_auc_score(y_test, model.predict_proba(X_test[:, keep])[:, 1])
        ablations[feature] = {"roc_auc": auc, "delta": auc - base_auc}
        print(f"  without {feature:26s} ROC-AUC={auc:.4f}  ({auc - base_auc:+.4f})")

    metrics = {
        "model_version": MODEL_VERSION,
        "selected_model": best_name,
        "comparison": results,
        "features": feature_names,
        "stall_rate": float(y.mean()),
        "cv_roc_auc_mean": float(cv.mean()),
        "cv_roc_auc_std": float(cv.std()),
        "permutation_importance": importance,
        "ablations": ablations,
        "calibration": _calibration(y_test, proba),
        "classification_report": classification_report(y_test, preds, output_dict=True,
                                                       zero_division=0),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }

    joblib.dump({"model": best, "features": feature_names,
                 "model_version": MODEL_VERSION}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_report(metrics)

    print(f"\nSaved model   -> {MODEL_PATH}")
    print(f"Saved report  -> {REPORT_PATH}")
    print("\n" + classification_report(y_test, preds, zero_division=0))


def _write_report(m):
    lines = [
        "# Onboarding Stall-Risk Model — Evaluation Report",
        "",
        f"- Model version: `{m['model_version']}`",
        f"- Selected model: **{m['selected_model']}**",
        f"- Train / test: {m['train_size']} / {m['test_size']}",
        f"- Base stall rate: {m['stall_rate']:.1%}",
        f"- 5-fold CV ROC-AUC: **{m['cv_roc_auc_mean']:.4f} ± {m['cv_roc_auc_std']:.4f}**",
        "",
        "## Model comparison",
        "",
        "| Model | ROC-AUC | PR-AUC | Brier | Accuracy |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, r in m["comparison"].items():
        lines.append(f"| {name} | {r['roc_auc']:.4f} | {r['pr_auc']:.4f} "
                     f"| {r['brier']:.4f} | {r['accuracy']:.4f} |")

    lines += ["", "## Ablations", "",
              "Each row retrains the model with one feature removed. A negative delta",
              "means the feature was carrying real signal.", "",
              "| Removed feature | ROC-AUC | Δ |", "| --- | --- | --- |"]
    for feature, r in m["ablations"].items():
        lines.append(f"| {feature} | {r['roc_auc']:.4f} | {r['delta']:+.4f} |")

    lines += ["", "## Permutation importance", "",
              "| Feature | Importance | Std |", "| --- | --- | --- |"]
    for r in m["permutation_importance"]:
        lines.append(f"| {r['feature']} | {r['importance']:.4f} | {r['std']:.4f} |")

    lines += ["", "## Calibration", "",
              "Predicted probability versus observed stall rate on held-out data.", "",
              "| Predicted bucket | N | Mean predicted | Observed |",
              "| --- | --- | --- | --- |"]
    for r in m["calibration"]:
        lines.append(f"| {r['bucket']} | {r['n']} | {r['predicted']:.3f} | {r['observed']:.3f} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
