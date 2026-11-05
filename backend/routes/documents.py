import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import events
import storage
from database import get_db
from ml import pipeline as ml_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# How an automated verdict maps onto the status the UI already renders.
_VERDICT_TO_STATUS = {
    ml_pipeline.VERDICT_APPROVED: "verified",
    ml_pipeline.VERDICT_REJECTED: "rejected",
    ml_pipeline.VERDICT_REVIEW: "pending",
}


def _find_required_doc(db: Session, emp_id: str, required_doc_id: str):
    doc = db.query(models.RequiredDocument).filter(
        models.RequiredDocument.id == required_doc_id
    ).first()
    if not doc:
        doc = db.query(models.RequiredDocument).filter(
            models.RequiredDocument.id == f"{required_doc_id}_{emp_id}"
        ).first()
    return doc


@router.post("/employees/{emp_id}/documents/upload")
def upload_document(
    emp_id: str,
    file: UploadFile = File(...),
    required_doc_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    employee = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    required_doc = None
    if required_doc_id:
        required_doc = _find_required_doc(db, emp_id, required_doc_id)
        if not required_doc:
            raise HTTPException(status_code=404, detail="Required document not found")

    try:
        saved = storage.save_upload(file.file, emp_id, file.content_type)
    except storage.UploadRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    upload = models.DocumentUpload(
        id=saved["id"],
        empId=emp_id,
        requiredDocId=required_doc.id if required_doc else None,
        original_filename=file.filename,
        stored_path=saved["stored_path"],
        content_type=saved["content_type"],
        size_bytes=saved["size_bytes"],
        sha256=saved["sha256"],
        verdict=ml_pipeline.VERDICT_REVIEW,
    )
    db.add(upload)

    events.record(
        db,
        event_type="document.uploaded",
        actor="employee",
        emp_id=emp_id,
        payload={
            "upload_id": upload.id,
            "required_doc_id": required_doc.id if required_doc else None,
            "filename": file.filename,
            "content_type": saved["content_type"],
            "size_bytes": saved["size_bytes"],
        },
        audit=f"Document uploaded: {required_doc.name if required_doc else file.filename}",
        commit=False,
    )

    analysis = None
    try:
        analysis = ml_pipeline.analyse(
            storage.resolve(saved["stored_path"]),
            saved["content_type"],
            requirement_name=required_doc.name if required_doc else None,
            employee_name=employee.name,
        )
    except Exception:
        # A pipeline failure must never lose the employee's upload; the document
        # simply falls through to manual review.
        logger.exception("Document analysis failed for upload %s", upload.id)

    if analysis:
        upload.ocr_text = (analysis["text"] or "")[:20000]
        upload.predicted_type = analysis["predicted_type"]
        upload.predicted_confidence = analysis["predicted_confidence"]
        upload.extracted_fields = analysis["extracted_fields"]
        upload.validations = {
            "checks": analysis["checks"],
            "reason": analysis["reason"],
            "extraction": analysis["extraction"],
            "type_scores": analysis["type_scores"],
        }
        upload.verdict = analysis["verdict"]
        upload.model_version = analysis["model_version"]

        if required_doc:
            required_doc.status = _VERDICT_TO_STATUS.get(analysis["verdict"], "pending")
            required_doc.reason = (
                analysis["reason"] if analysis["verdict"] == ml_pipeline.VERDICT_REJECTED else None
            )

        events.record(
            db,
            event_type="document.analysed",
            actor="model:document-intelligence",
            emp_id=emp_id,
            confidence=analysis["predicted_confidence"],
            payload={
                "upload_id": upload.id,
                "verdict": analysis["verdict"],
                "reason": analysis["reason"],
                "predicted_type": analysis["predicted_type"],
                "model_version": analysis["model_version"],
                "failed_checks": [c["check"] for c in analysis["checks"] if not c["passed"]],
            },
            audit=f"Automated review: {analysis['verdict'].replace('_', ' ')} — {analysis['reason']}",
            commit=False,
        )
    elif required_doc:
        required_doc.status = "pending"
        required_doc.reason = None

    db.commit()

    return {
        "id": upload.id,
        "filename": upload.original_filename,
        "content_type": upload.content_type,
        "size_bytes": upload.size_bytes,
        "verdict": upload.verdict,
        "required_doc_id": upload.requiredDocId,
        "predicted_type": upload.predicted_type,
        "predicted_confidence": upload.predicted_confidence,
        "reason": (upload.validations or {}).get("reason"),
    }


@router.get("/employees/{emp_id}/uploads")
def list_uploads(emp_id: str, db: Session = Depends(get_db)):
    uploads = (
        db.query(models.DocumentUpload)
        .filter(models.DocumentUpload.empId == emp_id)
        .order_by(models.DocumentUpload.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": u.id,
            "filename": u.original_filename,
            "content_type": u.content_type,
            "size_bytes": u.size_bytes,
            "uploaded_at": u.uploaded_at,
            "required_doc_id": u.requiredDocId,
            "verdict": u.verdict,
            "predicted_type": u.predicted_type,
            "predicted_confidence": u.predicted_confidence,
            "extracted_fields": u.extracted_fields,
            "validations": u.validations,
        }
        for u in uploads
    ]


@router.get("/uploads/{upload_id}/file")
def get_upload_file(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(models.DocumentUpload).filter(
        models.DocumentUpload.id == upload_id
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    try:
        path = storage.resolve(upload.stored_path)
    except storage.UploadRejected:
        raise HTTPException(status_code=404, detail="File not found")

    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        media_type=upload.content_type,
        filename=upload.original_filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/uploads/{upload_id}/analysis")
def get_analysis(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(models.DocumentUpload).filter(
        models.DocumentUpload.id == upload_id
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    validations = upload.validations or {}
    return {
        "id": upload.id,
        "filename": upload.original_filename,
        "uploaded_at": upload.uploaded_at,
        "verdict": upload.verdict,
        "reason": validations.get("reason"),
        "predicted_type": upload.predicted_type,
        "predicted_confidence": upload.predicted_confidence,
        "type_scores": validations.get("type_scores", {}),
        "checks": validations.get("checks", []),
        "extraction": validations.get("extraction", {}),
        "extracted_fields": upload.extracted_fields,
        "model_version": upload.model_version,
        "hr_decision": upload.hr_decision,
        "text_preview": (upload.ocr_text or "")[:1500],
    }


class DecisionRequest(BaseModel):
    decision: str
    reason: str = ""


@router.post("/uploads/{upload_id}/decision")
def record_decision(upload_id: str, body: DecisionRequest, db: Session = Depends(get_db)):
    """Record HR's ruling on an upload.

    Beyond updating the document status, this is the labelling step: the pair
    (model verdict, human decision) is what the classifier is retrained on.
    """
    if body.decision not in {"verified", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be 'verified' or 'rejected'")

    upload = db.query(models.DocumentUpload).filter(
        models.DocumentUpload.id == upload_id
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload.hr_decision = body.decision
    upload.hr_decided_at = datetime.now(timezone.utc)

    if upload.requiredDocId:
        doc = db.query(models.RequiredDocument).filter(
            models.RequiredDocument.id == upload.requiredDocId
        ).first()
        if doc:
            doc.status = body.decision
            doc.reason = body.reason or None

    agreed = _VERDICT_TO_STATUS.get(upload.verdict) == body.decision
    events.record(
        db,
        event_type="document.hr_decision",
        actor="hr",
        emp_id=upload.empId,
        payload={
            "upload_id": upload.id,
            "decision": body.decision,
            "reason": body.reason,
            "model_verdict": upload.verdict,
            "model_predicted_type": upload.predicted_type,
            "agreed_with_model": agreed,
        },
        confidence=upload.predicted_confidence,
        audit=f"HR marked document as {body.decision}"
              + (f": {body.reason}" if body.reason else ""),
    )

    return {"id": upload.id, "hr_decision": body.decision, "agreed_with_model": agreed}


@router.get("/ml/model-info")
def model_info():
    """Classifier metadata and held-out evaluation metrics."""
    import json
    from ml import classifier
    from ml.train_classifier import METRICS_PATH

    info = {
        "classifier_available": classifier.is_available(),
        "model_version": classifier.model_version(),
        "thresholds": {
            "auto_approve_confidence": ml_pipeline.AUTO_APPROVE_CONFIDENCE,
            "auto_reject_confidence": ml_pipeline.AUTO_REJECT_CONFIDENCE,
        },
        "metrics": None,
    }
    if METRICS_PATH.exists():
        try:
            info["metrics"] = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to read classifier metrics")
    return info


@router.get("/ml/agreement")
def model_agreement(db: Session = Depends(get_db)):
    """How often HR upheld the automated verdict — the live quality signal."""
    rows = (
        db.query(models.DocumentUpload)
        .filter(models.DocumentUpload.hr_decision.isnot(None))
        .all()
    )
    total = len(rows)
    agreed = sum(1 for r in rows if _VERDICT_TO_STATUS.get(r.verdict) == r.hr_decision)
    return {
        "labelled_uploads": total,
        "agreements": agreed,
        "agreement_rate": (agreed / total) if total else None,
        "pending_labels": db.query(models.DocumentUpload).filter(
            models.DocumentUpload.hr_decision.is_(None)
        ).count(),
    }


@router.get("/employees/{emp_id}/events")
def list_events(emp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Event)
        .filter(models.Event.empId == emp_id)
        .order_by(models.Event.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "actor": e.actor,
            "payload": e.payload,
            "confidence": e.confidence,
            "created_at": e.created_at,
        }
        for e in rows
    ]
