"""Synthetic employee messages for the intent and sentiment classifiers.

Messages carry two independent labels: what the person wants (intent) and how
they feel about it (sentiment). Keeping them independent matters -- "where do I
upload my ID" and "I've asked about my ID three times now" share an intent but
not a mood, and the router must not confuse the two.
"""
import random

INTENTS = [
    "document_help",
    "it_access",
    "kt_schedule",
    "policy_question",
    "status_check",
    "payroll_benefits",
    "escalation",
    "smalltalk",
]

SENTIMENTS = ["negative", "neutral", "positive"]

_TEMPLATES = {
    "document_help": [
        "where do I upload my {doc}",
        "I can't work out how to submit the {doc}",
        "my {doc} was rejected, what do I do now",
        "does the {doc} need to be signed before I send it",
        "is a scan of my {doc} acceptable or do you need the original",
        "I uploaded the {doc} but the status still says pending",
    ],
    "it_access": [
        "I still don't have access to {system}",
        "when will my {system} account be set up",
        "my laptop hasn't arrived yet",
        "can someone reset my {system} password",
        "I need permissions for {system} to start work",
        "my VPN login isn't working",
    ],
    "kt_schedule": [
        "when is my knowledge transfer session",
        "who am I meeting for the {topic} handover",
        "can we move my KT session to next week",
        "has the {topic} walkthrough been scheduled",
        "I'd like more time on the {topic} handover",
    ],
    "policy_question": [
        "how many leave days do I get",
        "what is the policy on working from home",
        "am I allowed to take leave during probation",
        "what is the notice period",
        "is there a policy on {topic} training reimbursement",
        "what are the office hours",
    ],
    "status_check": [
        "what stage am I at",
        "how much of my onboarding is left",
        "what do I still need to complete",
        "am I on track to start on time",
        "what's outstanding on my checklist",
    ],
    "payroll_benefits": [
        "when will I receive my first salary",
        "how do I enrol in health insurance",
        "my bank details need updating",
        "what is included in the benefits package",
        "when does provident fund start",
    ],
    "escalation": [
        "this is the third time I've asked and nobody has replied",
        "I've been waiting {days} days with no response",
        "I'm supposed to start on Monday and nothing is ready",
        "this process is a shambles, can someone actually help",
        "I need to speak to a human being please",
        "I'm seriously reconsidering whether to join",
    ],
    "smalltalk": [
        "thanks, that's helpful",
        "good morning",
        "thank you",
        "ok got it",
        "appreciate the quick reply",
        "that makes sense, cheers",
    ],
}

_SENTIMENT_PREFIX = {
    "negative": [
        "I'm frustrated, ", "This is really annoying. ", "Honestly this is a mess. ",
        "I'm getting worried. ", "Not happy about this. ", "",
    ],
    "neutral": ["", "Hi, ", "Hello, ", "Quick question, ", "Just checking, "],
    "positive": [
        "Thanks so much! ", "This has been great so far. ", "Really enjoying it here. ",
        "Brilliant, ", "", "Loving the onboarding, ",
    ],
}

_SENTIMENT_SUFFIX = {
    "negative": [
        " This is holding everything up.", " I'm losing patience.",
        " Nobody seems to know.", " Very disappointing.", "",
    ],
    "neutral": ["", " Thanks.", " Please advise.", " Let me know."],
    "positive": [
        " Thanks for all the help!", " Everyone has been lovely.",
        " Really appreciate it.", " No rush at all!", "",
    ],
}

_DOCS = ["passport", "govt ID", "offer letter", "safety certificate",
         "direct deposit form", "bank details", "degree certificate"]
_SYSTEMS = ["AWS", "GitHub", "Slack", "Jira", "the VPN", "the HR portal", "email"]
_TOPICS = ["systems and access", "sprint 42", "safety protocols", "the design system",
           "vendor management", "shift handover"]


# Genuinely uninformative messages. A bare "any update?" does not reveal what
# the person wants, and pretending otherwise inflates the reported accuracy.
_VAGUE = [
    "any update?", "still waiting", "hello?", "can someone help",
    "what's happening with this", "following up", "please advise",
    "checking in again", "?", "sorry to chase", "is anyone there",
]

# Clauses that drag a message toward a second intent.
_BLEND_CLAUSES = [
    "also I still can't log in to {system}",
    "and I've not had my {doc} confirmed",
    "by the way when is the {topic} session",
    "also what's the leave policy",
    "and when does my salary come through",
    "also what stage am I at",
]


def _fill(template, rng):
    return (template
            .replace("{doc}", rng.choice(_DOCS))
            .replace("{system}", rng.choice(_SYSTEMS))
            .replace("{topic}", rng.choice(_TOPICS))
            .replace("{days}", str(rng.randint(3, 15))))


def _typo(text, rng):
    chars = list(text)
    for _ in range(max(1, int(len(chars) * 0.02))):
        i = rng.randrange(len(chars))
        if rng.random() < 0.5:
            chars[i] = ""
        elif chars[i].isalpha():
            chars[i] = rng.choice("abcdefghijklmnopqrstuvwxyz")
    return "".join(chars)


def generate(samples_per_intent=420, seed=7):
    """Return (texts, intents, sentiments)."""
    rng = random.Random(seed)
    texts, intents, sentiments = [], [], []

    for intent in INTENTS:
        for _ in range(samples_per_intent):
            # Escalations are rarely cheerful; smalltalk is rarely furious.
            if intent == "escalation":
                sentiment = rng.choices(SENTIMENTS, weights=[0.82, 0.16, 0.02])[0]
            elif intent == "smalltalk":
                sentiment = rng.choices(SENTIMENTS, weights=[0.05, 0.35, 0.60])[0]
            else:
                sentiment = rng.choices(SENTIMENTS, weights=[0.30, 0.45, 0.25])[0]

            roll = rng.random()
            if roll < 0.09 and intent != "smalltalk":
                # Vague chaser: the label is what they actually wanted, but the
                # text does not say so. Irreducible error, exactly as in reality.
                body = rng.choice(_VAGUE)
            else:
                body = _fill(rng.choice(_TEMPLATES[intent]), rng)
                if roll < 0.32:
                    body += ", " + _fill(rng.choice(_BLEND_CLAUSES), rng)

            prefix = rng.choice(_SENTIMENT_PREFIX[sentiment])
            suffix = rng.choice(_SENTIMENT_SUFFIX[sentiment])

            # Escalation bodies are inherently angry and smalltalk bodies
            # inherently warm, so those carry their tone without any marker.
            implicit = intent in ("escalation", "smalltalk")

            if sentiment != "neutral" and not implicit and not prefix and not suffix:
                # Both pools contain an empty option, so without this a positive
                # or negative example could end up with no sentiment marker at
                # all: text indistinguishable from neutral, carrying another label.
                if rng.random() < 0.5:
                    prefix = rng.choice([p for p in _SENTIMENT_PREFIX[sentiment] if p])
                else:
                    suffix = rng.choice([s for s in _SENTIMENT_SUFFIX[sentiment] if s])

            # Mixed signals: polite opener, unhappy substance. The label follows
            # the substance, which is what makes these genuinely hard.
            if sentiment == "negative" and rng.random() < 0.14:
                prefix = rng.choice([
                    "Thanks for getting back to me, but ",
                    "I appreciate the help, however ",
                    "Sorry to be a pain, but ",
                    "No offence to anyone, but ",
                ])

            text = prefix + body + suffix

            if rng.random() < 0.35:
                text = _typo(text, rng)
            if rng.random() < 0.15:
                text = text.lower()
            if rng.random() < 0.10:
                text = text.upper()

            texts.append(text.strip())
            intents.append(intent)
            sentiments.append(sentiment)

    order = list(range(len(texts)))
    rng.shuffle(order)
    return ([texts[i] for i in order],
            [intents[i] for i in order],
            [sentiments[i] for i in order])
