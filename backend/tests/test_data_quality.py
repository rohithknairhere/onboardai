"""TC-01 to TC-08: data quality and validation checks on the three datasets.

These are the checks a tester runs before anyone trains anything: is the data
present, complete, balanced, correctly typed, and free of records that would
corrupt an evaluation.
"""
from collections import Counter

import numpy as np
import pytest


# --- TC-01 --------------------------------------------------------------------
def test_tc01_document_corpus_shape(document_corpus):
    """Input: generated document corpus. Expect 4,950 docs, 9 classes, aligned labels."""
    texts, labels, tiers = document_corpus
    assert len(texts) == len(labels) == len(tiers), "parallel arrays must align"
    assert len(texts) == 4950
    assert len(set(labels)) == 9


# --- TC-02 --------------------------------------------------------------------
def test_tc02_no_empty_or_missing_records(document_corpus, message_corpus, risk_dataset):
    """Input: all three datasets. Expect zero empty strings and zero NaN values."""
    d_texts, _, _ = document_corpus
    m_texts, _, _ = message_corpus
    X, y, _, _ = risk_dataset

    assert not [t for t in d_texts if not t.strip()], "empty documents present"
    assert not [t for t in m_texts if not t.strip()], "empty messages present"
    assert np.isnan(X).sum() == 0, "NaN in the feature matrix"
    assert np.isnan(y).sum() == 0, "NaN in the target"


# --- TC-03 --------------------------------------------------------------------
def test_tc03_document_classes_are_balanced(document_corpus):
    """Input: document labels. Expect every class within 1% of the mean count."""
    _, labels, _ = document_corpus
    counts = Counter(labels)
    ratio = min(counts.values()) / max(counts.values())
    assert ratio >= 0.99, f"document classes imbalanced (ratio {ratio:.3f})"


# --- TC-04 --------------------------------------------------------------------
def test_tc04_document_corpus_has_no_duplicates(document_corpus):
    """Input: document texts. Expect zero exact duplicates.

    Duplicates would let the same record sit in both folds and inflate scores.
    """
    texts, _, _ = document_corpus
    duplicates = len(texts) - len(set(texts))
    assert duplicates == 0, f"{duplicates} duplicate documents"


# --- TC-05 --------------------------------------------------------------------
def test_tc05_known_defect_message_corpus_contains_duplicates(message_corpus):
    """Input: message texts. KNOWN DEFECT: short messages repeat.

    This test documents a real, measured defect rather than asserting it away.
    It fails if duplication grows materially worse, and must be updated (with the
    leakage re-measured) if the corpus is ever deduplicated.
    """
    texts, _, _ = message_corpus
    duplicates = len(texts) - len(set(texts))
    assert duplicates > 0, "expected the known duplicate defect; corpus may have changed"
    assert duplicates / len(texts) < 0.10, (
        f"duplicate rate {duplicates/len(texts):.1%} exceeds the 10% tolerance")


# --- TC-06 --------------------------------------------------------------------
def test_tc06_risk_features_are_numeric_and_finite(risk_dataset):
    """Input: risk feature matrix. Expect float dtype, all finite, no constant columns."""
    X, _, features, _ = risk_dataset
    assert X.dtype.kind == "f", f"expected float features, got {X.dtype}"
    assert np.isfinite(X).all(), "non-finite values present"
    assert X.shape[1] == len(features) == 12

    constant = [f for i, f in enumerate(features) if X[:, i].std() == 0]
    assert not constant, f"zero-variance features would contribute nothing: {constant}"


# --- TC-07 --------------------------------------------------------------------
def test_tc07_target_is_binary_and_not_degenerate(risk_dataset):
    """Input: risk target. Expect values in {0,1} and a usable class balance."""
    _, y, _, _ = risk_dataset
    assert set(np.unique(y)) <= {0, 1}
    rate = y.mean()
    assert 0.20 < rate < 0.80, f"stall rate {rate:.1%} is too extreme to learn from"


# --- TC-08 --------------------------------------------------------------------
@pytest.mark.parametrize("feature,low,high", [
    ("progress", 0, 100),
    ("pct_tasks_complete", 0, 1),
    ("kt_completed_pct", 0, 100),
    ("avg_sentiment", -1, 1),
    ("stage", 0, 5),
    ("days_since_last_activity", 0, 30),
])
def test_tc08_features_respect_their_domain(risk_dataset, feature, low, high):
    """Input: each bounded feature. Expect values inside their declared range.

    A percentage above 100 or a sentiment above +1 means the generator is wrong.
    """
    X, _, features, _ = risk_dataset
    col = X[:, features.index(feature)]
    assert col.min() >= low, f"{feature} min {col.min()} below {low}"
    assert col.max() <= high, f"{feature} max {col.max()} above {high}"
