"""Validation rules applied to an extracted document.

Each rule returns a verdict with a severity. `blocking` means the document
cannot be accepted whatever the classifier thinks; `warning` sends it to a
human; `info` is recorded but does not affect routing.
"""
from datetime import date

from ml import fields

# Maps the wording HR uses for a requirement onto the classifier's label space.
_REQUIREMENT_KEYWORDS = [
    (("offer", "appointment"), "offer_letter"),
    (("passport", "govt id", "government id", "identity", "aadhaar", "licence", "license"), "govt_id"),
    (("safety", "osh"), "safety_certification"),
    (("deposit", "bank", "salary account", "payroll"), "bank_details"),
    (("background", "screening", "verification consent"), "background_check_consent"),
    (("ip ", "intellectual property", "invention", "confidentiality", "nda"), "ip_agreement"),
    (("degree", "education", "transcript", "marksheet", "provisional"), "education_certificate"),
    (("bar association", "bar council", "practice", "licence to practise", "professional"), "professional_license"),
]

# Document types that are meaningless without a signature.
_SIGNATURE_REQUIRED = {
    "offer_letter", "background_check_consent", "ip_agreement", "bank_details",
}

# Types whose whole purpose is time-limited validity.
_EXPIRY_REQUIRED = {"safety_certification", "professional_license", "govt_id"}

EXPIRY_WARN_DAYS = 30


def expected_class(requirement_name: str) -> str | None:
    if not requirement_name:
        return None
    lowered = requirement_name.lower()
    for keywords, label in _REQUIREMENT_KEYWORDS:
        if any(k in lowered for k in keywords):
            return label
    return None


def _check(name, passed, severity, message):
    return {"check": name, "passed": passed, "severity": severity, "message": message}


def _name_matches(extracted: list[str], employee_name: str) -> bool:
    if not extracted or not employee_name:
        return False
    employee_tokens = {t for t in employee_name.lower().split() if len(t) > 2}
    if not employee_tokens:
        return False
    for candidate in extracted:
        candidate_tokens = {t for t in candidate.lower().split() if len(t) > 2}
        if employee_tokens & candidate_tokens:
            return True
    return False


def run_checks(
    text: str,
    predicted_type: str | None,
    confidence: float | None,
    extracted: dict,
    requirement_name: str | None,
    employee_name: str | None,
    reference_date: date | None = None,
) -> list[dict]:
    checks = []
    today = reference_date or date.today()

    if not text or len(text.strip()) < 20:
        checks.append(_check(
            "readable", False, "blocking",
            "No readable text could be extracted from this file.",
        ))
        return checks
    checks.append(_check("readable", True, "info", "Document text extracted successfully."))

    wanted = expected_class(requirement_name or "")
    if wanted and predicted_type:
        if wanted == predicted_type:
            checks.append(_check(
                "type_match", True, "info",
                f"Document appears to be a {predicted_type.replace('_', ' ')}, as required.",
            ))
        else:
            looks_like = ("does not look like any onboarding document"
                          if predicted_type == "other"
                          else f"looks like a {predicted_type.replace('_', ' ')}")
            checks.append(_check(
                "type_match", False, "blocking",
                f"This {looks_like}, but '{requirement_name}' was requested.",
            ))

    expiry = extracted.get("dates", {}).get("expiry")
    if expiry:
        remaining = fields.days_until(expiry, today)
        if remaining is None:
            pass
        elif remaining < 0:
            checks.append(_check(
                "not_expired", False, "blocking",
                f"Document expired on {expiry} ({abs(remaining)} days ago).",
            ))
        elif remaining <= EXPIRY_WARN_DAYS:
            checks.append(_check(
                "not_expired", True, "warning",
                f"Document expires on {expiry}, in {remaining} days.",
            ))
        else:
            checks.append(_check(
                "not_expired", True, "info", f"Valid until {expiry}.",
            ))
    elif predicted_type in _EXPIRY_REQUIRED:
        checks.append(_check(
            "not_expired", False, "warning",
            "No expiry date could be found on a document type that should carry one.",
        ))

    if employee_name:
        if _name_matches(extracted.get("names", []), employee_name):
            checks.append(_check("name_match", True, "info",
                                 f"Name on document matches {employee_name}."))
        else:
            found = ", ".join(extracted.get("names", [])) or "none found"
            checks.append(_check(
                "name_match", False, "warning",
                f"Could not confirm the document belongs to {employee_name} (names found: {found}).",
            ))

    if predicted_type in _SIGNATURE_REQUIRED:
        if extracted.get("has_signature"):
            checks.append(_check("signature_present", True, "info", "Signature block detected."))
        elif extracted.get("signature_state") == "blank":
            # A scanned page can carry a handwritten signature that text
            # extraction cannot see, so an empty field goes to a human rather
            # than being rejected outright.
            checks.append(_check(
                "signature_present", False, "warning",
                "A signature field was found but it appears to be empty; HR should confirm it is signed.",
            ))
        else:
            checks.append(_check(
                "signature_present", False, "blocking",
                "This document type must be signed, but no signature was detected.",
            ))

    return checks
