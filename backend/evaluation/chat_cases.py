"""Hand-written test cases for the chatbot.

Three layers are tested separately, because a single "the chatbot works" score
hides where it fails:

1. Routing: does the intent classifier send the message to the right specialist?
2. Retrieval: does policy search find the right document and section, and does
   it refuse to show another company's documents?
3. Answers: does the full assistant (language model + tools) give the correct
   fact with a citation, and decline when the handbook has no answer?
"""

# (id, message, expected intent, expected sentiment)
ROUTING_CASES = [
    # document_help
    ("R01", "Which file format should my passport scan be in?", "document_help", "neutral"),
    ("R02", "HR bounced my safety certificate back, can you tell me why?", "document_help", "neutral"),
    ("R03", "Do I need to get my degree certificate attested before uploading it?", "document_help", "neutral"),
    ("R04", "I sent the bank form yesterday and it still hasn't been checked, really annoying", "document_help", "negative"),
    ("R05", "Great, my offer letter got approved! What's the next document I should send?", "document_help", "positive"),
    ("R06", "Is a photo of my aadhaar card okay instead of the passport?", "document_help", "neutral"),
    # it_access
    ("R07", "My GitHub invite never came through", "it_access", "neutral"),
    ("R08", "I can't sign into Slack, it keeps saying my account doesn't exist", "it_access", "negative"),
    ("R09", "Could I get a second monitor for my desk?", "it_access", "neutral"),
    ("R10", "Who do I ask for Jira permissions?", "it_access", "neutral"),
    ("R11", "Day three and still no laptop, I literally cannot do any work", "it_access", "negative"),
    ("R12", "Thanks! Could you also set me up on the AWS staging account?", "it_access", "positive"),
    # kt_schedule
    ("R13", "Who's running the handover on the payments service?", "kt_schedule", "neutral"),
    ("R14", "Is the sprint 42 walkthrough still happening this week?", "kt_schedule", "neutral"),
    ("R15", "I missed my knowledge transfer meeting, can it be rebooked?", "kt_schedule", "neutral"),
    ("R16", "Who should I contact about the shift handover training?", "kt_schedule", "neutral"),
    ("R17", "The KT with Alex was super useful, when is the next one?", "kt_schedule", "positive"),
    ("R18", "My handover sessions keep getting cancelled and I'm falling behind", "kt_schedule", "negative"),
    # policy_question
    ("R19", "How many sick days am I allowed?", "policy_question", "neutral"),
    ("R20", "Can I work from Goa for a couple of weeks?", "policy_question", "neutral"),
    ("R21", "What safety gear is compulsory on the factory floor?", "policy_question", "neutral"),
    ("R22", "Is there a limit on gifts I can accept from vendors?", "policy_question", "neutral"),
    ("R23", "What happens if I need a day off while I'm still on probation?", "policy_question", "neutral"),
    ("R24", "Do I have to come into the office every day?", "policy_question", "neutral"),
    # status_check
    ("R25", "How far along am I in onboarding?", "status_check", "neutral"),
    ("R26", "Is there anything left on my to-do list?", "status_check", "neutral"),
    ("R27", "Which step of the process am I on right now?", "status_check", "neutral"),
    ("R28", "Am I nearly done with all the joining formalities?", "status_check", "neutral"),
    ("R29", "Just finished my training, so what's next for me?", "status_check", "positive"),
    ("R30", "I feel like I'm behind, how much do I still have to finish?", "status_check", "negative"),
    # payroll_benefits
    ("R31", "On what date does salary get credited each month?", "payroll_benefits", "neutral"),
    ("R32", "Does the health plan cover my parents too?", "payroll_benefits", "neutral"),
    ("R33", "Is there a joining bonus in my package?", "payroll_benefits", "neutral"),
    ("R34", "I want to change the bank account my pay goes into", "payroll_benefits", "neutral"),
    ("R35", "When will my PF account be opened?", "payroll_benefits", "neutral"),
    ("R36", "My first payslip looks wrong, the amount is way less than my offer", "payroll_benefits", "negative"),
    # escalation
    ("R37", "I've emailed HR four times and heard nothing back", "escalation", "negative"),
    ("R38", "Please get me a real person, the bot isn't helping", "escalation", "negative"),
    ("R39", "Honestly I'm thinking of withdrawing my acceptance, this is chaos", "escalation", "negative"),
    ("R40", "This is unacceptable, I start tomorrow and nothing has been set up", "escalation", "negative"),
    ("R41", "I want to raise a formal complaint about how my onboarding has been handled", "escalation", "negative"),
    ("R42", "Nobody has responded for over a week, who is actually in charge here?", "escalation", "negative"),
    # smalltalk
    ("R43", "Hey there!", "smalltalk", "neutral"),
    ("R44", "Thanks a lot, that sorted it", "smalltalk", "positive"),
    ("R45", "Have a nice weekend", "smalltalk", "positive"),
    ("R46", "Cool, understood", "smalltalk", "neutral"),
    ("R47", "You've been really helpful today", "smalltalk", "positive"),
    ("R48", "Morning! Hope you're doing well", "smalltalk", "positive"),
]


# Employees used for retrieval and answers. Same question, different company,
# must give a different answer.
EMPLOYEES = {
    "emp_1": {"name": "Shreya", "org_id": "org_1", "org": "Nimbus Labs", "department": "Engineering"},
    "emp_2": {"name": "Adithya", "org_id": "org_2", "org": "Veltrix Corp", "department": "Operations"},
}

# kind:
#   answer    the handbook covers it; expect this document and section, and the
#             answer must contain one of `facts`.
#   no_answer the handbook does not cover it; expect a weak or empty search and
#             an answer that says so rather than guessing.
#   isolation the answer exists, but only in another company's handbook, which
#             must never be shown to this employee.
POLICY_CASES = [
    {"id": "P01", "emp_id": "emp_1", "kind": "answer",
     "question": "How many days of annual leave do I get each year?",
     "doc": "org_1__leave_policy", "section": "Annual leave", "facts": ["24"]},
    {"id": "P02", "emp_id": "emp_2", "kind": "answer",
     "question": "How many days of annual leave do I get each year?",
     "doc": "org_2__leave_policy", "section": "Annual leave", "facts": ["18"]},
    {"id": "P03", "emp_id": "emp_1", "kind": "answer",
     "question": "Do I need a doctor's note if I'm off sick?",
     "doc": "org_1__leave_policy", "section": "Sick leave", "facts": ["three", "3 "]},
    {"id": "P04", "emp_id": "emp_1", "kind": "answer",
     "question": "Can I work from another country for a while?",
     "doc": "org_1__remote_work", "section": "Working from abroad", "facts": ["30 days", "30"]},
    {"id": "P05", "emp_id": "emp_1", "kind": "answer",
     "question": "How much will the company pay towards a desk and chair at home?",
     "doc": "org_1__remote_work", "section": "Equipment at home", "facts": ["15,000", "15000"]},
    {"id": "P06", "emp_id": "emp_1", "kind": "answer",
     "question": "What's the deadline for submitting an expense claim?",
     "doc": "shared__equipment_and_expenses", "section": "Expense claims", "facts": ["30 days", "30"]},
    {"id": "P07", "emp_id": "emp_1", "kind": "answer",
     "question": "Who do I tell if I think customer data has been breached?",
     "doc": "org_1__information_security", "section": "Incidents",
     "facts": ["security@", "one hour", "1 hour"]},
    {"id": "P08", "emp_id": "emp_1", "kind": "answer",
     "question": "Can I take leave while I'm on probation?",
     "doc": "org_1__leave_policy", "section": "Leave during probation", "facts": ["6 days", "six days", "6"]},
    {"id": "P09", "emp_id": "emp_1", "kind": "answer",
     "question": "Can I accept a gift from a supplier?",
     "doc": "shared__code_of_conduct", "section": "Gifts", "facts": ["2,000", "2000"]},
    {"id": "P10", "emp_id": "emp_2", "kind": "answer",
     "question": "What extra pay do I get for working nights?",
     "doc": "org_2__shift_patterns", "section": "Shift allowance", "facts": ["25%", "25 %", "25 percent"]},
    {"id": "P11", "emp_id": "emp_2", "kind": "answer",
     "question": "What protective gear do I need on the production floor?",
     "doc": "org_2__safety_policy", "section": "Personal protective equipment",
     "facts": ["steel-toed", "steel toed", "high-visibility", "eye protection"]},
    {"id": "P12", "emp_id": "emp_2", "kind": "answer",
     "question": "How long is a safety certificate valid for?",
     "doc": "org_2__safety_policy", "section": "Certification", "facts": ["three years", "3 years"]},
    {"id": "P13", "emp_id": "emp_1", "kind": "no_answer",
     "question": "Is there a gym membership or wellness allowance?"},
    {"id": "P14", "emp_id": "emp_1", "kind": "no_answer",
     "question": "What is the company's stock option vesting schedule?"},
    {"id": "P15", "emp_id": "emp_1", "kind": "isolation",
     "question": "What is the lockout-tagout procedure for machine maintenance?",
     "forbidden_org": "org_2"},
    {"id": "P16", "emp_id": "emp_2", "kind": "isolation",
     "question": "Am I allowed to work from abroad, and for how long?",
     "forbidden_org": "org_1"},
]

# Phrases that show the assistant declined rather than invented an answer.
DECLINE_PHRASES = [
    "no documented", "not documented", "don't have", "do not have", "couldn't find",
    "could not find", "not covered", "no information", "doesn't cover", "does not cover",
    "isn't covered", "not mentioned", "no specific", "unable to find", "not able to find",
    "no policy", "raise it with hr", "check with hr", "contact hr", "reach out to hr",
]
