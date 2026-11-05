"""Generate demo PDFs for testing and for live demonstrations.

Run from the backend directory:
    python -m ml.make_demo_docs

Each file is named after the verdict it should produce, so a demo can show the
pipeline approving, rejecting and escalating without hunting for sample files.
"""
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "demo_documents"

DOCUMENTS = {
    "shreya_offer_letter_SIGNED_expect_approve.pdf": """Nimbus Labs
LETTER OF APPOINTMENT

Date: 01/09/2026

Dear Shreya Nair,

We are pleased to offer you the position of Senior Frontend Engineer at
Nimbus Labs, based in Bengaluru.

Your annual gross compensation will be INR 24,00,000 per annum.
Your date of joining is 12/10/2026. This offer is contingent on satisfactory
completion of background verification.

Please sign and return this letter to indicate acceptance.

Accepted by: Shreya Nair
Signature: /s/ signed
Date: 12/10/2026
""",
    "shreya_offer_letter_UNSIGNED_expect_reject.pdf": """Nimbus Labs
LETTER OF APPOINTMENT

Date: 01/09/2026

Dear Shreya Nair,

We are pleased to offer you the position of Senior Frontend Engineer at
Nimbus Labs, based in Bengaluru.

Your annual gross compensation will be INR 24,00,000 per annum.
Your date of joining is 12/10/2026.

Please return this letter to indicate acceptance.
""",
    "adithya_safety_cert_EXPIRED_expect_reject.pdf": """CERTIFICATE OF SAFETY TRAINING

This is to certify that Adithya Rao has successfully completed the
Occupational Health and Safety course prescribed under the Factories Act.

Certificate Number: OHS-48213
Date of Issue: 14/03/2021
Valid Until: 14/03/2024

Training Provider: National Institute of Industrial Safety, Chennai
Authorised Signatory: /s/ signed
""",
    "adithya_safety_cert_VALID_expect_approve.pdf": """CERTIFICATE OF SAFETY TRAINING

This is to certify that Adithya Rao has successfully completed the
Occupational Health and Safety course prescribed under the Factories Act.

Certificate Number: OHS-99001
Date of Issue: 10/01/2025
Valid Until: 10/01/2029

Training Provider: National Institute of Industrial Safety, Chennai
Authorised Signatory: /s/ signed
""",
    "shreya_passport_expect_approve.pdf": """GOVERNMENT OF INDIA
INDIAN PASSPORT / PASSEPORT

Type: P   Country Code: IND   Passport No: K4471902

Surname: NAIR
Given Name(s): SHREYA
Name: Shreya Nair
Nationality: INDIAN   Sex: F

Date of Birth: 08/06/1997   Place of Birth: Kochi
Date of Issue: 22/07/2021   Date of Expiry: 21/07/2031
Place of Issue: Kochi
""",
    "wrong_file_a_memo_expect_reject.pdf": """Nimbus Labs
INTERNAL MEMORANDUM

To: All Staff, Bengaluru office
Date: 01/09/2026
Subject: Revised cafeteria timings

With effect from 15/09/2026 the cafeteria will operate from 08:00 to 19:00.
Please direct questions to the facilities desk.
""",
    "shreya_direct_deposit_expect_approve.pdf": """DIRECT DEPOSIT AUTHORISATION FORM

Employee Name: Shreya Nair
Employee ID: EMP1042
Bank Name: HDFC Bank
Account Holder: Shreya Nair
Account Number: 50100234519987
IFSC Code: HDFC0004512
Branch: Bengaluru
Account Type: Savings

I authorise Nimbus Labs to deposit my salary directly to the account above.

Signature: /s/ signed
Date: 02/09/2026
""",
}


def main():
    from fpdf import FPDF

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, body in DOCUMENTS.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in body.split("\n"):
            pdf.multi_cell(
                w=0, h=6, text=line if line.strip() else " ",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.output(str(OUTPUT_DIR / filename))
        print(f"  wrote {filename}")

    print(f"\n{len(DOCUMENTS)} demo documents in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
