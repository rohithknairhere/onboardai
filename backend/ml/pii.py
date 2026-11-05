"""Detect and redact personal data before text leaves the building.

Employee messages are sent to a third-party model provider by default, so
identifiers are stripped first. The rules below are deliberately conservative
and India-aware (Aadhaar, PAN, IFSC) because that is where this deployment is.

For production, Microsoft Presidio adds ML-based NER on top of rules; this
module is the dependency-free floor, not the ceiling.
"""
import re

# Order matters: the most specific patterns run first so that, for example, an
# IFSC code is not partially consumed by the generic long-number rule.
PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
    ("AADHAAR", re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("PASSPORT", re.compile(r"\b[A-PR-WYa-pr-wy][0-9]{7}\b")),
    ("PHONE", re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")),
    ("ACCOUNT", re.compile(r"\b\d{11,18}\b")),
    ("CARD", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")),
]


def scan(text: str) -> list[dict]:
    """Return the entities found, without their values."""
    if not text:
        return []
    found = []
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            found.append({"type": label, "start": match.start(), "end": match.end()})
    return found


def redact(text: str) -> tuple[str, list[str]]:
    """Replace personal identifiers with typed placeholders.

    Returns the cleaned text and the entity types that were removed. Values are
    never returned, so they cannot leak into logs or the event stream.
    """
    if not text:
        return text, []

    redacted = text
    types: list[str] = []
    for label, pattern in PATTERNS:
        def _replace(match, label=label):
            if label not in types:
                types.append(label)
            return f"[{label}_REDACTED]"
        redacted = pattern.sub(_replace, redacted)

    return redacted, types
