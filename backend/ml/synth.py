"""Synthetic corpus for training the onboarding document classifier.

Real labelled onboarding documents cannot be published, so the classifier is
bootstrapped on generated text and then improved from HR's real decisions (see
`document_uploads.hr_decision`).

The generator deliberately works against itself: templates share boilerplate,
values are randomised, and OCR-style character noise is injected. Without that,
classes separate on surface tokens alone and the reported accuracy means
nothing.
"""
import random

DOC_CLASSES = [
    "offer_letter",
    "govt_id",
    "safety_certification",
    "bank_details",
    "background_check_consent",
    "ip_agreement",
    "education_certificate",
    "professional_license",
    "other",
]

# Proportion of the corpus generated at each difficulty tier. Reported
# separately at evaluation time, because a single headline accuracy over a
# corpus this varied hides where the model actually fails.
DIFFICULTY_MIX = {"clean": 0.40, "degraded": 0.38, "severe": 0.22}

_ORGS = ["Nimbus Labs", "Veltrix Corp", "Arcadia Systems", "Meridian Industries",
         "Halcyon Group", "Northwind Manufacturing"]
_NAMES = ["Shreya Nair", "Adithya Rao", "Aisha Patel", "David Chen", "Elena Rodriguez",
          "James Wilson", "Priya Menon", "Marcus Thorne", "Sarah Jenkins", "Ravi Kumar"]
_CITIES = ["Bengaluru", "Chennai", "Pune", "Hyderabad", "Coimbatore", "Kochi"]
_ROLES = ["Senior Frontend Engineer", "Plant Manager", "Product Designer",
          "Logistics Coordinator", "Compliance Officer", "Assembly Line Lead"]

# Appears across several classes so no single token gives the label away.
_BOILERPLATE = [
    "This document is confidential and intended solely for the named individual.",
    "Please retain a copy for your records.",
    "Generated electronically; no physical signature is required for validity.",
    "For queries contact the People Operations team.",
    "Page 1 of 1",
    "Reference: {ref}",
]

_TEMPLATES = {
    "offer_letter": [
        """{org}
LETTER OF APPOINTMENT
Date: {date}
Dear {name},
We are pleased to offer you the position of {role} at {org}, based in {city}.
Your annual gross compensation will be INR {salary} per annum.
Your date of joining is {date2}. This offer is contingent on satisfactory
completion of background verification.
Please sign and return this letter to indicate acceptance.
Accepted by: {name}     Signature: {sig}     Date: {date2}""",
        """OFFER OF EMPLOYMENT
Employer: {org}
Candidate: {name}
Designation: {role}
Annual CTC: INR {salary}
Commencement: {date2}
By countersigning below the candidate accepts the terms of employment set out
in this letter and the accompanying employee handbook.
Candidate signature: {sig}""",
    ],
    "govt_id": [
        """GOVERNMENT OF INDIA
INDIAN PASSPORT / PASSEPORT
Type: P   Country Code: IND   Passport No: {passport}
Surname: {surname}
Given Name(s): {given}
Nationality: INDIAN   Sex: {sex}
Date of Birth: {dob}   Place of Birth: {city}
Date of Issue: {date}   Date of Expiry: {expiry}
Place of Issue: {city}""",
        """DRIVING LICENCE
Licence No: {licence}
Name: {name}
S/W/D of: {name2}
Date of Birth: {dob}
Address: {addr}, {city}
Valid From: {date}   Valid Till: {expiry}
Authorisation to Drive: LMV, MCWG
Issuing Authority: RTO {city}""",
        """UNIQUE IDENTIFICATION AUTHORITY OF INDIA
Aadhaar
{aadhaar}
Name: {name}
DOB: {dob}   Gender: {sex}
Address: {addr}, {city}
This is electronically generated and does not require a signature.""",
    ],
    "safety_certification": [
        """CERTIFICATE OF SAFETY TRAINING
This is to certify that {name} has successfully completed the
Occupational Health and Safety course prescribed under the Factories Act.
Certificate Number: {certno}
Date of Issue: {date}
Valid Until: {expiry}
Training Provider: National Institute of Industrial Safety, {city}
Authorised Signatory: {sig}""",
        """INDUSTRIAL SAFETY COMPLIANCE CERTIFICATE
Holder: {name}
Employer: {org}
Scope: Machine guarding, lockout-tagout, hazardous materials handling
Certificate Ref: {certno}
Issued: {date}    Expires: {expiry}
The holder is certified competent to supervise plant floor operations.""",
    ],
    "bank_details": [
        """DIRECT DEPOSIT AUTHORISATION FORM
Employee Name: {name}
Employee ID: {empno}
Bank Name: {bank}
Account Holder: {name}
Account Number: {acct}
IFSC Code: {ifsc}
Branch: {city}
Account Type: Savings
I authorise {org} to deposit my salary directly to the account above and, if
necessary, to debit erroneous credits.
Signature: {sig}   Date: {date}""",
        """SALARY ACCOUNT DETAILS
To: Payroll, {org}
Beneficiary: {name}
Bank: {bank}, {city} branch
A/C No: {acct}
IFSC: {ifsc}
Please route all future salary credits to this account with effect from {date2}.
Signed: {sig}""",
    ],
    "background_check_consent": [
        """CONSENT TO BACKGROUND VERIFICATION
I, {name}, authorise {org} and its appointed screening agency to verify my
employment history, educational qualifications, criminal record and address.
I understand this verification may be repeated during my employment.
I confirm the information supplied by me is true to the best of my knowledge.
Candidate Signature: {sig}
Date: {date}
Place: {city}""",
        """PRE-EMPLOYMENT SCREENING AUTHORISATION
Candidate: {name}
Prospective Employer: {org}
I consent to the collection and processing of personal data for the purpose of
pre-employment screening, in accordance with applicable data protection law.
I may withdraw this consent in writing at any time.
Signature: {sig}    Dated: {date}""",
    ],
    "ip_agreement": [
        """INTELLECTUAL PROPERTY AND CONFIDENTIALITY AGREEMENT
Between {org} (the Company) and {name} (the Employee).
1. Assignment. The Employee assigns to the Company all right, title and
interest in any invention, work of authorship or improvement conceived during
the course of employment.
2. Confidentiality. The Employee shall not disclose proprietary information.
3. Survival. Clause 2 survives termination of employment.
Executed on {date}.
Employee: {sig}    For the Company: {sig2}""",
        """PROPRIETARY INFORMATION AND INVENTIONS AGREEMENT
Employee: {name}      Company: {org}
The Employee acknowledges that all source code, designs, and trade secrets
developed in the course of employment are the exclusive property of the
Company. Nothing in this agreement assigns inventions developed entirely on
the Employee's own time without Company equipment.
Signed at {city} on {date}. Signature: {sig}""",
    ],
    "education_certificate": [
        """{univ}
DEGREE CERTIFICATE
This is to certify that {name} having been examined and found qualified was
admitted to the Degree of Bachelor of Technology in Computer Science and
Engineering in the year {year}, with First Class with Distinction.
Register Number: {regno}
Date of Award: {date}
Controller of Examinations: {sig}""",
        """PROVISIONAL CERTIFICATE
{univ}
Certified that {name} (Register No. {regno}) has passed the Master of Business
Administration examination held in {year}.
CGPA: {cgpa}
This provisional certificate is issued pending the formal degree certificate.
Issued on {date}. Registrar: {sig}""",
    ],
    "professional_license": [
        """BAR COUNCIL OF INDIA
CERTIFICATE OF ENROLMENT AND PRACTICE
This certifies that {name} is enrolled as an Advocate.
Enrolment Number: {barno}
Date of Enrolment: {date}
Valid Through: {expiry}
The advocate named above is entitled to practise before all courts in India.
Secretary: {sig}""",
        """INSTITUTE OF CHARTERED ACCOUNTANTS
CERTIFICATE OF PRACTICE
Member: {name}
Membership Number: {barno}
Certificate of Practice issued {date}, valid until {expiry}.
The member is authorised to practise as a Chartered Accountant.
Authorised Signatory: {sig}""",
    ],
    # Genuine uploads that satisfy no requirement. Without this class the model
    # is forced to assign every stray file to a real document type.
    "other": [
        """{org}
INTERNAL MEMORANDUM
To: All Staff, {city} office
Date: {date}
Subject: Revised cafeteria timings
With effect from {date2} the cafeteria will operate from 08:00 to 19:00.
Please direct questions to the facilities desk.""",
        """PAYSLIP FOR THE MONTH OF {year}
Employee: {name}    Employee ID: {empno}
Basic: {salary}   HRA: {salary}   Deductions: {salary}
This is a computer generated statement.""",
        """MEETING INVITATION
Organiser: {name2}
Subject: Sprint planning
When: {date} 10:00 - 11:00 IST
Location: {city} office, Room 4
Please accept or decline this invitation.""",
        """{org} — IT HELPDESK TICKET
Ticket: {ref}
Raised by: {name}
Category: Hardware request
Description: Requesting a docking station and a second monitor.
Status: Open""",
    ],
}

# Fragments lifted from other classes. Real documents are rarely pure: an offer
# letter often embeds an IP clause, a bank form is often stapled to one. These
# create the genuine ambiguity a template corpus otherwise lacks.
_CROSS_CLASS_NOISE = [
    "The Employee assigns to the Company all right, title and interest in any invention.",
    "Account Number: {acct}   IFSC: {ifsc}",
    "I consent to verification of my employment and educational history.",
    "Certificate Number: {certno}   Valid Until: {expiry}",
    "Date of Birth: {dob}   Place of Birth: {city}",
    "Annual CTC: INR {salary} payable monthly in arrears.",
    "Register Number: {regno}    Year of passing: {year}",
]

_BANKS = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Canara Bank"]
_UNIS = ["Amrita Vishwa Vidyapeetham", "Anna University", "VIT University",
         "University of Madras", "Manipal Academy of Higher Education"]


def _date(rng, lo=2015, hi=2027):
    return f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/{rng.randint(lo, hi)}"


def _slots(rng):
    name = rng.choice(_NAMES)
    parts = name.split()
    return {
        "org": rng.choice(_ORGS),
        "name": name,
        "name2": rng.choice(_NAMES),
        "surname": parts[-1].upper(),
        "given": parts[0].upper(),
        "role": rng.choice(_ROLES),
        "city": rng.choice(_CITIES),
        "addr": f"{rng.randint(1, 400)} {rng.choice(['MG Road', 'Park Street', 'Anna Salai', 'Residency Road'])}",
        "date": _date(rng),
        "date2": _date(rng),
        "dob": _date(rng, 1975, 2002),
        "expiry": _date(rng, 2019, 2031),
        "salary": f"{rng.randint(4, 45)},{rng.randint(0, 99):02d},000",
        "passport": f"{rng.choice('AJKLMNPZ')}{rng.randint(1000000, 9999999)}",
        "licence": f"{rng.choice(['KA', 'TN', 'MH', 'KL'])}{rng.randint(10, 99)} {rng.randint(10000000000, 99999999999)}",
        "aadhaar": f"{rng.randint(1000, 9999)} {rng.randint(1000, 9999)} {rng.randint(1000, 9999)}",
        "certno": f"{rng.choice(['OHS', 'ISC', 'NSC'])}-{rng.randint(10000, 99999)}",
        "empno": f"EMP{rng.randint(1000, 9999)}",
        "bank": rng.choice(_BANKS),
        "acct": str(rng.randint(10**10, 10**12)),
        "ifsc": f"{rng.choice(['SBIN', 'HDFC', 'ICIC', 'UTIB'])}0{rng.randint(100000, 999999)}",
        "univ": rng.choice(_UNIS),
        "year": str(rng.randint(2012, 2025)),
        "regno": f"{rng.randint(10**9, 10**10)}",
        "cgpa": f"{rng.uniform(6.0, 9.9):.2f}",
        "barno": f"{rng.choice(['D', 'KAR', 'TN'])}/{rng.randint(100, 9999)}/{rng.randint(2010, 2024)}",
        "sex": rng.choice(["M", "F"]),
        "sig": rng.choice(["/s/ signed", "[signature]", "___________", "(signed)"]),
        "sig2": rng.choice(["/s/ authorised", "[signature]", "___________"]),
        "ref": f"{rng.randint(100000, 999999)}",
    }


_OCR_CONFUSIONS = [("0", "O"), ("O", "0"), ("1", "l"), ("l", "1"),
                   ("5", "S"), ("rn", "m"), ("cl", "d"), ("I", "|")]


def _add_noise(text, rng, rate=0.02):
    """Approximate OCR damage so the classifier cannot rely on clean spelling."""
    chars = list(text)
    for _ in range(int(len(chars) * rate)):
        i = rng.randrange(len(chars))
        roll = rng.random()
        if roll < 0.5:
            src, dst = rng.choice(_OCR_CONFUSIONS)
            if chars[i] == src:
                chars[i] = dst
        elif roll < 0.75:
            chars[i] = ""
        else:
            chars[i] = chars[i].swapcase()
    return "".join(chars)


def _strip_header(body, rng):
    """Drop the leading lines. The header is the most discriminative part of a
    document, and it is exactly what a partial scan or a photo tends to lose."""
    lines = [ln for ln in body.split("\n") if ln.strip()]
    if len(lines) <= 3:
        return body
    cut = rng.randint(1, max(1, len(lines) // 2))
    return "\n".join(lines[cut:])


def _fragment(body, rng, min_lines=2, max_lines=5):
    lines = [ln for ln in body.split("\n") if ln.strip()]
    if len(lines) <= min_lines:
        return body
    take = rng.randint(min_lines, min(max_lines, len(lines)))
    start = rng.randrange(0, max(1, len(lines) - take + 1))
    return "\n".join(lines[start:start + take])


def _degrade(body, tier, rng, slots):
    """Apply tier-appropriate damage to a clean document."""
    if tier == "clean":
        if rng.random() < 0.30:
            body = _add_noise(body, rng, rate=rng.uniform(0.005, 0.02))
        if rng.random() < 0.15:
            body = body.upper()
        return body

    if tier == "degraded":
        if rng.random() < 0.55:
            body = _strip_header(body, rng)
        if rng.random() < 0.45:
            body += "\n" + rng.choice(_CROSS_CLASS_NOISE).format(**slots)
        body = _add_noise(body, rng, rate=rng.uniform(0.03, 0.09))
        if rng.random() < 0.25:
            body = body.upper()
        return body

    # severe: a bad phone photo of a crumpled page
    body = _strip_header(body, rng)
    body = _fragment(body, rng)
    for _ in range(rng.randint(1, 2)):
        body += "\n" + rng.choice(_CROSS_CLASS_NOISE).format(**slots)
    body = _add_noise(body, rng, rate=rng.uniform(0.10, 0.20))
    if rng.random() < 0.35:
        body = body.upper()
    return body


def generate(samples_per_class=550, seed=42):
    """Return (texts, labels, difficulties) for the whole synthetic corpus."""
    rng = random.Random(seed)
    texts, labels, tiers = [], [], []

    tier_names = list(DIFFICULTY_MIX)
    tier_weights = [DIFFICULTY_MIX[t] for t in tier_names]

    for label in DOC_CLASSES:
        for _ in range(samples_per_class):
            slots = _slots(rng)
            body = rng.choice(_TEMPLATES[label]).format(**slots)

            for line in rng.sample(_BOILERPLATE, rng.randint(0, 3)):
                body += "\n" + line.format(**slots)

            tier = rng.choices(tier_names, weights=tier_weights, k=1)[0]
            body = _degrade(body, tier, rng, slots)

            texts.append(body)
            labels.append(label)
            tiers.append(tier)

    order = list(range(len(texts)))
    rng.shuffle(order)
    return ([texts[i] for i in order],
            [labels[i] for i in order],
            [tiers[i] for i in order])
