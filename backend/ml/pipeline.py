"""End-to-end document analysis: extract -> classify -> extract fields -> validate -> route.

The routing policy is deliberately conservative. Auto-approval requires both a
confident classification and a clean set of checks; anything else goes to a
human. Getting an approval wrong is far more expensive than asking HR to look.
"""
import logging
from datetime import date
from pathlib import Path

from ml import classifier, extract, fields, validate

logger = logging.getLogger(__name__)

AUTO_APPROVE_CONFIDENCE = 0.80
AUTO_REJECT_CONFIDENCE = 0.60

VERDICT_APPROVED = "auto_approved"
VERDICT_REVIEW = "needs_review"
VERDICT_REJECTED = "auto_rejected"


def decide(checks: list[dict], confidence: float | None) -> tuple[str, str]:
    """Return (verdict, human-readable reason)."""
    blocking = [c for c in checks if not c["passed"] and c["severity"] == "blocking"]
    if blocking:
        return VERDICT_REJECTED, blocking[0]["message"]

    warnings = [c for c in checks if not c["passed"] and c["severity"] == "warning"]
    soft = [c for c in checks if c["passed"] and c["severity"] == "warning"]

    if confidence is None:
        if warnings:
            return VERDICT_REVIEW, warnings[0]["message"]
        return VERDICT_REVIEW, "No classifier available; manual review required."

    if confidence < AUTO_REJECT_CONFIDENCE:
        return VERDICT_REVIEW, (
            f"Document type is unclear (confidence {confidence:.0%}); manual review required."
        )

    if warnings:
        return VERDICT_REVIEW, warnings[0]["message"]

    if confidence < AUTO_APPROVE_CONFIDENCE:
        return VERDICT_REVIEW, (
            f"Checks passed but classification confidence is only {confidence:.0%}."
        )

    if soft:
        return VERDICT_REVIEW, soft[0]["message"]

    return VERDICT_APPROVED, "All automated checks passed."


def analyse(
    path: Path,
    content_type: str,
    requirement_name: str | None = None,
    employee_name: str | None = None,
    reference_date: date | None = None,
) -> dict:
    extraction = extract.extract_text(path, content_type)
    text = extraction["text"]

    prediction = classifier.predict(text)
    extracted = fields.extract_fields(text)

    checks = validate.run_checks(
        text=text,
        predicted_type=prediction["label"],
        confidence=prediction["confidence"],
        extracted=extracted,
        requirement_name=requirement_name,
        employee_name=employee_name,
        reference_date=reference_date,
    )

    # A scan or photo that could not be read because no OCR engine is installed
    # says nothing about the document itself, so it goes to a person instead of
    # being rejected as unreadable.
    if extraction["method"] in ("ocr:unavailable", "pdf:no-text-layer"):
        for check in checks:
            if check["check"] == "readable" and not check["passed"]:
                check["severity"] = "warning"
                check["message"] = ("This looks like a scan or photo and no OCR engine is "
                                    "installed on the server, so HR will review it manually.")

    verdict, reason = decide(checks, prediction["confidence"])

    return {
        "verdict": verdict,
        "reason": reason,
        "predicted_type": prediction["label"],
        "predicted_confidence": prediction["confidence"],
        "type_scores": prediction["scores"],
        "model_version": prediction["model_version"],
        "extraction": {
            "method": extraction["method"],
            "char_count": extraction["char_count"],
            "note": extraction.get("note"),
        },
        "extracted_fields": extracted,
        "checks": checks,
        "text": text,
    }
