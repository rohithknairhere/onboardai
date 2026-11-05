"""Shared fixtures.

Tests are deliberately offline and deterministic: nothing here calls a language
model, and nothing writes to the development database. A test that depends on a
network service or on generation temperature cannot be used as a regression
gate, which is the whole point of having one.
"""
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SEED = 42
TEST_SIZE = 0.25

# A syntactically valid minimal PDF: correct magic bytes, almost no content.
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"


@pytest.fixture(scope="session")
def demo_dir():
    d = BACKEND / "demo_documents"
    if not d.exists() or not any(d.glob("*.pdf")):
        pytest.skip("demo documents missing; run: python -m ml.make_demo_docs")
    return d


@pytest.fixture(scope="session")
def document_corpus():
    from ml import synth
    return synth.generate()


@pytest.fixture(scope="session")
def message_corpus():
    from ml import text_synth
    return text_synth.generate()


@pytest.fixture(scope="session")
def risk_dataset():
    from ml import risk_synth
    return risk_synth.generate()


@pytest.fixture()
def tmp_storage(tmp_path, monkeypatch):
    """Point the upload store at a temp directory so tests never touch real files."""
    import storage
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)
    return tmp_path
