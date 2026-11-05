"""Train and evaluate the onboarding document-type classifier.

Run from the backend directory:
    python -m ml.train_classifier

Writes the fitted pipeline and a metrics report to ml/artifacts/.
"""
import json
import time
from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import LinearSVC

from ml import synth

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS / "doc_classifier.joblib"
METRICS_PATH = ARTIFACTS / "classifier_metrics.json"
REPORT_PATH = ARTIFACTS / "classifier_report.md"

MODEL_VERSION = "doc-clf-v1"


def build_features():
    """Word n-grams carry topic; char n-grams survive OCR damage that breaks words."""
    return FeatureUnion([
        ("word", TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), min_df=2,
            sublinear_tf=True, strip_accents="unicode", lowercase=True,
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=3,
            sublinear_tf=True, lowercase=True, max_features=60000,
        )),
    ])


def candidates():
    return {
        "logreg": Pipeline([
            ("features", build_features()),
            ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
        ]),
        "linearsvc_calibrated": Pipeline([
            ("features", build_features()),
            ("clf", CalibratedClassifierCV(
                LinearSVC(C=1.0, class_weight="balanced"), cv=3, method="sigmoid"
            )),
        ]),
    }


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic corpus...")
    texts, labels, tiers = synth.generate()
    print(f"  {len(texts)} documents across {len(set(labels))} classes")
    for tier in synth.DIFFICULTY_MIX:
        print(f"    {tier}: {tiers.count(tier)}")

    X_train, X_test, y_train, y_test, _, t_test = train_test_split(
        texts, labels, tiers, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"  train={len(X_train)}  test={len(X_test)}")

    results = {}
    fitted = {}

    for name, pipe in candidates().items():
        print(f"\nTraining {name}...")
        started = time.time()
        pipe.fit(X_train, y_train)
        elapsed = time.time() - started

        preds = pipe.predict(X_test)
        macro_f1 = f1_score(y_test, preds, average="macro")
        results[name] = {
            "accuracy": accuracy_score(y_test, preds),
            "macro_f1": macro_f1,
            "train_seconds": round(elapsed, 2),
        }
        fitted[name] = pipe
        print(f"  accuracy={results[name]['accuracy']:.4f}  macro_f1={macro_f1:.4f}  ({elapsed:.1f}s)")

    best_name = max(results, key=lambda n: results[n]["macro_f1"])
    best = fitted[best_name]
    print(f"\nBest model: {best_name}")

    preds = best.predict(X_test)
    labels_sorted = sorted(set(labels))
    report_dict = classification_report(y_test, preds, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, preds, labels=labels_sorted).tolist()

    per_tier = {}
    for tier in synth.DIFFICULTY_MIX:
        idx = [i for i, t in enumerate(t_test) if t == tier]
        if not idx:
            continue
        truth = [y_test[i] for i in idx]
        pred = [preds[i] for i in idx]
        per_tier[tier] = {
            "n": len(idx),
            "accuracy": accuracy_score(truth, pred),
            "macro_f1": f1_score(truth, pred, average="macro", zero_division=0),
        }
        print(f"  {tier:9s} n={len(idx):4d}  acc={per_tier[tier]['accuracy']:.4f}")

    print("Running 5-fold cross-validation...")
    cv = cross_val_score(best, texts, labels, cv=5, scoring="f1_macro", n_jobs=-1)
    print(f"  cv macro-F1: {cv.mean():.4f} (+/- {cv.std():.4f})")

    metrics = {
        "model_version": MODEL_VERSION,
        "selected_model": best_name,
        "comparison": results,
        "classes": labels_sorted,
        "test_accuracy": accuracy_score(y_test, preds),
        "test_macro_f1": f1_score(y_test, preds, average="macro"),
        "cv_macro_f1_mean": float(cv.mean()),
        "cv_macro_f1_std": float(cv.std()),
        "per_class": report_dict,
        "per_difficulty": per_tier,
        "confusion_matrix": cm,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }

    joblib.dump({"pipeline": best, "classes": labels_sorted,
                 "model_version": MODEL_VERSION}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_report(metrics)

    print(f"\nSaved model    -> {MODEL_PATH}")
    print(f"Saved metrics  -> {METRICS_PATH}")
    print(f"Saved report   -> {REPORT_PATH}")
    print("\n" + classification_report(y_test, preds, zero_division=0))


def _write_report(m):
    lines = [
        "# Document Classifier — Evaluation Report",
        "",
        f"- Model version: `{m['model_version']}`",
        f"- Selected model: **{m['selected_model']}**",
        f"- Train / test split: {m['train_size']} / {m['test_size']}",
        f"- Test accuracy: **{m['test_accuracy']:.4f}**",
        f"- Test macro-F1: **{m['test_macro_f1']:.4f}**",
        f"- 5-fold CV macro-F1: **{m['cv_macro_f1_mean']:.4f} ± {m['cv_macro_f1_std']:.4f}**",
        "",
        "## Model comparison",
        "",
        "| Model | Accuracy | Macro-F1 | Train time (s) |",
        "| --- | --- | --- | --- |",
    ]
    for name, r in m["comparison"].items():
        lines.append(f"| {name} | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | {r['train_seconds']} |")

    lines += ["", "## Performance by scan quality", "",
              "Documents are generated at three degradation tiers. `severe` simulates a",
              "cropped, heavily noised phone photo with cross-class text bleeding in.", "",
              "| Tier | N | Accuracy | Macro-F1 |", "| --- | --- | --- | --- |"]
    for tier, r in m.get("per_difficulty", {}).items():
        lines.append(f"| {tier} | {r['n']} | {r['accuracy']:.4f} | {r['macro_f1']:.4f} |")

    lines += ["", "## Per-class performance", "",
              "| Class | Precision | Recall | F1 | Support |", "| --- | --- | --- | --- | --- |"]
    for cls in m["classes"]:
        r = m["per_class"].get(cls, {})
        lines.append(
            f"| {cls} | {r.get('precision', 0):.3f} | {r.get('recall', 0):.3f} "
            f"| {r.get('f1-score', 0):.3f} | {int(r.get('support', 0))} |"
        )

    lines += ["", "## Confusion matrix", "",
              "Rows are true labels, columns predicted.", "",
              "| | " + " | ".join(m["classes"]) + " |",
              "| --- |" + " --- |" * len(m["classes"])]
    for cls, row in zip(m["classes"], m["confusion_matrix"]):
        lines.append(f"| **{cls}** | " + " | ".join(str(v) for v in row) + " |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
