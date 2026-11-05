"""Rule-based field extraction from document text.

Dates are the load-bearing part: a certificate's validity cannot be judged
without knowing which date is the expiry, so dates are classified by the label
they appear next to rather than by position.
"""
import re
from datetime import date

from dateutil import parser as date_parser

_MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"

_DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    rf"\b\d{{1,2}}\s+{_MONTHS}\.?,?\s+\d{{4}}\b",
    rf"\b{_MONTHS}\.?\s+\d{{1,2}},?\s+\d{{4}}\b",
]
_DATE_RE = re.compile("|".join(_DATE_PATTERNS), re.IGNORECASE)

_EXPIRY_HINTS = ["expiry", "expires", "expire", "valid until", "valid till",
                 "valid through", "valid upto", "valid up to", "date of expiry"]
_ISSUE_HINTS = ["date of issue", "issued on", "issued", "valid from", "date of award",
                "date of enrolment", "dated", "commencement", "executed on"]
_DOB_HINTS = ["date of birth", "dob", "d.o.b"]

_IDENTIFIER_PATTERNS = {
    "passport": r"passport\s*(?:no\.?|number)?\s*:?\s*([A-Z]\d{7})",
    "aadhaar": r"\b(\d{4}\s\d{4}\s\d{4})\b",
    "account_number": r"(?:a/?c|account)\s*(?:no\.?|number)?\s*:?\s*(\d{9,18})",
    "ifsc": r"ifsc\s*(?:code)?\s*:?\s*([A-Z]{4}0[A-Z0-9]{6})",
    # The no/number/ref token is required, not optional: without it "cert"
    # matches the leading substring of a "CERTIFICATE OF ..." title and captures
    # the rest of the word.
    "certificate_number": r"\bcert(?:ificate)?\s*(?:no\.?|number|ref)\s*:?\s*([A-Z0-9][A-Z0-9\-/]{3,20})",
    "enrolment_number": r"\b(?:enrolment|enrollment|membership|register)\s*(?:no\.?|number)\s*:?\s*([A-Z0-9][A-Z0-9\-/]{2,20})",
    "licence_number": r"licence\s*(?:no\.?|number)?\s*:?\s*([A-Z]{2}\d{2}\s?\d{6,12})",
}

# Labelled form fields, e.g. "Employee Name: Shreya Nair".
_NAME_LABEL_RE = re.compile(
    r"(?:^|\n)\s*(?:employee\s+)?(?:name|candidate|employee|holder|member|beneficiary"
    r"|account holder|given name\(s\)|surname|advocate)\s*:\s*([A-Za-z][A-Za-z .'-]{2,60})",
    re.IGNORECASE,
)

# Names embedded in prose, e.g. "Dear Shreya Nair," or "certify that Adithya Rao has".
# Each token must be capitalised, so the match stops at the first ordinary word.
# The trigger is case-insensitive via a scoped flag, but the captured name is
# not: requiring capitalised tokens is what stops the match running on into
# ordinary prose.
_NAME_INLINE_RE = re.compile(
    r"\b(?i:dear|certify that|certifies that|certified that|accepted by|awarded to|granted to"
    r"|issued to|signed by)\s*:?\s*"
    r"(?:Mr\.?|Ms\.?|Mrs\.?|Dr\.?)?\s*"
    r"([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){0,3})",
)

# Markers that only appear once a document has actually been signed.
_SIGNED_MARK_RE = re.compile(
    r"(/s/|\[signature\]|\(signed\)|digitally signed|e-signed|esigned)",
    re.IGNORECASE,
)

# A signature field label. Whether the field is filled in is decided by what
# follows it on the same line.
_SIGNATURE_FIELD_RE = re.compile(
    r"(?:signature|signed(?:\s+by)?)\s*:[ \t]*([^\n]*)",
    re.IGNORECASE,
)

# Another field label on the same line ("Signature: ____   Date: 01/01/2026")
# is not part of the signature.
_NEXT_FIELD_RE = re.compile(r"\s{2,}|\b(?:date|place|name)\s*:", re.IGNORECASE)

# A bare signature line ("__________") with nothing written on it.
_BLANK_LINE_RE = re.compile(r"^[\s_.\-]*$")


def _signature_state(text: str) -> str:
    """Return "signed", "blank" or "absent".

    "blank" means a signature field exists but nothing is written in it. An
    empty "Signature: ________" line used to count as signed, so an unsigned
    form passed the signature check.
    """
    if _SIGNED_MARK_RE.search(text):
        return "signed"
    saw_field = False
    for match in _SIGNATURE_FIELD_RE.finditer(text):
        saw_field = True
        value = _NEXT_FIELD_RE.split(match.group(1).strip(), maxsplit=1)[0].strip()
        if value and not _BLANK_LINE_RE.match(value) and len(re.sub(r"[_.\-\s]", "", value)) >= 2:
            return "signed"
    if saw_field or re.search(r"_{5,}", text):
        return "blank"
    return "absent"


# Capitalised words that follow a name on the same line and are not part of it.
_NAME_STOPWORDS = {
    "signature", "signed", "date", "dated", "place", "accepted", "employee",
    "company", "bank", "account", "designation", "role", "for", "at", "on",
}


def _trim_name(raw: str) -> str:
    tokens = raw.split()
    kept = []
    for token in tokens:
        if token.lower().strip(".,:") in _NAME_STOPWORDS:
            break
        kept.append(token)
    return " ".join(kept).strip(" .-'")


def _parse(raw: str):
    try:
        return date_parser.parse(raw, dayfirst=True, fuzzy=False).date()
    except (ValueError, OverflowError):
        return None


_ROLE_HINTS = (("expiry", _EXPIRY_HINTS), ("dob", _DOB_HINTS), ("issue", _ISSUE_HINTS))


def _nearest_role(segment: str) -> str | None:
    """Role of the label closest to the end of `segment`, if any.

    Identity documents routinely put issue and expiry on one line, so a date
    must take the role of the label immediately to its left, not of any label
    appearing somewhere on the line.
    """
    best_role, best_index = None, -1
    for role, hints in _ROLE_HINTS:
        for hint in hints:
            index = segment.rfind(hint)
            if index > best_index:
                best_role, best_index = role, index
    return best_role


def _classify_dates(text: str) -> dict:
    found = {"issue": None, "expiry": None, "dob": None}
    all_dates = []
    pending_role = None

    for line in text.split("\n"):
        lowered = line.lower()
        matches = list(_DATE_RE.finditer(line))

        if not matches:
            # A label on its own line applies to dates on the line below it.
            pending_role = _nearest_role(lowered)
            continue

        for match in matches:
            parsed = _parse(match.group(0))
            if not parsed:
                continue
            iso = parsed.isoformat()
            all_dates.append(iso)

            role = _nearest_role(lowered[: match.start()]) or pending_role
            if role and not found[role]:
                found[role] = iso

        pending_role = None

    return {"dates": found, "all_dates": sorted(set(all_dates))}


def extract_fields(text: str) -> dict:
    if not text or not text.strip():
        return {
            "dates": {"issue": None, "expiry": None, "dob": None},
            "all_dates": [], "names": [], "identifiers": {}, "has_signature": False,
            "signature_state": "absent",
        }

    result = _classify_dates(text)

    names = []
    for pattern in (_NAME_LABEL_RE, _NAME_INLINE_RE):
        for match in pattern.finditer(text):
            candidate = _trim_name(match.group(1))
            if 2 < len(candidate) <= 60 and candidate.lower() not in {n.lower() for n in names}:
                names.append(candidate)
    result["names"] = names[:6]

    identifiers = {}
    for key, pattern in _IDENTIFIER_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            identifiers[key] = match.group(1).strip()
    result["identifiers"] = identifiers

    state = _signature_state(text)
    result["signature_state"] = state
    result["has_signature"] = state == "signed"
    return result


def days_until(iso_date: str | None, reference: date | None = None) -> int | None:
    if not iso_date:
        return None
    try:
        target = date.fromisoformat(iso_date)
    except ValueError:
        return None
    return (target - (reference or date.today())).days
