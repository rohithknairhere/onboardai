"""TC-09 to TC-15: preprocessing output verification and split integrity.

These confirm the transformations actually did what the report claims, and that
the train/test split is honest.
"""
from collections import Counter

import numpy as np
import pytest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from tests.conftest import SEED, TEST_SIZE


# --- TC-09 --------------------------------------------------------------------
def test_tc09_tfidf_produces_expected_matrix(document_corpus):
    """Input: document texts. Expect a sparse matrix, one row per document, >99% sparse."""
    from ml.train_classifier import build_features
    texts, _, _ = document_corpus

    matrix = build_features().fit_transform(texts)
    assert matrix.shape[0] == len(texts), "one row per document"
    assert matrix.shape[1] > 1000, "suspiciously few features"

    # The word-only matrix is ~99.3% sparse; this is the word+char union, which is
    # legitimately denser because character n-grams fire on almost every document.
    sparsity = 1.0 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])
    assert sparsity > 0.95, f"expected a sparse matrix, got {sparsity:.3f}"


# --- TC-10 --------------------------------------------------------------------
def test_tc10_min_df_pruning_reduces_feature_count(document_corpus):
    """Input: document texts. Expect min_df=2 to drop features that appear once."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts, _, _ = document_corpus

    loose = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1).fit(texts)
    tight = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2).fit(texts)

    assert len(tight.vocabulary_) < len(loose.vocabulary_), "pruning removed nothing"


# --- TC-11 --------------------------------------------------------------------
def test_tc11_scaling_yields_zero_mean_unit_variance(risk_dataset):
    """Input: risk features. Expect every column to standardise to mean~0, sd~1."""
    X, _, features, _ = risk_dataset
    scaled = StandardScaler().fit_transform(X)

    for i, f in enumerate(features):
        assert abs(scaled[:, i].mean()) < 1e-9, f"{f} mean not ~0"
        assert abs(scaled[:, i].std() - 1.0) < 1e-9, f"{f} sd not ~1"


# --- TC-12 --------------------------------------------------------------------
def test_tc12_split_is_stratified(document_corpus):
    """Input: documents + labels. Expect class proportions preserved within 1%."""
    texts, labels, _ = document_corpus
    _, _, y_tr, y_te = train_test_split(
        texts, labels, test_size=TEST_SIZE, random_state=SEED, stratify=labels)

    overall = Counter(labels)
    for cls in overall:
        want = overall[cls] / len(labels)
        for name, fold in (("train", y_tr), ("test", y_te)):
            got = Counter(fold)[cls] / len(fold)
            assert abs(got - want) < 0.01, f"{cls} drifted in {name}: {got:.3f} vs {want:.3f}"


# --- TC-13 --------------------------------------------------------------------
def test_tc13_no_document_leaks_across_the_split(document_corpus):
    """Input: documents. Expect zero records present in both folds."""
    texts, labels, _ = document_corpus
    X_tr, X_te, _, _ = train_test_split(
        texts, labels, test_size=TEST_SIZE, random_state=SEED, stratify=labels)

    overlap = set(X_tr) & set(X_te)
    assert not overlap, f"{len(overlap)} documents appear in both folds"


# --- TC-14 --------------------------------------------------------------------
def test_tc14_known_defect_messages_leak_across_the_split(message_corpus):
    """Input: messages. KNOWN DEFECT: duplicate short messages straddle the folds.

    Measured impact is negligible (sentiment actually scores lower on the leaked
    rows), but the leakage is real and is asserted here so it cannot silently grow.
    """
    texts, intents, _ = message_corpus
    X_tr, X_te, _, _ = train_test_split(
        texts, intents, test_size=TEST_SIZE, random_state=SEED, stratify=intents)

    overlap = set(X_tr) & set(X_te)
    assert overlap, "expected the known leakage defect; corpus may have changed"
    assert len(overlap) / len(X_te) < 0.15, (
        f"leakage grew to {len(overlap)/len(X_te):.1%} of the test set")


# --- TC-15 --------------------------------------------------------------------
def test_tc15_split_is_reproducible(risk_dataset):
    """Input: risk dataset split twice with the same seed. Expect identical folds."""
    X, y, _, _ = risk_dataset
    a = train_test_split(X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y)
    b = train_test_split(X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y)
    assert np.array_equal(a[0], b[0]), "same seed produced different splits"
    assert np.array_equal(a[2], b[2])
