"""Regression tests for defects found by the hand-written final review benchmark."""
from ml import fields, pipeline, rag, validate


def test_blank_signature_line_is_not_a_signature():
    text = "Offer of Employment\nDear Shreya Nair,\nSignature: ____________\nDate: ______"
    extracted = fields.extract_fields(text)
    assert extracted["signature_state"] == "blank"
    assert extracted["has_signature"] is False


def test_real_signature_is_still_detected():
    for text in ("Signature: /s/ Shreya Nair", "Signed by: Shreya Nair", "Authorised Signatory: (signed)"):
        assert fields.extract_fields(text)["has_signature"], text


def test_blank_signature_goes_to_review_not_approval():
    text = "Offer of Employment\nDear Shreya Nair,\nSignature: ____________"
    checks = validate.run_checks(text, "offer_letter", 0.95, fields.extract_fields(text),
                                 "Offer Letter Signed", "Shreya Nair")
    verdict, _ = pipeline.decide(checks, 0.95)
    assert verdict == pipeline.VERDICT_REVIEW


def test_certifies_that_names_are_found():
    names = fields.extract_fields("This certifies that Adithya Rao has completed training.")["names"]
    assert "Adithya Rao" in names


def test_photo_without_ocr_goes_to_review(tmp_path):
    from PIL import Image

    path = tmp_path / "photo.png"
    Image.new("RGB", (200, 100), (240, 240, 240)).save(path)
    result = pipeline.analyse(path, "image/png", requirement_name="Govt ID / Passport",
                              employee_name="Shreya Nair")
    if result["extraction"]["method"] != "ocr:unavailable":
        return  # an OCR engine is installed here, so this path is not exercised
    assert result["verdict"] == pipeline.VERDICT_REVIEW
    assert "OCR" in result["reason"]


def test_agent_receiving_a_transfer_cannot_transfer_again():
    from agents import specialists
    from agents.specialists import Context, Handoff

    ctx = Context(emp_id="emp_1", org_id="org_1", department="Engineering")
    first = {t.name for t in specialists.build_tools("Policy Agent", ctx, Handoff())}
    receiving = {t.name for t in specialists.build_tools("Policy Agent", ctx, Handoff(),
                                                         allow_transfer=False)}
    assert "transfer_to_specialist" in first
    assert "transfer_to_specialist" not in receiving
    assert "search_company_policy" in receiving


def test_plural_question_finds_singular_section():
    results = rag.search("Can I accept gifts from a supplier?", org_id="org_1",
                         department="Engineering", k=3)
    assert any(r["section"] == "Gifts" for r in results)
