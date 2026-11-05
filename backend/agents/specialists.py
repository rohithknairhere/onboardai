"""Specialist agents and the tools each one is allowed to use.

Previously a single agent held every tool and the UI merely displayed a label
chosen by the intent classifier, which implied an architecture that did not
exist. Here each specialist is a separate agent with its own system prompt and
its own tool subset, so the Policy agent genuinely cannot complete a task and
the Onboarding agent genuinely cannot read the policy corpus.

Capability boundaries are enforced by construction rather than by instruction:
a specialist is only ever handed the tools listed in its registry entry.

Every tool is built inside a closure over the authenticated employee id, which
is never a model-supplied argument, so no prompt can make any specialist address
another employee's record.
"""
import logging
from dataclasses import dataclass, field

from langchain_core.tools import tool

import events
import models
from database import SessionLocal
from ml import rag

logger = logging.getLogger(__name__)


@dataclass
class Context:
    emp_id: str
    org_id: str | None = None
    department: str | None = None
    employee_name: str = ""


@dataclass
class Handoff:
    """Records a specialist's request to pass the conversation on.

    A tool cannot re-enter the graph itself, so it records the request here and
    the dispatcher re-runs against the target once.
    """
    target: str | None = None
    reason: str = ""
    history: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool builders. Each returns a LangChain tool bound to one employee.
# ---------------------------------------------------------------------------

def _t_get_my_status(ctx: Context):
    @tool
    def get_my_status() -> str:
        """Get the employee's onboarding stage, status and progress percentage."""
        db = SessionLocal()
        try:
            emp = db.query(models.Employee).filter(models.Employee.id == ctx.emp_id).first()
            if not emp:
                return "Employee record not found."
            return (f"{emp.name} is at stage {emp.stage} of 5, status '{emp.status}', "
                    f"{emp.progress}% complete. Start date: {emp.startDate}.")
        finally:
            db.close()
    return get_my_status


def _t_list_my_tasks(ctx: Context):
    @tool
    def list_my_tasks() -> str:
        """List the employee's onboarding tasks and whether each one is complete."""
        db = SessionLocal()
        try:
            tasks = db.query(models.Task).filter(models.Task.empId == ctx.emp_id).all()
            if not tasks:
                return "No tasks assigned."
            return "\n".join(
                f"- {t.title} [{'done' if t.completed else 'outstanding'}]" for t in tasks)
        finally:
            db.close()
    return list_my_tasks


def _t_complete_task(ctx: Context):
    @tool
    def complete_task(task_title: str) -> str:
        """Mark one of the employee's onboarding tasks complete.

        Pass the task title exactly as it appears in list_my_tasks.
        """
        db = SessionLocal()
        try:
            tasks = db.query(models.Task).filter(models.Task.empId == ctx.emp_id).all()
            match = next((t for t in tasks
                          if t.title.strip().lower() == task_title.strip().lower()), None)
            if not match:
                available = ", ".join(t.title for t in tasks) or "none"
                return f"No task called '{task_title}'. Available tasks: {available}."
            if match.completed:
                return f"'{match.title}' was already complete."
            match.completed = True
            events.record(db, event_type="task.completed", actor="agent:onboarding",
                          emp_id=ctx.emp_id,
                          payload={"task_id": match.id, "title": match.title},
                          audit=f"Task '{match.title}' completed via OnboardAI assistant.")
            return f"Marked '{match.title}' as complete."
        finally:
            db.close()
    return complete_task


def _t_list_my_documents(ctx: Context):
    @tool
    def list_my_documents() -> str:
        """List required documents, their verification status and any rejection reason."""
        db = SessionLocal()
        try:
            docs = (db.query(models.RequiredDocument)
                    .filter(models.RequiredDocument.empId == ctx.emp_id).all())
            if not docs:
                return "No documents required."
            lines = []
            for d in docs:
                line = f"- {d.name}: {d.status}"
                if d.reason:
                    line += f" (reason: {d.reason})"
                lines.append(line)
            return "\n".join(lines)
        finally:
            db.close()
    return list_my_documents


def _t_list_kt_sessions(ctx: Context):
    @tool
    def list_kt_sessions() -> str:
        """List the employee's knowledge-transfer sessions, their status and contact."""
        db = SessionLocal()
        try:
            sections = (db.query(models.KTSection)
                        .filter(models.KTSection.empId == ctx.emp_id).all())
            if not sections:
                return "No knowledge-transfer sessions have been planned yet."
            return "\n".join(
                f"- {s.name}: {s.status}, contact {s.contact}" for s in sections)
        finally:
            db.close()
    return list_kt_sessions


def _t_raise_it_request(ctx: Context):
    @tool
    def raise_it_request(system: str, details: str) -> str:
        """Raise an IT provisioning request for the employee.

        `system` is the system or hardware needed (for example "AWS", "laptop").
        Use this only once the employee has confirmed they want it raised.
        """
        db = SessionLocal()
        try:
            events.record(db, event_type="it.request_raised", actor="agent:it",
                          emp_id=ctx.emp_id,
                          payload={"system": system[:120], "details": details[:400]},
                          audit=f"IT provisioning request raised for {system[:120]}.")
            return (f"Raised an IT request for {system}. IT and HR can see it on the "
                    f"employee's activity log.")
        finally:
            db.close()
    return raise_it_request


def _t_escalate_to_hr(ctx: Context):
    @tool
    def escalate_to_hr(summary: str) -> str:
        """Escalate this conversation to a human in HR.

        `summary` is a short neutral description of the problem for the HR queue.
        """
        db = SessionLocal()
        try:
            events.record(db, event_type="chat.escalated", actor="agent:escalation",
                          emp_id=ctx.emp_id, payload={"summary": summary[:400]},
                          audit=f"Escalated to HR by the assistant: {summary[:200]}")
            return ("Escalated to HR. A human will pick this up and it is now visible "
                    "on the employee's activity log.")
        finally:
            db.close()
    return escalate_to_hr


def _t_search_company_policy(ctx: Context):
    @tool
    def search_company_policy(question: str) -> str:
        """Search this employee's company policy documents.

        Returns passages with the document and section they came from, which must
        be cited in any answer.
        """
        results = rag.search(question, org_id=ctx.org_id, department=ctx.department, k=3)
        top_score = results[0]["score"] if results else 0.0
        weak = top_score < rag.WEAK_MATCH_SCORE

        if weak:
            db = SessionLocal()
            try:
                events.record(db, event_type="knowledge.gap", actor="agent:policy",
                              emp_id=ctx.emp_id, confidence=top_score,
                              payload={"question": question[:400], "top_score": top_score,
                                       "had_results": bool(results)})
            finally:
                db.close()

        if not results:
            return ("NO_POLICY_FOUND. Nothing in the company documents covers this. "
                    "Tell the employee you have no documented answer and offer to raise "
                    "it with HR. Do not answer from general knowledge.")

        body = "\n\n".join(
            f"[source: {r['doc_title']} — {r['section']}]\n{r['text']}" for r in results)
        if weak:
            return ("WEAK_MATCH: nothing in the corpus closely matches this question. The "
                    "passages below are related but may not answer it. Cite them only if "
                    "they genuinely do; otherwise say you have no documented answer.\n\n"
                    + body)
        return body
    return search_company_policy


def _t_handoff(ctx: Context, handoff: Handoff, current: str):
    @tool
    def transfer_to_specialist(specialist: str, reason: str) -> str:
        """Transfer the conversation to a different specialist.

        Use this only when the question is outside your own remit. Valid values
        for `specialist` are: Onboarding Agent, Document Agent, IT Provisioning
        Agent, Knowledge Transfer Agent, Policy Agent, Escalation Agent.
        """
        target = specialist.strip()
        if target not in SPECIALISTS:
            return (f"'{target}' is not a specialist. Choose one of: "
                    f"{', '.join(SPECIALISTS)}.")
        if target == current:
            return "You are already that specialist. Answer with your own tools."
        if handoff.target is not None or current in handoff.history:
            return "A transfer has already happened for this message. Answer as best you can."
        handoff.target = target
        handoff.reason = reason[:300]
        return f"TRANSFER_ACCEPTED to {target}. Stop and say you are passing this on."
    return transfer_to_specialist


TOOL_BUILDERS = {
    "get_my_status": _t_get_my_status,
    "list_my_tasks": _t_list_my_tasks,
    "complete_task": _t_complete_task,
    "list_my_documents": _t_list_my_documents,
    "list_kt_sessions": _t_list_kt_sessions,
    "raise_it_request": _t_raise_it_request,
    "escalate_to_hr": _t_escalate_to_hr,
    "search_company_policy": _t_search_company_policy,
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SPECIALISTS = {
    "Onboarding Agent": {
        "tools": ["get_my_status", "list_my_tasks", "complete_task"],
        "remit": (
            "You handle onboarding progress: what stage the employee is at, what "
            "tasks remain, and marking tasks complete. You are also the default "
            "for general conversation."),
    },
    "Document Agent": {
        "tools": ["list_my_documents", "list_my_tasks"],
        "remit": (
            "You handle required documents: which are outstanding, which were "
            "rejected and why, and what the employee must do next. You cannot "
            "upload files for them; explain that they upload from their dashboard."),
    },
    "IT Provisioning Agent": {
        "tools": ["raise_it_request", "list_my_tasks"],
        "remit": (
            "You handle system access, accounts and hardware. Confirm what the "
            "employee needs, then raise an IT request. Never promise a delivery "
            "date; you do not control the IT queue."),
    },
    "Knowledge Transfer Agent": {
        "tools": ["list_kt_sessions"],
        "remit": (
            "You handle knowledge-transfer sessions: what is planned, its status "
            "and who the contact is. You cannot reschedule sessions; direct "
            "rescheduling requests to the named contact."),
    },
    "Policy Agent": {
        "tools": ["search_company_policy"],
        "remit": (
            "You answer questions about company policy, pay and benefits, strictly "
            "from the policy corpus. You MUST call search_company_policy before "
            "answering and cite the document and section, like: (Leave Policy "
            "(Nimbus Labs) — Annual leave). If the search returns NO_POLICY_FOUND "
            "or WEAK_MATCH, say you have no documented answer and offer to raise it "
            "with HR. Never answer policy from general knowledge: policies differ "
            "between companies and a confident wrong answer about leave or pay "
            "causes real harm."),
    },
    "Escalation Agent": {
        "tools": ["escalate_to_hr", "get_my_status"],
        "remit": (
            "You handle frustration, complaints and anything needing a human. "
            "Acknowledge the problem plainly without being defensive, check their "
            "status if it helps, and escalate to HR. Do not make promises on HR's "
            "behalf."),
    },
}

DEFAULT_SPECIALIST = "Onboarding Agent"

BASE_PROMPT = """You are the {specialist} within OnboardAI, an onboarding assistant.

You are helping:
- Name: {name}
- Role: {role} in {department}
- Organisation: {org}
- Onboarding stage: {stage} of 5 ({status}, {progress}% complete)

Your remit: {remit}

Rules that apply to every specialist:
- Use your tools to look up real data before answering. Never invent a status,
  a date or a deadline.
- STAY IN YOUR REMIT. If the question is outside it, your FIRST action must be
  to call transfer_to_specialist. Do not try to help anyway, do not offer
  alternatives, do not call your own tools first, and do not ask the employee
  whether they would like to be transferred. Just transfer.
  Examples of questions that are NOT yours unless you are the named specialist:
    company policy, leave, pay, benefits  -> Policy Agent
    documents, uploads, rejections        -> Document Agent
    accounts, access, laptops, systems    -> IT Provisioning Agent
    handover or KT sessions               -> Knowledge Transfer Agent
    stage, progress, tasks                -> Onboarding Agent
    complaints, or wanting a human        -> Escalation Agent
- If you genuinely do not know, say so and offer to involve HR.
- Be concise and warm. This person is new and may be anxious.
- Only ever discuss the employee named above."""


def build_tools(specialist: str, ctx: Context, handoff: Handoff, allow_transfer: bool = True):
    spec = SPECIALISTS[specialist]
    tools = [TOOL_BUILDERS[name](ctx) for name in spec["tools"]]
    if allow_transfer:
        tools.append(_t_handoff(ctx, handoff, specialist))
    return tools


def build_prompt(specialist: str, employee: dict) -> str:
    return BASE_PROMPT.format(specialist=specialist,
                              remit=SPECIALISTS[specialist]["remit"],
                              **employee)
