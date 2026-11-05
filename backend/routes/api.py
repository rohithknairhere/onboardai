from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from ml import risk_model

router = APIRouter()


@router.get("/knowledge/gaps")
def knowledge_gaps(db: Session = Depends(get_db)):
    """Questions the policy corpus could not answer.

    Every unanswerable question is a hole in the company's documentation, so
    this turns assistant failures into a work list for HR.
    """
    from ml import rag

    rows = (
        db.query(models.Event)
        .filter(models.Event.event_type == "knowledge.gap")
        .order_by(models.Event.created_at.desc())
        .limit(200)
        .all()
    )

    grouped: dict[str, dict] = {}
    for row in rows:
        question = (row.payload or {}).get("question", "").strip()
        if not question:
            continue
        key = question.lower()
        entry = grouped.setdefault(key, {"question": question, "count": 0,
                                         "employees": set(), "last_asked": row.created_at})
        entry["count"] += 1
        if row.empId:
            entry["employees"].add(row.empId)

    gaps = sorted(
        ({"question": g["question"], "times_asked": g["count"],
          "distinct_employees": len(g["employees"]), "last_asked": g["last_asked"]}
         for g in grouped.values()),
        key=lambda g: (g["distinct_employees"], g["times_asked"]), reverse=True,
    )
    return {"corpus": rag.stats(), "gaps": gaps}


@router.get("/employees/{emp_id}/risk")
def get_employee_risk(emp_id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return risk_model.predict(db, emp)


@router.get("/risk/overview")
def risk_overview(db: Session = Depends(get_db)):
    """Risk score for every employee, highest first, for the HR dashboard."""
    rows = []
    for emp in db.query(models.Employee).all():
        result = risk_model.predict(db, emp)
        if not result.get("available"):
            continue
        rows.append({
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "orgId": emp.orgId,
            "probability": result["probability"],
            "band": result["band"],
            "top_driver": result["drivers"][0] if result["drivers"] else None,
        })
    rows.sort(key=lambda r: r["probability"], reverse=True)
    return {"model_version": risk_model.model_version(), "employees": rows}

@router.get("/organizations", response_model=List[schemas.Organization])
def get_organizations(db: Session = Depends(get_db)):
    return db.query(models.Organization).all()

@router.get("/employees", response_model=List[schemas.Employee])
def get_employees(db: Session = Depends(get_db)):
    return db.query(models.Employee).all()

@router.get("/employees/{emp_id}", response_model=schemas.Employee)
def get_employee(emp_id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/employees/{emp_id}/task/{task_id}")
def update_employee_task(emp_id: str, task_id: str, completed: bool, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == f"{task_id}_{emp_id}").first()
    if not task:
        # Also check without prefix if needed, but our seed uses task_id_emp_id
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    task.completed = completed
    db.commit()
    return {"message": "Task updated"}

@router.put("/employees/{emp_id}/stage")
def hr_override_step(emp_id: str, stage: int, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.stage = stage
    emp.progress = min(100, max(0, stage * 20))
    
    # Create audit log
    log = models.AuditLog(time="Just now", action=f"HR forced stage update to {stage}", empId=emp_id)
    db.add(log)
    db.commit()
    return {"message": "Stage updated"}

@router.put("/employees/{emp_id}/document/{doc_id}")
def hr_update_doc(emp_id: str, doc_id: str, status: str, reason: str = "", db: Session = Depends(get_db)):
    doc = db.query(models.RequiredDocument).filter(models.RequiredDocument.id == f"{doc_id}_{emp_id}").first()
    if not doc:
        doc = db.query(models.RequiredDocument).filter(models.RequiredDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
    
    doc.status = status
    if reason:
        doc.reason = reason
        
    log = models.AuditLog(time="Just now", action=f"HR updated document status to {status}.", empId=emp_id)
    db.add(log)
    db.commit()
    return {"message": "Document updated"}
