"""Train the intent and sentiment classifiers.

Run from the backend directory:
    python -m ml.train_nlp
"""
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion

from ml import text_synth

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
INTENT_PATH = ARTIFACTS / "intent_classifier.joblib"
SENTIMENT_PATH = ARTIFACTS / "sentiment_classifier.joblib"
METRICS_PATH = ARTIFACTS / "nlp_metrics.json"
REPORT_PATH = ARTIFACTS / "nlp_report.md"

MODEL_VERSION = "nlp-v1"


def build_pipeline():
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                                     sublinear_tf=True, lowercase=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                     sublinear_tf=True, lowercase=True, max_features=50000)),
        ])),
        ("clf", LogisticRegression(max_iter=2000, C=6.0, class_weight="balanced")),
    ])


def _train_one(name, texts, labels):
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)

    classes = sorted(set(labels))
    cv = cross_val_score(pipe, texts, labels, cv=5, scoring="f1_macro", n_jobs=-1)

    metrics = {
        "accuracy": accuracy_score(y_test, preds),
        "macro_f1": f1_score(y_test, preds, average="macro"),
        "cv_macro_f1_mean": float(cv.mean()),
        "cv_macro_f1_std": float(cv.std()),
        "classes": classes,
        "per_class": classification_report(y_test, preds, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, preds, labels=classes).tolist(),
        "test_size": len(X_test),
    }
    print(f"  {name}: accuracy={metrics['accuracy']:.4f}  macro_f1={metrics['macro_f1']:.4f}  "
          f"cv={cv.mean():.4f}±{cv.std():.4f}")
    print(classification_report(y_test, preds, zero_division=0))
    return pipe, metrics


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic messages...")
    texts, intents, sentiments = text_synth.generate()
    print(f"  {len(texts)} messages, {len(set(intents))} intents, {len(set(sentiments))} sentiments\n")

    print("Intent classifier")
    intent_model, intent_metrics = _train_one("intent", texts, intents)

    print("\nSentiment classifier")
    sentiment_model, sentiment_metrics = _train_one("sentiment", texts, sentiments)

    joblib.dump({"pipeline": intent_model, "model_version": MODEL_VERSION}, INTENT_PATH)
    joblib.dump({"pipeline": sentiment_model, "model_version": MODEL_VERSION}, SENTIMENT_PATH)

    metrics = {"model_version": MODEL_VERSION,
               "intent": intent_metrics, "sentiment": sentiment_metrics}
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_report(metrics)

    print(f"\nSaved intent    -> {INTENT_PATH}")
    print(f"Saved sentiment -> {SENTIMENT_PATH}")
    print(f"Saved report    -> {REPORT_PATH}")


def _section(lines, title, m):
    lines += [f"## {title}", "",
              f"- Accuracy: **{m['accuracy']:.4f}**",
              f"- Macro-F1: **{m['macro_f1']:.4f}**",
              f"- 5-fold CV macro-F1: **{m['cv_macro_f1_mean']:.4f} ± {m['cv_macro_f1_std']:.4f}**",
              "", "| Class | Precision | Recall | F1 | Support |",
              "| --- | --- | --- | --- | --- |"]
    for cls in m["classes"]:
        r = m["per_class"].get(cls, {})
        lines.append(f"| {cls} | {r.get('precision', 0):.3f} | {r.get('recall', 0):.3f} "
                     f"| {r.get('f1-score', 0):.3f} | {int(r.get('support', 0))} |")
    lines += ["", "Confusion matrix (rows true, columns predicted):", "",
              "| | " + " | ".join(m["classes"]) + " |",
              "| --- |" + " --- |" * len(m["classes"])]
    for cls, row in zip(m["classes"], m["confusion_matrix"]):
        lines.append(f"| **{cls}** | " + " | ".join(str(v) for v in row) + " |")
    lines.append("")


def _write_report(m):
    lines = [f"# NLP Models — Evaluation Report", "",
             f"Model version: `{m['model_version']}`", ""]
    _section(lines, "Intent classification", m["intent"])
    _section(lines, "Sentiment classification", m["sentiment"])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
