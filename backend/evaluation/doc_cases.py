"""Hand-written test documents for document verification.

Each case is a document an employee might really upload, the requirement it was
uploaded against, and the verdict a careful HR officer would reach. Dates are
computed from today so "expires in 10 days" stays true whenever this runs.

Verdicts:
    auto_approved  every check passed and the model is confident
    auto_rejected  a blocking problem (wrong document, expired, unsigned)
    needs_review   something a person should look at (name mismatch, expiring
                   soon, empty signature field, unreadable scan)
"""
from datetime import date, timedelta


def _d(days: int, fmt: str = "%d/%m/%Y") -> str:
    return (date.today() + timedelta(days=days)).strftime(fmt)


def build_cases() -> list[dict]:
    """Return the cases with dates filled in relative to today."""
    return [
        {
            "id": "D01", "title": "Signed offer letter",
            "employee": "Shreya Nair", "requirement": "Offer Letter Signed",
            "expected": "auto_approved", "teaches": "The normal happy path.",
            "text": f"""NIMBUS LABS PRIVATE LIMITED
Offer of Employment

{_d(-40, '%d %B %Y')}

Dear Ms. Shreya Nair,

Further to your interviews, we are delighted to offer you the role of Senior
Frontend Engineer in our Engineering team. Your fixed annual compensation will
be INR 24,00,000, payable monthly. Your joining date will be {_d(-25)}.

This offer remains subject to background verification and to the terms set out
in the enclosed employee handbook.

Kindly sign below to confirm your acceptance.

For Nimbus Labs: Priya Raman, Head of People
Accepted and signed by: Shreya Nair
Signature: /s/ Shreya Nair
Date: {_d(-38)}
""",
        },
        {
            "id": "D02", "title": "Offer letter, never signed",
            "employee": "Shreya Nair", "requirement": "Offer Letter Signed",
            "expected": "auto_rejected", "teaches": "Signature is required on an offer letter.",
            "text": f"""NIMBUS LABS PRIVATE LIMITED
Offer of Employment

{_d(-40, '%d %B %Y')}

Dear Ms. Shreya Nair,

We are delighted to offer you the role of Senior Frontend Engineer in our
Engineering team at a fixed annual compensation of INR 24,00,000.
Your joining date will be {_d(-25)}.

Please return a countersigned copy of this letter to People Operations.
""",
        },
        {
            "id": "D03", "title": "Offer letter, signature line left blank",
            "employee": "Shreya Nair", "requirement": "Offer Letter Signed",
            "expected": "needs_review",
            "teaches": "An empty 'Signature: ____' line is not a signature (fixed for the final review).",
            "text": f"""NIMBUS LABS PRIVATE LIMITED
Offer of Employment

Dear Ms. Shreya Nair,

We are delighted to offer you the role of Senior Frontend Engineer at a fixed
annual compensation of INR 24,00,000. Your joining date will be {_d(-25)}.

Candidate acceptance

Signature: ______________________
Date: ____________
""",
        },
        {
            "id": "D04", "title": "Valid passport",
            "employee": "Shreya Nair", "requirement": "Govt ID / Passport",
            "expected": "auto_approved", "teaches": "Identity document with a future expiry date.",
            "text": f"""REPUBLIC OF INDIA
PASSPORT
Type P    Code IND    Passport No. M8823410
Surname: NAIR
Given Name(s): SHREYA
Nationality: INDIAN
Sex: F    Date of Birth: 08/06/1997
Place of Birth: KOCHI, KERALA
Place of Issue: COCHIN
Date of Issue: {_d(-1500)}
Date of Expiry: {_d(2150)}
""",
        },
        {
            "id": "D05", "title": "Somebody else's passport",
            "employee": "Shreya Nair", "requirement": "Govt ID / Passport",
            "expected": "needs_review",
            "teaches": "Right document type, wrong person: the name check flags it for HR.",
            "text": f"""REPUBLIC OF INDIA
PASSPORT
Type P    Code IND    Passport No. R1190256
Surname: MEHTA
Given Name(s): RAHUL
Nationality: INDIAN
Sex: M    Date of Birth: 19/11/1994
Place of Issue: MUMBAI
Date of Issue: {_d(-900)}
Date of Expiry: {_d(2700)}
""",
        },
        {
            "id": "D06", "title": "Expired passport",
            "employee": "Shreya Nair", "requirement": "Govt ID / Passport",
            "expected": "auto_rejected", "teaches": "Expiry date is read and compared to today.",
            "text": f"""REPUBLIC OF INDIA
PASSPORT
Type P    Code IND    Passport No. J5512093
Surname: NAIR
Given Name(s): SHREYA
Nationality: INDIAN
Date of Birth: 08/06/1997
Date of Issue: {_d(-3700)}
Date of Expiry: {_d(-50)}
""",
        },
        {
            "id": "D07", "title": "Valid safety certificate",
            "employee": "Adithya Rao", "requirement": "Safety Certification",
            "expected": "auto_approved", "teaches": "Certificate with a long validity left.",
            "text": f"""INDUSTRIAL SAFETY TRAINING BOARD
Certificate of Competence - Occupational Health and Safety

This certifies that Adithya Rao has completed 40 hours of training in
workplace hazard identification, fire safety, PPE use and machine guarding,
and has passed the practical assessment.

Certificate No: ISTB-2207-5531
Issued on: {_d(-200, '%d %b %Y')}
Valid until: {_d(900, '%d %b %Y')}

Signed: /s/ Chief Assessor
""",
        },
        {
            "id": "D08", "title": "Expired safety certificate",
            "employee": "Adithya Rao", "requirement": "Safety Certification",
            "expected": "auto_rejected", "teaches": "Veltrix policy: an expired certificate counts as no certificate.",
            "text": f"""INDUSTRIAL SAFETY TRAINING BOARD
Certificate of Competence - Occupational Health and Safety

This certifies that Adithya Rao has completed training in workplace hazard
identification and machine guarding.

Certificate No: ISTB-1904-0087
Issued on: {_d(-1300, '%d %b %Y')}
Valid until: {_d(-200, '%d %b %Y')}

Signed: /s/ Chief Assessor
""",
        },
        {
            "id": "D09", "title": "Safety certificate expiring in 10 days",
            "employee": "Adithya Rao", "requirement": "Safety Certification",
            "expected": "needs_review", "teaches": "Valid today but about to lapse, so HR is warned.",
            "text": f"""INDUSTRIAL SAFETY TRAINING BOARD
Certificate of Competence - Occupational Health and Safety

This certifies that Adithya Rao has completed training in workplace hazard
identification, fire safety and PPE use.

Certificate No: ISTB-2011-7720
Issued on: {_d(-1085, '%d %b %Y')}
Valid until: {_d(10, '%d %b %Y')}

Signed: /s/ Chief Assessor
""",
        },
        {
            "id": "D10", "title": "Cafeteria memo uploaded as bank form",
            "employee": "Shreya Nair", "requirement": "Direct Deposit Form",
            "expected": "auto_rejected", "teaches": "Wrong file entirely: the classifier spots the type mismatch.",
            "text": f"""Nimbus Labs - Facilities Team
Notice to all Bengaluru staff

From {_d(5)} the ground floor cafeteria will close at 7 pm instead of 9 pm
while the kitchen is refurbished. Evening snacks will be available from the
pantry on the third floor. Questions to facilities@nimbuslabs.example.
""",
        },
        {
            "id": "D11", "title": "Passport uploaded as offer letter",
            "employee": "Shreya Nair", "requirement": "Offer Letter Signed",
            "expected": "auto_rejected", "teaches": "A real document, but not the one requested.",
            "text": f"""REPUBLIC OF INDIA
PASSPORT
Passport No. M8823410
Surname: NAIR
Given Name(s): SHREYA
Date of Birth: 08/06/1997
Date of Issue: {_d(-1500)}
Date of Expiry: {_d(2150)}
""",
        },
        {
            "id": "D12", "title": "Signed salary account form",
            "employee": "Shreya Nair", "requirement": "Direct Deposit Form",
            "expected": "auto_approved", "teaches": "Bank details with account number, IFSC and signature.",
            "text": f"""SALARY CREDIT MANDATE

Employee name: Shreya Nair
Employee code: NL-2291
Bank: ICICI Bank, Indiranagar branch
Account holder: Shreya Nair
Account number: 001905507788
IFSC code: ICIC0000019
Account type: Savings

I request Nimbus Labs to credit my monthly salary to the account above.

Signature: /s/ Shreya Nair
Date: {_d(-20)}
""",
        },
        {
            "id": "D13", "title": "Salary account form, unsigned",
            "employee": "Shreya Nair", "requirement": "Direct Deposit Form",
            "expected": "auto_rejected", "teaches": "Bank mandates must be signed.",
            "text": """SALARY CREDIT MANDATE

Employee name: Shreya Nair
Bank: ICICI Bank, Indiranagar branch
Account holder: Shreya Nair
Account number: 001905507788
IFSC code: ICIC0000019
Account type: Savings

I request Nimbus Labs to credit my monthly salary to the account above.
""",
        },
        {
            "id": "D14", "title": "Signed background check consent",
            "employee": "Adithya Rao", "requirement": "Background Check Consent",
            "expected": "auto_approved", "teaches": "A different document type, same pipeline.",
            "text": f"""VELTRIX CORP - AUTHORISATION FOR BACKGROUND VERIFICATION

I, Adithya Rao, authorise Veltrix Corp and its appointed screening agency to
verify my identity, education, previous employment and criminal record, and to
contact the references I have provided. I understand that any material
discrepancy may lead to withdrawal of my offer.

Name: Adithya Rao
Signature: /s/ Adithya Rao
Date: {_d(-15)}
""",
        },
        {
            "id": "D15", "title": "Phone-quality scan of a signed offer letter",
            "employee": "Shreya Nair", "requirement": "Offer Letter Signed",
            "expected": "auto_approved",
            "teaches": "OCR-style damage (wrong letters, broken words); character n-grams still recognise it.",
            "text": f"""NlMBUS LA8S PR1VATE LIMlTED
0ffer of Emp1oyment

Dear Ms. Shreya Nair,

We are de1ighted to ofer you the ro1e of Seni0r Frontend Engin eer in our
Engineerlng team. Y0ur fixed annual c0mpensation wil1 be INR 24,00,000.
Your j0ining date wi11 be {_d(-25)}. This 0ffer is subject to backgr0und
verificati0n.

Accepted by: Shreya Nair
Signature: /s/ signed
Date: {_d(-38)}
""",
        },
        {
            "id": "D16", "title": "Photo of a document (no OCR engine on server)",
            "employee": "Shreya Nair", "requirement": "Govt ID / Passport",
            "expected": "needs_review",
            "teaches": "Unreadable without OCR, so it goes to HR rather than being rejected (fixed for the final review).",
            "text": None,  # written as a PNG image with no text layer
        },
    ]
