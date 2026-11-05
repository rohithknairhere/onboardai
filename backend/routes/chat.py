from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

import events
from agents.chatbot import process_chat_message
from database import get_db
from ml import nlp_models, pii

router = APIRouter()

# A message this negative is escalated to HR regardless of what it is about.
ESCALATION_SENTIMENT = -0.60


class ChatRequest(BaseModel):
    message: str
    emp_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent: str = "Onboarding Agent"
    routed_to: Optional[str] = None
    transferred_from: Optional[str] = None
    transfer_reason: Optional[str] = None
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    redacted: list[str] = []
    escalated: bool = False


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    analysis = nlp_models.analyse(request.message)

    # Strip identifiers before the text reaches a third-party model.
    safe_message, redacted_types = pii.redact(request.message)

    escalated = (
        analysis.get("intent") == "escalation"
        or (analysis.get("sentiment_score") is not None
            and analysis["sentiment_score"] <= ESCALATION_SENTIMENT)
    )

    # The classifier has already chosen a specialist; pass it through rather than
    # letting the dispatcher classify the same message a second time.
    result = process_chat_message(safe_message, request.emp_id,
                                  specialist=analysis.get("agent"))
    response_text = result["response"]
    answered_by = result["specialist"]

    if request.emp_id:
        # The message body is deliberately not stored: the risk model needs the
        # sentiment score, not the employee's words.
        events.record(
            db,
            event_type="chat.message",
            actor="employee",
            emp_id=request.emp_id,
            confidence=analysis.get("intent_confidence"),
            payload={
                "intent": analysis.get("intent"),
                "agent": answered_by,
                "routed_to": analysis.get("agent"),
                "transferred_from": result.get("transferred_from"),
                "routed": analysis.get("routed", False),
                "sentiment": analysis.get("sentiment_score"),
                "sentiment_label": analysis.get("sentiment"),
                "pii_redacted": redacted_types,
                "escalated": escalated,
            },
            commit=not escalated,
        )

        if escalated:
            events.record(
                db,
                event_type="chat.escalated",
                actor="model:intent-router",
                emp_id=request.emp_id,
                confidence=analysis.get("intent_confidence"),
                payload={"intent": analysis.get("intent"),
                         "sentiment": analysis.get("sentiment_score")},
                audit="Assistant escalated a distressed message to HR.",
            )

    return ChatResponse(
        response=response_text,
        agent=answered_by,
        routed_to=analysis.get("agent"),
        transferred_from=result.get("transferred_from"),
        transfer_reason=result.get("transfer_reason"),
        intent=analysis.get("intent"),
        intent_confidence=analysis.get("intent_confidence"),
        sentiment=analysis.get("sentiment"),
        sentiment_score=analysis.get("sentiment_score"),
        redacted=redacted_types,
        escalated=escalated,
    )
