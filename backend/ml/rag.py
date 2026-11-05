"""Retrieval over the company policy corpus.

Retrieval is hybrid: a lexical TF-IDF score catches exact policy wording
("lockout-tagout"), and an LSA projection of the same matrix catches
paraphrase ("time off" vs "annual leave"). LSA is used rather than a neural
embedding model so the whole system runs offline with no model download; the
`embed` backend can be swapped later without changing callers.

Retrieval is access-controlled. A chunk is only visible to an employee whose
organisation matches, and whose department is allowed if the document restricts
one. Retrieval that ignores permissions is the classic way a helpful assistant
leaks confidential policy.
"""
import logging
import re
import threading
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

# Below this the retriever reports that it found nothing rather than returning
# the least-bad chunk. A confident wrong policy answer is worse than silence.
RELEVANCE_FLOOR = 0.12

# Above the floor but below this, a chunk is topically adjacent rather than an
# actual answer: "parental leave" retrieves the leave policy without being
# covered by it. Those are logged as documentation gaps.
WEAK_MATCH_SCORE = 0.42

LEXICAL_WEIGHT = 0.5

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-]*[a-z0-9]|[a-z0-9]")


def _stem(word: str) -> str:
    """Fold simple plurals so "gift" matches "Gifts" and "policy" matches "policies".

    Deliberately light: a full stemmer turns "leave" and "leaving" into the same
    token too, and over-merging hurts precision on a corpus this small.
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("ches", "shes", "sses", "xes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _tokenize(text: str) -> list[str]:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    words = _WORD_RE.findall(text.lower().replace("’", "'"))
    return [_stem(w) for w in words if w not in ENGLISH_STOP_WORDS and len(w) > 1]


_lock = threading.Lock()
_index = None

_META_RE = re.compile(r"<!--\s*(\w+):\s*(.*?)\s*-->")


def _parse_document(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta = {k: v for k, v in _META_RE.findall(raw)}
    body = _META_RE.sub("", raw).strip()
    return {
        "id": path.stem,
        "title": meta.get("title", path.stem),
        "org": meta.get("org", "all"),
        "departments": [d.strip() for d in meta.get("departments", "").split(",") if d.strip()],
        "body": body,
        "path": str(path),
    }


def _chunk(document: dict) -> list[dict]:
    """Split on markdown sections, keeping each chunk self-describing."""
    body = document["body"]
    parts = re.split(r"\n(?=##\s)", body)
    chunks = []
    for part in parts:
        text = part.strip()
        if len(text) < 40:
            continue
        heading = text.split("\n", 1)[0].lstrip("# ").strip()
        chunks.append({
            "doc_id": document["id"],
            "doc_title": document["title"],
            "section": heading,
            "org": document["org"],
            "departments": document["departments"],
            # The title is prepended so a chunk retrieves on its document's
            # subject even when the section text never repeats it.
            "text": f"{document['title']} — {heading}\n{text}",
            "raw": text,
        })
    return chunks


def build_index(force: bool = False):
    global _index
    with _lock:
        if _index is not None and not force:
            return _index

        if not KNOWLEDGE_DIR.exists():
            logger.warning("Knowledge directory missing. Run: python -m ml.knowledge_seed")
            _index = {"chunks": []}
            return _index

        chunks = []
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            try:
                chunks.extend(_chunk(_parse_document(path)))
            except Exception:
                logger.exception("Failed to index %s", path.name)

        if not chunks:
            _index = {"chunks": []}
            return _index

        texts = [c["text"] for c in chunks]
        vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                     min_df=1, sublinear_tf=True,
                                     tokenizer=_tokenize, token_pattern=None,
                                     lowercase=False)
        tfidf = vectorizer.fit_transform(texts)

        components = max(2, min(64, tfidf.shape[0] - 1, tfidf.shape[1] - 1))
        svd = TruncatedSVD(n_components=components, random_state=42)
        latent = normalize(svd.fit_transform(tfidf))

        _index = {
            "chunks": chunks,
            "vectorizer": vectorizer,
            "tfidf": normalize(tfidf),
            "svd": svd,
            "latent": latent,
        }
        logger.info("Indexed %d chunks from %d documents", len(chunks),
                    len({c['doc_id'] for c in chunks}))
        return _index


def _visible(chunk, org_id, department) -> bool:
    if chunk["org"] not in ("all", org_id):
        return False
    if chunk["departments"] and department not in chunk["departments"]:
        return False
    return True


def search(query: str, org_id: str | None = None, department: str | None = None,
           k: int = 4) -> list[dict]:
    index = build_index()
    if not index.get("chunks") or not query or not query.strip():
        return []

    query_tfidf = normalize(index["vectorizer"].transform([query]))
    lexical = (index["tfidf"] @ query_tfidf.T).toarray().ravel()

    query_latent = normalize(index["svd"].transform(query_tfidf))
    semantic = (index["latent"] @ query_latent.T).ravel()

    combined = LEXICAL_WEIGHT * lexical + (1 - LEXICAL_WEIGHT) * np.clip(semantic, 0, None)

    results = []
    for position in np.argsort(combined)[::-1]:
        chunk = index["chunks"][position]
        if not _visible(chunk, org_id, department):
            continue
        score = float(combined[position])
        if score < RELEVANCE_FLOOR:
            break
        results.append({
            "doc_id": chunk["doc_id"],
            "doc_title": chunk["doc_title"],
            "section": chunk["section"],
            "text": chunk["raw"],
            "score": score,
            "lexical": float(lexical[position]),
            "semantic": float(semantic[position]),
        })
        if len(results) >= k:
            break
    return results


def stats() -> dict:
    index = build_index()
    chunks = index.get("chunks", [])
    return {
        "documents": len({c["doc_id"] for c in chunks}),
        "chunks": len(chunks),
        "relevance_floor": RELEVANCE_FLOOR,
    }
