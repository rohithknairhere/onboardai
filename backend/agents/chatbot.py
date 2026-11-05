"""Routes a message to a specialist agent and runs it.

Routing is done by the trained intent classifier rather than by asking an LLM
which agent to use. That is deliberate: it is one model call cheaper, it is
deterministic and therefore testable, and its accuracy is measurable against a
confusion matrix (see ml/artifacts/nlp_report.md). Below the classifier's
confidence floor nothing is routed and the default specialist answers, because a
vague message genuinely does not identify a specialist.

Specialists may transfer once if a message reaches the wrong one, which covers
the classifier's residual error without risking a loop.
"""
import logging

from langgraph.checkpoint.memory import InMemorySaver

import llm_provider
import models
from agents import specialists
from agents.specialists import Context, Handoff
from database import SessionLocal
from ml import nlp_models

logger = logging.getLogger(__name__)

_checkpointer = InMemorySaver()


def reset_memory():
    """Forget every conversation. Used when the demo data is reset."""
    global _checkpointer
    _checkpointer = InMemorySaver()

MAX_TRANSFERS = 1

# Said when the model returns nothing. An honest "I don't know" is better than
# an error-like message, and the employee still has a next step.
NO_ANSWER_REPLY = ("I'm not able to give you a reliable answer to that. I can raise it with HR "
                   "so someone can get back to you, if you'd like.")


def _as_text(content) -> str:
    """Flatten a message's content to plain text.

    Newer models (Gemini 3.x among them) return a list of typed blocks, some of
    which are internal reasoning that must not be shown to the employee.
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p).strip()
    return str(content).strip() if content else ""


def _load_employee(emp_id: str) -> dict | None:
    """Read the employee into a plain dict.

    Returning the ORM object would detach it when the session closes and every
    relationship access afterwards would raise DetachedInstanceError.
    """
    db = SessionLocal()
    try:
        emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
        if not emp:
            return None
        return {
            "name": emp.name,
            "role": emp.role,
            "department": emp.department,
            "org": emp.organization.name if emp.organization else "your organisation",
            "org_id": emp.orgId,
            "stage": emp.stage,
            "status": emp.status,
            "progress": emp.progress,
        }
    finally:
        db.close()


def route(message: str) -> dict:
    """Pick a specialist for a message using the intent classifier."""
    analysis = nlp_models.analyse(message)
    agent = analysis.get("agent") or specialists.DEFAULT_SPECIALIST
    if agent not in specialists.SPECIALISTS:
        agent = specialists.DEFAULT_SPECIALIST
    return {"specialist": agent,
            "intent": analysis.get("intent"),
            "confidence": analysis.get("intent_confidence"),
            "routed": analysis.get("routed", False)}


def _run(specialist: str, message: str, employee: dict, ctx: Context, handoff: Handoff,
         thread_tag: str | None = None, received_from: str | None = None,
         reason: str | None = None):
    """Build and invoke one specialist. Agents are rebuilt per call so a changed
    employee record cannot leave a stale system prompt in a cache; conversation
    history lives in the checkpointer, not in the agent object.

    A specialist that has just received a transfer is not given the transfer
    tool. With it, the receiving agent would try to pass the message on again,
    be refused, and reply "I'll transfer you" instead of answering.
    """
    from langchain.agents import create_agent

    prompt = specialists.build_prompt(specialist, employee)
    if received_from:
        prompt += (f"\n\nThe {received_from} has passed this message to you"
                   + (f" because: {reason}" if reason else "")
                   + ". It is yours now. Do not transfer it and do not say you are passing "
                     "it on. Use your tools and answer the employee directly.")

    agent = create_agent(
        model=llm_provider.get_llm(temperature=0.2),
        tools=specialists.build_tools(specialist, ctx, handoff,
                                      allow_transfer=received_from is None),
        system_prompt=prompt,
        checkpointer=_checkpointer,
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        # Threads are per specialist: replaying another specialist's tool calls
        # into an agent that does not hold those tools is not safe.
        config={"configurable": {"thread_id": f"{thread_tag or ctx.emp_id}:{specialist}"}},
    )
    return _as_text(getattr(result["messages"][-1], "content", None))


def process_chat_message(message: str, emp_id: str = None,
                         specialist: str | None = None,
                         thread_tag: str | None = None) -> dict:
    """Answer a message. Returns the reply plus which specialist produced it."""
    fallback = {"response": "", "specialist": specialists.DEFAULT_SPECIALIST,
                "transferred_from": None, "transfer_reason": None}

    if not emp_id:
        return {**fallback,
                "response": "I need to know who you are before I can help. Please sign in again."}

    employee = _load_employee(emp_id)
    if not employee:
        return {**fallback,
                "response": "I couldn't find your employee record. Please contact HR."}

    if specialist not in specialists.SPECIALISTS:
        specialist = route(message)["specialist"]

    ctx = Context(emp_id=emp_id, org_id=employee.get("org_id"),
                  department=employee.get("department"), employee_name=employee["name"])

    started_with = specialist
    transferred_from = None
    transfer_reason = None

    try:
        for _ in range(MAX_TRANSFERS + 1):
            handoff = Handoff(history=[started_with] if transferred_from else [])
            text = _run(specialist, message, employee, ctx, handoff, thread_tag,
                        received_from=transferred_from, reason=transfer_reason)

            if handoff.target and handoff.target != specialist:
                logger.info("Transfer %s -> %s: %s", specialist, handoff.target, handoff.reason)
                transferred_from = specialist
                transfer_reason = handoff.reason
                specialist = handoff.target
                continue

            return {"response": text or NO_ANSWER_REPLY,
                    "specialist": specialist,
                    "transferred_from": transferred_from,
                    "transfer_reason": transfer_reason}

        return {"response": text or NO_ANSWER_REPLY,
                "specialist": specialist,
                "transferred_from": transferred_from,
                "transfer_reason": transfer_reason}

    except Exception as exc:
        logger.exception("Agent invocation failed")
        name = type(exc).__name__.lower()
        provider = llm_provider.active_provider()
        model = llm_provider.active_model()

        if "ratelimit" in name or "resourceexhausted" in name or "quota" in str(exc).lower():
            text = ("I've hit the usage limit on the AI service for the moment, so I can't "
                    "answer right now. Please try again shortly — your dashboard is unaffected.")
        elif any(t in name for t in ("connect", "timeout", "unavailable", "notfound",
                                     "auth", "permission")):
            text = (f"I can't reach the {provider} model '{model}' right now, so AI features "
                    f"are offline. Your dashboard still works normally. "
                    f"(Technical detail: {type(exc).__name__}: {exc})")
        else:
            text = ("Something went wrong while I was working on that, so I haven't changed "
                    "anything. Please try again, or contact HR if it keeps happening. "
                    f"(Technical detail: {type(exc).__name__}: {exc})")

        return {**fallback, "response": text, "specialist": specialist}
