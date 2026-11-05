"""Write the starter policy corpus that the RAG layer retrieves from.

Run from the backend directory:
    python -m ml.knowledge_seed

Each file carries a small metadata header. `org` scopes a document to one
organisation and `departments` optionally narrows it further, which is what
makes retrieval access-controlled rather than a shared free-for-all.

Deliberately incomplete: several questions employees actually ask (parental
leave, notice period, relocation) are not covered anywhere. That is what the
knowledge-gap report is meant to surface.
"""
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

DOCUMENTS = {
    "shared__code_of_conduct.md": {
        "title": "Code of Conduct",
        "org": "all",
        "body": """# Code of Conduct

All employees are expected to treat colleagues, customers and suppliers with
respect and professionalism.

## Harassment
Harassment of any kind is not tolerated. Reports may be made to any manager or
directly to People Operations, and will be handled confidentially.

## Conflicts of interest
Employees must declare any outside employment, directorship or financial
interest in a competitor, supplier or customer before taking it up.

## Gifts
Gifts with a value above INR 2,000 must be declared to your manager. Cash gifts
may never be accepted.
""",
    },
    "shared__equipment_and_expenses.md": {
        "title": "Equipment and Expenses",
        "org": "all",
        "body": """# Equipment and Expenses

## Company equipment
Every employee is issued a laptop. Engineering and Design roles may request a
second monitor and a docking station through the IT Helpdesk.

## Expense claims
Claims must be submitted within 30 days of the expense being incurred, with a
receipt attached. Claims are reimbursed with the following month's salary.

## Travel
Domestic travel is booked through the internal travel desk. Economy class is
standard for flights under four hours.
""",
    },
    "org_1__leave_policy.md": {
        "title": "Leave Policy (Nimbus Labs)",
        "org": "org_1",
        "body": """# Leave Policy - Nimbus Labs

## Annual leave
Employees receive 24 days of paid annual leave per calendar year, accrued
monthly at 2 days per month. Up to 10 unused days may be carried into the
following year.

## Sick leave
12 days of paid sick leave per year. A medical certificate is required for any
absence of more than three consecutive working days.

## Leave during probation
Leave may be taken during the six-month probation period, but is limited to
6 days in total and requires manager approval in advance.

## Public holidays
12 public holidays per year, published each January.
""",
    },
    "org_1__remote_work.md": {
        "title": "Remote Work Policy (Nimbus Labs)",
        "org": "org_1",
        "body": """# Remote Work Policy - Nimbus Labs

Nimbus Labs operates a hybrid model. Employees are expected in the Bengaluru
office on Tuesdays and Wednesdays; the remaining days may be worked remotely.

## Equipment at home
The company contributes up to INR 15,000 towards a desk and chair, claimable
once every three years.

## Working from abroad
Working from outside India requires written approval from both your manager and
People Operations, and is limited to 30 days per year for tax reasons.
""",
    },
    "org_1__information_security.md": {
        "title": "Information Security (Nimbus Labs)",
        "org": "org_1",
        "departments": ["Engineering", "Design", "Legal"],
        "body": """# Information Security - Nimbus Labs

As a regulated fintech, Nimbus Labs applies strict controls to customer data.

## Access
Access to production systems requires completion of the security training module
and approval from an engineering manager. Access is reviewed quarterly.

## Customer data
Customer financial data may never be copied to a personal device, a personal
cloud account, or a local machine outside the approved development environment.

## Incidents
Suspected breaches must be reported to security@nimbuslabs.example within one
hour of discovery, at any hour of the day.

## Passwords
All accounts require multi-factor authentication. Shared credentials are
prohibited without exception.
""",
    },
    "org_2__safety_policy.md": {
        "title": "Plant Safety Policy (Veltrix Corp)",
        "org": "org_2",
        "body": """# Plant Safety Policy - Veltrix Corp

## Certification
No employee may enter the production floor without a valid safety certification.
Certifications are valid for three years and must be renewed before expiry. An
expired certificate is treated as no certificate.

## Personal protective equipment
Steel-toed boots, high-visibility vests and eye protection are mandatory on the
production floor at all times. Hearing protection is required in the press shop.

## Incident reporting
All incidents, including near misses with no injury, must be reported to the
shift supervisor before the end of the shift.

## Lockout-tagout
Machinery must be isolated and tagged before any maintenance work begins. Only
personnel certified in lockout-tagout may perform the isolation.
""",
    },
    "org_2__shift_patterns.md": {
        "title": "Shift Patterns (Veltrix Corp)",
        "org": "org_2",
        "body": """# Shift Patterns - Veltrix Corp

## Standard shifts
The plant runs three shifts: morning 06:00-14:00, afternoon 14:00-22:00 and
night 22:00-06:00. Shift rotation is on a weekly cycle.

## Shift allowance
Night shift attracts a 25% allowance on basic pay. Afternoon shift attracts 10%.

## Handover
Outgoing operators must complete a written handover covering machine status,
outstanding faults and production counts before leaving.

## Overtime
Overtime is voluntary and paid at 1.5x. It requires supervisor approval in
advance and is capped at 12 hours per week under the Factories Act.
""",
    },
    "org_2__leave_policy.md": {
        "title": "Leave Policy (Veltrix Corp)",
        "org": "org_2",
        "body": """# Leave Policy - Veltrix Corp

## Annual leave
Employees receive 18 days of paid annual leave per calendar year. Leave must be
requested at least two weeks in advance so that shift cover can be arranged.

## Sick leave
10 days of paid sick leave per year. Absence must be reported to the shift
supervisor at least two hours before the shift begins.

## Leave during probation
No annual leave may be taken in the first three months of employment except in
an emergency approved by the plant manager.
""",
    },
}


def main():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    for filename, meta in DOCUMENTS.items():
        header = [
            f"<!-- title: {meta['title']} -->",
            f"<!-- org: {meta['org']} -->",
        ]
        if meta.get("departments"):
            header.append(f"<!-- departments: {','.join(meta['departments'])} -->")
        content = "\n".join(header) + "\n\n" + meta["body"]
        (KNOWLEDGE_DIR / filename).write_text(content, encoding="utf-8")
        print(f"  wrote {filename}")
    print(f"\n{len(DOCUMENTS)} documents in {KNOWLEDGE_DIR}")


if __name__ == "__main__":
    main()
