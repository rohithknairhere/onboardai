"""Helper for writing to the structured event stream.

Every state change in the app should pass through here. Downstream consumers
(risk model features, agent memory, evaluation) read only from this table, so
an action that skips it is invisible to the ML layer.
"""
import models


def record(
    db,
    event_type: str,
    actor: str,
    emp_id: str | None = None,
    payload: dict | None = None,
    confidence: float | None = None,
    audit: str | None = None,
    commit: bool = True,
):
    event = models.Event(
        empId=emp_id,
        event_type=event_type,
        actor=actor,
        payload=payload or {},
        confidence=confidence,
    )
    db.add(event)

    if audit and emp_id:
        db.add(models.AuditLog(time="Just now", action=audit, empId=emp_id))

    if commit:
        db.commit()
    return event
