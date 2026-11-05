"""TC-16 to TC-26: document pipeline behaviour, upload safety and boundary cases.

TC-16 is the functional contract: each demo document must produce the verdict its
filename declares. TC-20 onward are the edge, boundary and exceptional cases.
"""
import time

import pytest

from tests.conftest import MINIMAL_PDF

# filename -> (requirement, employee, expected verdict)
PIPELINE_CASES = [
    ("shreya_offer_letter_SIGNED_expect_approve.pdf", "Offer Letter Signed", "Shreya", "auto_approved"),
    ("shreya_offer_letter_UNSIGNED_expect_reject.pdf", "Offer Letter Signed", "Shreya", "auto_rejected"),
    ("adithya_safety_cert_EXPIRED_expect_reject.pdf", "Safety Certification", "Adithya", "auto_rejected"),
    ("adithya_safety_cert_VALID_expect_approve.pdf", "Safety Certification", "Adithya", "auto_approved"),
    ("shreya_passport_expect_approve.pdf", "Govt ID / Passport", "Shreya", "auto_approved"),
    ("wrong_file_a_memo_expect_reject.pdf", "Govt ID / Passport", "Shreya", "auto_rejected"),
    ("shreya_direct_deposit_expect_approve.pdf", "Direct Deposit Form", "Shreya", "auto_approved"),
]


# --- TC-16 --------------------------------------------------------------------
@pytest.mark.parametrize("filename,requirement,employee,expected", PIPELINE_CASES)
def test_tc16_document_pipeline_contract(demo_dir, filename, requirement, employee, expected):
    """Input: a demo PDF + its requirement. Expect the verdict named in the filename."""
    from ml import pipeline
    result = pipeline.analyse(demo_dir / filename, "application/pdf", requirement, employee)
    assert result["verdict"] == expected, (
        f"{filename}: expected {expected}, got {result['verdict']} ({result['reason']})")


# --- TC-17 --------------------------------------------------------------------
def test_tc17_expired_document_rejection_cites_the_expiry(demo_dir):
    """Input: an expired certificate. Expect rejection whose reason names the date."""
    from ml import pipeline
    r = pipeline.analyse(demo_dir / "adithya_safety_cert_EXPIRED_expect_reject.pdf",
                         "application/pdf", "Safety Certification", "Adithya")
    assert r["verdict"] == "auto_rejected"
    assert "expired" in r["reason"].lower()
    assert "2024-03-14" in r["reason"], "the rejection must state which date expired"


# --- TC-18 --------------------------------------------------------------------
def test_tc18_date_roles_resolve_on_a_shared_line():
    """Input: a passport line holding issue and expiry together.

    Regression test: a whole-line keyword search previously tagged the issue date
    as the expiry and declared a valid passport expired.
    """
    from ml import fields
    text = ("GOVERNMENT OF INDIA\n"
            "Date of Issue: 22/07/2021   Date of Expiry: 21/07/2031\n")
    dates = fields.extract_fields(text)["dates"]
    assert dates["issue"] == "2021-07-22"
    assert dates["expiry"] == "2031-07-21"


# --- TC-19 --------------------------------------------------------------------
def test_tc19_certificate_number_is_not_taken_from_the_title():
    """Input: a document titled 'CERTIFICATE OF ...' with a real number below it.

    Regression test: the pattern previously matched the prefix of the word
    'CERTIFICATE' and captured 'IFICATE' as the identifier.
    """
    from ml import fields
    text = "CERTIFICATE OF SAFETY TRAINING\nCertificate Number: OHS-48213\n"
    assert fields.extract_fields(text)["identifiers"].get("certificate_number") == "OHS-48213"


# --- TC-20 (boundary) ---------------------------------------------------------
def test_tc20_empty_file_is_rejected(tmp_storage):
    """Input: a zero-byte upload. Expect rejection, not a crash."""
    import io
    import storage
    with pytest.raises(storage.UploadRejected):
        storage.save_upload(io.BytesIO(b""), "emp_1", "application/pdf")


# --- TC-21 (exceptional) ------------------------------------------------------
def test_tc21_html_disguised_as_pdf_is_rejected(tmp_storage):
    """Input: HTML content with a PDF content-type. Expect rejection on magic bytes."""
    import io
    import storage
    with pytest.raises(storage.UploadRejected):
        storage.save_upload(io.BytesIO(b"<html><script>alert(1)</script></html>"),
                            "emp_1", "application/pdf")


# --- TC-22 (boundary) ---------------------------------------------------------
def test_tc22_oversized_upload_is_rejected_and_leaves_no_file(tmp_storage):
    """Input: a file one byte over the 10MB cap. Expect rejection and no partial file."""
    import io
    import storage
    payload = MINIMAL_PDF + b"0" * (storage.MAX_BYTES + 1)
    with pytest.raises(storage.UploadRejected):
        storage.save_upload(io.BytesIO(payload), "emp_1", "application/pdf")
    assert not list(tmp_storage.rglob("*.pdf")), "a partial file was left behind"


# --- TC-23 (exceptional) ------------------------------------------------------
@pytest.mark.parametrize("bad_id", ["../etc", "emp 1", "emp/1", "", "a" * 100])
def test_tc23_malformed_employee_id_is_rejected(tmp_storage, bad_id):
    """Input: employee ids containing traversal or illegal characters. Expect rejection."""
    import io
    import storage
    with pytest.raises(storage.UploadRejected):
        storage.save_upload(io.BytesIO(MINIMAL_PDF), bad_id, "application/pdf")


# --- TC-24 (exceptional) ------------------------------------------------------
def test_tc24_stored_path_cannot_escape_the_store(tmp_storage):
    """Input: a crafted relative path. Expect resolution to refuse to leave the root."""
    import storage
    with pytest.raises(storage.UploadRejected):
        storage.resolve("../../../windows/win.ini")


# --- TC-25 (validation) -------------------------------------------------------
def test_tc25_unreadable_document_goes_to_a_human_not_to_approval(tmp_storage):
    """Input: a PDF with no extractable text. Expect review or rejection, never approval."""
    import io
    import storage
    from ml import pipeline

    saved = storage.save_upload(io.BytesIO(MINIMAL_PDF), "emp_1", "application/pdf")
    result = pipeline.analyse(storage.resolve(saved["stored_path"]), "application/pdf",
                              "Govt ID / Passport", "Shreya")
    assert result["verdict"] != pipeline.VERDICT_APPROVED, (
        "an unreadable document must never be auto-approved")


# --- TC-26 (performance) ------------------------------------------------------
def test_tc26_pipeline_latency_is_acceptable(demo_dir):
    """Input: one demo PDF. Expect end-to-end analysis under 5 seconds.

    Guards the interactive upload path; the classifier is local so this is
    generous, and a regression here means something started loading per call.
    """
    from ml import pipeline
    path = demo_dir / "shreya_passport_expect_approve.pdf"
    pipeline.analyse(path, "application/pdf", "Govt ID / Passport", "Shreya")  # warm caches

    started = time.perf_counter()
    pipeline.analyse(path, "application/pdf", "Govt ID / Passport", "Shreya")
    elapsed = time.perf_counter() - started
    assert elapsed < 5.0, f"pipeline took {elapsed:.2f}s"
