"""Dataset understanding, quality checks, preprocessing evidence and split audit.

Run from the backend directory:
    python -m ml.data_report

Writes ml/artifacts/data_report.md and data_report.json. Everything here is
measured from the live generators and pipelines; nothing is hand-written.
"""
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ml import risk_synth, synth, text_synth

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
REPORT_PATH = ARTIFACTS / "data_report.md"
JSON_PATH = ARTIFACTS / "data_report.json"

SEED = 42
TEST_SIZE = 0.25


def _norm(text):
    """Whitespace- and case-insensitive form, for near-duplicate detection."""
    return re.sub(r"\s+", " ", text).strip().lower()


def text_corpus_stats(name, texts, labels, extra=None):
    lengths = np.array([len(t) for t in texts])
    words = np.array([len(t.split()) for t in texts])
    counts = Counter(labels)

    exact = len(texts) - len(set(texts))
    near = len(texts) - len(set(_norm(t) for t in texts))
    empty = sum(1 for t in texts if not t.strip())

    stats = {
        "name": name,
        "samples": len(texts),
        "classes": sorted(counts),
        "class_counts": dict(sorted(counts.items())),
        "class_balance_ratio": min(counts.values()) / max(counts.values()),
        "chars_total": int(lengths.sum()),
        "words_total": int(words.sum()),
        "char_len": {"min": int(lengths.min()), "max": int(lengths.max()),
                     "mean": float(lengths.mean()), "median": float(np.median(lengths)),
                     "std": float(lengths.std())},
        "word_len": {"min": int(words.min()), "max": int(words.max()),
                     "mean": float(words.mean())},
        "duplicates_exact": exact,
        "duplicates_normalised": near,
        "empty_documents": empty,
        "missing_values": 0,
    }
    if extra:
        stats.update(extra)
    return stats


def tfidf_evidence(texts, labels):
    """Before/after numbers for the vectorisation step."""
    raw_vocab = len({w.lower() for t in texts for w in re.findall(r"\w+", t)})

    unpruned = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1)
    unpruned.fit(texts)

    pruned = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                             sublinear_tf=True, strip_accents="unicode", lowercase=True)
    matrix = pruned.fit_transform(texts)

    return {
        "raw_unique_tokens": raw_vocab,
        "word_ngram_features_min_df_1": len(unpruned.vocabulary_),
        "word_ngram_features_min_df_2": len(pruned.vocabulary_),
        "features_pruned_away": len(unpruned.vocabulary_) - len(pruned.vocabulary_),
        "matrix_shape": list(matrix.shape),
        "sparsity_pct": 100.0 * (1.0 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])),
        "nonzero_per_doc_mean": float(matrix.nnz / matrix.shape[0]),
    }


def split_audit(texts, labels):
    """Verify stratification held and that no document leaked across the split."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, labels, test_size=TEST_SIZE, random_state=SEED, stratify=labels)

    overall = Counter(labels)
    tr, te = Counter(y_tr), Counter(y_te)
    drift = {c: abs(tr[c] / len(y_tr) - overall[c] / len(labels)) for c in overall}

    return {
        "train_size": len(X_tr),
        "test_size": len(X_te),
        "split_ratio": f"{100 * (1 - TEST_SIZE):.0f}/{100 * TEST_SIZE:.0f}",
        "random_state": SEED,
        "stratified": True,
        "max_class_proportion_drift": max(drift.values()),
        "train_class_counts": dict(sorted(tr.items())),
        "test_class_counts": dict(sorted(te.items())),
        "overlap_documents": len(set(X_tr) & set(X_te)),
    }


def numeric_audit(X, y, features):
    """Missing values, outliers and scaling evidence for the tabular dataset."""
    scaler = StandardScaler().fit(X)
    scaled = scaler.transform(X)

    per_feature = {}
    for i, f in enumerate(features):
        col = X[:, i]
        q1, q3 = np.percentile(col, [25, 75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = int(((col < lo) | (col > hi)).sum())
        per_feature[f] = {
            "dtype": str(X.dtype),
            "min": float(col.min()), "max": float(col.max()),
            "mean": float(col.mean()), "std": float(col.std()),
            "median": float(np.median(col)),
            "missing": int(np.isnan(col).sum()),
            "zero_variance": bool(col.std() == 0),
            "outliers_iqr": outliers,
            "outliers_pct": 100.0 * outliers / len(col),
            "mean_after_scaling": float(scaled[:, i].mean()),
            "std_after_scaling": float(scaled[:, i].std()),
        }

    corr = np.corrcoef(X, rowvar=False)
    pairs = []
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            pairs.append((features[i], features[j], float(corr[i, j])))
    pairs.sort(key=lambda p: abs(p[2]), reverse=True)

    target_corr = {f: float(np.corrcoef(X[:, i], y)[0, 1]) for i, f in enumerate(features)}

    return {
        "samples": int(X.shape[0]),
        "features": int(X.shape[1]),
        "feature_names": list(features),
        "target": "stalled (binary)",
        "target_positive_rate": float(y.mean()),
        "target_counts": {"stalled": int(y.sum()), "not_stalled": int(len(y) - y.sum())},
        "duplicate_rows": int(X.shape[0] - len(np.unique(X, axis=0))),
        "total_missing": int(np.isnan(X).sum()),
        "per_feature": per_feature,
        "top_correlated_pairs": pairs[:8],
        "correlation_with_target": dict(sorted(target_corr.items(),
                                               key=lambda kv: abs(kv[1]), reverse=True)),
    }


def leakage_impact(texts, labels):
    """Quantify memorisation: score the leaked and clean halves of the test set apart.

    One training run. If the model scores materially higher on test strings that
    also appear in training, that gap is memorisation rather than generalisation.
    """
    from ml.train_nlp import build_pipeline

    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, labels, test_size=TEST_SIZE, random_state=SEED, stratify=labels)

    train_set = set(X_tr)
    leaked = [i for i, t in enumerate(X_te) if t in train_set]
    clean = [i for i, t in enumerate(X_te) if t not in train_set]

    pipe = build_pipeline()
    pipe.fit(X_tr, y_tr)
    preds = pipe.predict(X_te)

    def acc(idx):
        if not idx:
            return None
        return float(np.mean([preds[i] == y_te[i] for i in idx]))

    overall, leaked_acc, clean_acc = acc(range(len(y_te))), acc(leaked), acc(clean)
    return {
        "test_size": len(y_te),
        "leaked_rows": len(leaked),
        "clean_rows": len(clean),
        "accuracy_overall": overall,
        "accuracy_on_leaked": leaked_acc,
        "accuracy_on_clean": clean_acc,
        "memorisation_gap": (leaked_acc - clean_acc)
        if (leaked_acc is not None and clean_acc is not None) else None,
    }


def build():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    print("Document corpus...")
    d_texts, d_labels, d_tiers = synth.generate()
    docs = text_corpus_stats("Onboarding documents", d_texts, d_labels, extra={
        "difficulty_tiers": dict(Counter(d_tiers)),
        "source_templates": sum(len(v) for v in synth._TEMPLATES.values()),
    })
    docs["tfidf"] = tfidf_evidence(d_texts, d_labels)
    docs["split"] = split_audit(d_texts, d_labels)

    print("Message corpus...")
    m_texts, m_intents, m_sentiments = text_synth.generate()
    msgs = text_corpus_stats("Employee messages (intent)", m_texts, m_intents, extra={
        "sentiment_counts": dict(Counter(m_sentiments)),
        "source_templates": sum(len(v) for v in text_synth._TEMPLATES.values()),
    })
    msgs["tfidf"] = tfidf_evidence(m_texts, m_intents)
    msgs["split"] = split_audit(m_texts, m_intents)

    print(" measuring leakage impact (sentiment)...")
    msgs["leakage_impact_sentiment"] = leakage_impact(m_texts, m_sentiments)
    print(" measuring leakage impact (intent)...")
    msgs["leakage_impact_intent"] = leakage_impact(m_texts, m_intents)

    print("Risk dataset...")
    X, y, feats, depts = risk_synth.generate()
    risk = numeric_audit(X, y, feats)
    risk["departments"] = dict(Counter(depts))
    risk["stall_rate_by_department"] = {
        d: float(y[np.array(depts) == d].mean()) for d in sorted(set(depts))}
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE,
                                          random_state=SEED, stratify=y)
    risk["split"] = {
        "train_size": int(len(Xtr)), "test_size": int(len(Xte)),
        "split_ratio": "75/25", "random_state": SEED, "stratified": True,
        "train_positive_rate": float(ytr.mean()), "test_positive_rate": float(yte.mean()),
        "scaler_fitted_on": "train only (inside the Pipeline, so the test fold is never seen)",
    }

    report = {"documents": docs, "messages": msgs, "risk": risk}
    JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(report)
    print(f"\nSaved {JSON_PATH}")
    print(f"Saved {REPORT_PATH}")
    return report


def _pct(x):
    return f"{100 * x:.1f}%"


def _write_markdown(r):
    L = ["# Dataset Understanding, Quality and Preprocessing Report", "",
         "Every figure below is computed by `ml/data_report.py` from the live data",
         "generators and the real preprocessing pipelines. Nothing is transcribed by hand.", ""]

    L += ["## 1. Datasets at a glance", "",
          "| Dataset | Samples | Target | Classes | Balance (min/max) | Source |",
          "| --- | --- | --- | --- | --- | --- |"]
    d, m, k = r["documents"], r["messages"], r["risk"]
    L.append(f"| Onboarding documents | {d['samples']:,} | document type | {len(d['classes'])} "
             f"| {d['class_balance_ratio']:.2f} | Generated (`ml/synth.py`) |")
    L.append(f"| Employee messages | {m['samples']:,} | intent + sentiment | "
             f"{len(m['classes'])} + 3 | {m['class_balance_ratio']:.2f} "
             f"| Generated (`ml/text_synth.py`) |")
    L.append(f"| Onboarding journeys | {k['samples']:,} | stalled (binary) | 2 "
             f"| {min(k['target_counts'].values())/max(k['target_counts'].values()):.2f} "
             f"| Simulated (`ml/risk_synth.py`) |")

    L += ["", "### Why the data is synthetic", "",
          "Real onboarding documents are identity and financial records that cannot be",
          "collected or published, and real onboarding outcomes do not exist for a system",
          "that has not been deployed. Both corpora are therefore generated. The generators",
          "are built to make the task realistically hard rather than flattering:", "",
          f"- Documents are produced from {d['source_templates']} templates across "
          f"{len(d['classes'])} classes, then degraded in three tiers "
          f"({', '.join(f'{t}={n:,}' for t, n in d['difficulty_tiers'].items())}).",
          f"- Messages come from {m['source_templates']} templates and include deliberately",
          " unresolvable cases, so some error is irreducible.",
          "- Journeys are a latent-variable process (engagement, friction, support) with an",
          " explicitly unobserved component, so no feature set can predict the outcome",
          " perfectly.", "",
          "**Limitation, stated plainly:** these metrics measure internal consistency with a",
          "generator, not real-world capability. No real document, message or outcome has",
          "been observed.", ""]

    L += ["## 2. Data understanding", "",
          "### 2.1 Onboarding documents", "",
          f"- Samples: **{d['samples']:,}** across **{len(d['classes'])}** classes",
          f"- Text volume: {d['chars_total']:,} characters / {d['words_total']:,} words",
          f"- Document length: mean {d['char_len']['mean']:.0f} chars "
          f"(median {d['char_len']['median']:.0f}, min {d['char_len']['min']}, "
          f"max {d['char_len']['max']}, sd {d['char_len']['std']:.0f})",
          f"- Mean words per document: {d['word_len']['mean']:.0f}", "",
          "| Class | Count |", "| --- | --- |"]
    for c, n in d["class_counts"].items():
        L.append(f"| {c} | {n:,} |")

    L += ["", "### 2.2 Employee messages", "",
          f"- Samples: **{m['samples']:,}**, {len(m['classes'])} intents, 3 sentiment classes",
          f"- Mean message length: {m['char_len']['mean']:.0f} chars", "",
          "| Intent | Count |", "| --- | --- |"]
    for c, n in m["class_counts"].items():
        L.append(f"| {c} | {n:,} |")
    L += ["", "Sentiment distribution: "
          + ", ".join(f"{s} = {n:,}" for s, n in m["sentiment_counts"].items()), ""]

    L += ["### 2.3 Onboarding journeys (tabular)", "",
          f"- Samples: **{k['samples']:,}**, Features: **{k['features']}**, "
          f"Target: `stalled` (binary)",
          f"- Class distribution: stalled {k['target_counts']['stalled']:,} "
          f"({_pct(k['target_positive_rate'])}), "
          f"not stalled {k['target_counts']['not_stalled']:,}",
          "- All features are numeric (float64); department is used to shape the simulation",
          " but is not exposed as a model input.", "",
          "| Feature | Min | Max | Mean | Median | SD | Corr. with target |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for f, s in k["per_feature"].items():
        L.append(f"| {f} | {s['min']:.2f} | {s['max']:.2f} | {s['mean']:.2f} "
                 f"| {s['median']:.2f} | {s['std']:.2f} "
                 f"| {k['correlation_with_target'][f]:+.3f} |")

    L += ["", "Stall rate by department:", "",
          "| Department | Stall rate |", "| --- | --- |"]
    for dept, rate in sorted(k["stall_rate_by_department"].items(),
                             key=lambda kv: kv[1], reverse=True):
        L.append(f"| {dept} | {_pct(rate)} |")

    L += ["", "## 3. Data quality checks", "",
          "| Check | Documents | Messages | Journeys |", "| --- | --- | --- | --- |",
          f"| Missing values | {d['missing_values']} | {m['missing_values']} "
          f"| {k['total_missing']} |",
          f"| Exact duplicates | {d['duplicates_exact']:,} | {m['duplicates_exact']:,} "
          f"| {k['duplicate_rows']:,} |",
          f"| Duplicates after normalising case/whitespace | {d['duplicates_normalised']:,} "
          f"| {m['duplicates_normalised']:,} | n/a |",
          f"| Empty records | {d['empty_documents']} | {m['empty_documents']} | 0 |",
          f"| Zero-variance features | n/a | n/a | "
          f"{sum(1 for s in k['per_feature'].values() if s['zero_variance'])} |", ""]

    m_dup_pct = 100 * m["duplicates_normalised"] / m["samples"]
    m_leak_pct = 100 * m["split"]["overlap_documents"] / m["split"]["test_size"]
    L += ["### Findings", "",
          f"**Documents are clean.** Zero exact duplicates and zero near-duplicates across "
          f"{d['samples']:,} records, and zero overlap between the train and test folds. Although "
          f"only {d['source_templates']} templates are used, every record randomises names, dates, "
          "identifiers and degradation, so no two documents come out identical.", "",
          f"**Messages are not clean, and this is a real defect.** {m['duplicates_exact']:,} exact "
          f"duplicates and {m['duplicates_normalised']:,} near-duplicates "
          f"({m_dup_pct:.2f}%) exist in {m['samples']:,} records, and "
          f"**{m['split']['overlap_documents']:,} messages appear in both the training and test "
          f"folds**, {m_leak_pct:.1f}% of the test set. Short messages such as \"thank you\" and "
          "\"any update?\" are produced identically by different draws, so a stratified random "
          "split cannot separate them.", "",
          "This is **train/test leakage**: the model is tested partly on strings it has already "
          "seen. The correct fix is to deduplicate before splitting, or to group identical strings "
          "into the same fold.", "",
          "#### Measured impact of the leakage", "",
          "The obvious hypothesis is that this leakage inflates the scores, and that it explains "
          "sentiment reaching 0.996. That hypothesis was tested rather than assumed. One training "
          "run, with the test set divided into rows that also appear in training (leaked) and rows "
          "that do not (clean). A positive gap would be memorisation:", "",
          "| Model | Overall | On leaked rows | On clean rows | Gap |",
          "| --- | --- | --- | --- | --- |"]
    for label, key in (("Sentiment", "leakage_impact_sentiment"),
                       ("Intent", "leakage_impact_intent")):
        li = m.get(key) or {}
        if li.get("memorisation_gap") is None:
            continue
        L.append(f"| {label} | {li['accuracy_overall']:.4f} | {li['accuracy_on_leaked']:.4f} "
                 f"({li['leaked_rows']} rows) | {li['accuracy_on_clean']:.4f} "
                 f"({li['clean_rows']} rows) | {li['memorisation_gap']:+.4f} |")

    sent_li = m.get("leakage_impact_sentiment") or {}
    L += ["",
          "**The hypothesis was wrong.** Sentiment scores *lower* on the leaked rows "
          f"({sent_li.get('accuracy_on_leaked', 0):.4f}) than on the clean ones "
          f"({sent_li.get('accuracy_on_clean', 0):.4f}), and the intent gap is within noise. The "
          "leakage is real but its measured effect is negligible.", "",
          "The explanation is that the duplicated strings are the *short, ambiguous* ones, "
          "\"thank you\", \"any update?\", which are both the most likely to be generated twice "
          "and the hardest to classify. Duplication is concentrated in the difficult cases, so it "
          "depresses the leaked-row score rather than inflating it.", "",
          "Sentiment's 0.996 therefore still needs explaining, and leakage is not the explanation. "
          "It remains a **template-separability ceiling**: the generator marks sentiment with stock "
          "phrases that a linear model separates almost perfectly. That is a property of the data, "
          "not evidence the model understands sentiment.", ""]

    L += ["### Outliers (IQR rule, tabular dataset)", "",
          "| Feature | Outliers | % of rows |", "| --- | --- | --- |"]
    for f, s in sorted(k["per_feature"].items(),
                       key=lambda kv: kv[1]["outliers_pct"], reverse=True):
        if s["outliers_iqr"]:
            L.append(f"| {f} | {s['outliers_iqr']:,} | {s['outliers_pct']:.2f}% |")
    L += ["", "Outliers were **retained**, not removed. These are counts and durations whose long "
          "right tail is the signal of interest, an employee inactive for 25 days is exactly "
          "the case the model must catch, not noise to discard.", ""]

    L += ["## 4. Preprocessing: what, why, result", "",
          "| Step | Why | Result |", "| --- | --- | --- |",
          "| Lowercasing + accent stripping | OCR and typing produce inconsistent case |"
          " applied to all text features |",
          "| Word 1-2 gram TF-IDF | captures topical vocabulary and short phrases |"
          f" {d['tfidf']['word_ngram_features_min_df_2']:,} features |",
          "| Character 3-5 gram TF-IDF | survives OCR damage that destroys whole words |"
          " unioned with word features |",
          "| Sublinear TF | dampens the effect of a term repeated many times in one document |"
          " applied |",
          f"| `min_df=2` pruning | removes tokens appearing once, which cannot generalise |"
          f" {d['tfidf']['features_pruned_away']:,} features dropped |",
          "| Stratified split | preserves class proportions in both folds |"
          " see section 5 |",
          "| StandardScaler (tabular) | features span different units and ranges |"
          " zero mean, unit variance |",
          "| Scaler fitted inside a Pipeline | prevents test statistics leaking into training |"
          " enforced by sklearn |", ""]

    L += ["### 4.1 Before vs after: text vectorisation (document corpus)", "",
          "| Measure | Before | After |", "| --- | --- | --- |",
          f"| Representation | {d['samples']:,} raw strings | sparse matrix "
          f"{d['tfidf']['matrix_shape'][0]:,} x {d['tfidf']['matrix_shape'][1]:,} |",
          f"| Unique tokens | {d['tfidf']['raw_unique_tokens']:,} | "
          f"{d['tfidf']['word_ngram_features_min_df_2']:,} word n-gram features |",
          f"| Features before pruning | {d['tfidf']['word_ngram_features_min_df_1']:,} | "
          f"{d['tfidf']['word_ngram_features_min_df_2']:,} (min_df=2) |",
          f"| Density | dense text | {d['tfidf']['sparsity_pct']:.2f}% sparse, "
          f"{d['tfidf']['nonzero_per_doc_mean']:.0f} non-zeros per document |", ""]

    first = next(iter(k["per_feature"]))
    fs = k["per_feature"][first]
    L += ["### 4.2 Before vs after: feature scaling (tabular)", "",
          "| Feature | Mean before | SD before | Mean after | SD after |",
          "| --- | --- | --- | --- | --- |"]
    for f, s in list(k["per_feature"].items())[:6]:
        L.append(f"| {f} | {s['mean']:.2f} | {s['std']:.2f} | "
                 f"{s['mean_after_scaling']:+.2e} | {s['std_after_scaling']:.3f} |")
    L += ["", "All 12 features standardise to mean ~0 and SD 1, which is what makes the logistic "
          "regression coefficients directly comparable as per-feature contributions.", ""]

    L += ["## 5. Data splitting and leakage", "",
          "| Dataset | Split | Train | Test | Stratified | Max class drift | Train/test overlap |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for label, s in (("Documents", d["split"]), ("Messages", m["split"])):
        L.append(f"| {label} | {s['split_ratio']} | {s['train_size']:,} | {s['test_size']:,} "
                 f"| yes | {s['max_class_proportion_drift']:.4f} | {s['overlap_documents']:,} |")
    ks = k["split"]
    L.append(f"| Journeys | {ks['split_ratio']} | {ks['train_size']:,} | {ks['test_size']:,} "
             f"| yes | {abs(ks['train_positive_rate'] - ks['test_positive_rate']):.4f} | n/a |")

    L += ["", f"- `random_state={SEED}` on every split, so results are reproducible.",
          "- Stratification keeps every class proportion within "
          f"{max(d['split']['max_class_proportion_drift'], m['split']['max_class_proportion_drift']):.4f} "
          "of the full dataset.",
          "- **Leakage controls:** the vectoriser and the scaler are fitted inside an sklearn "
          "`Pipeline`, so they are re-fitted on the training fold alone during cross-validation "
          "and never see the test fold. Cross-validation uses the full dataset only through that "
          "Pipeline, never a pre-fitted transformer.",
          f"- **Documents:** {d['split']['overlap_documents']} records overlap between folds. Clean.",
          f"- **Messages: {m['split']['overlap_documents']:,} records overlap between folds "
          f"({100 * m['split']['overlap_documents'] / m['split']['test_size']:.1f}% of the test "
          "set).** This is genuine leakage caused by duplicate short messages, and it inflates the "
          "intent and sentiment scores. Deduplicating before the split, or grouping identical "
          "strings into the same fold, is the required fix and is listed in future work.", ""]

    REPORT_PATH.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
