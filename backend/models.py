from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
from database import Base


def _utcnow():
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    industry = Column(String)
    logo = Column(String)

    employees = relationship("Employee", back_populates="organization")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)
    department = Column(String)
    orgId = Column(String, ForeignKey("organizations.id"))
    startDate = Column(String)
    status = Column(String)
    stage = Column(Integer)
    progress = Column(Integer)

    organization = relationship("Organization", back_populates="employees")
    requiredDocuments = relationship("RequiredDocument", back_populates="employee")
    ktSections = relationship("KTSection", back_populates="employee")
    tasks = relationship("Task", back_populates="employee")
    auditLog = relationship("AuditLog", back_populates="employee")


class RequiredDocument(Base):
    __tablename__ = "required_documents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    reason = Column(String, nullable=True)
    empId = Column(String, ForeignKey("employees.id"))

    employee = relationship("Employee", back_populates="requiredDocuments")


class KTSection(Base):
    __tablename__ = "kt_sections"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    contact = Column(String)
    empId = Column(String, ForeignKey("employees.id"))

    employee = relationship("Employee", back_populates="ktSections")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    completed = Column(Boolean, default=False)
    empId = Column(String, ForeignKey("employees.id"))

    employee = relationship("Employee", back_populates="tasks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    time = Column(String)
    action = Column(String)
    empId = Column(String, ForeignKey("employees.id"))

    employee = relationship("Employee", back_populates="auditLog")


class Event(Base):
    """Structured, machine-readable record of everything that happens.

    Distinct from AuditLog, which is prose for humans. This table is the
    feature source for the risk model, the agent's memory, and evaluation.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    empId = Column(String, ForeignKey("employees.id"), index=True, nullable=True)
    event_type = Column(String, index=True)
    actor = Column(String)
    payload = Column(JSON, default=dict)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)


class DocumentUpload(Base):
    """One uploaded file plus whatever the ML pipeline concluded about it.

    A RequiredDocument is the obligation; this is an attempt to satisfy it, so
    a rejected-then-resubmitted document yields several rows.
    """
    __tablename__ = "document_uploads"

    id = Column(String, primary_key=True, index=True)
    empId = Column(String, ForeignKey("employees.id"), index=True)
    requiredDocId = Column(String, ForeignKey("required_documents.id"), nullable=True)

    original_filename = Column(String)
    stored_path = Column(String)
    content_type = Column(String)
    size_bytes = Column(Integer)
    sha256 = Column(String, index=True)
    uploaded_at = Column(DateTime, default=_utcnow, index=True)

    ocr_text = Column(Text, nullable=True)
    predicted_type = Column(String, nullable=True)
    predicted_confidence = Column(Float, nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    validations = Column(JSON, nullable=True)
    verdict = Column(String, default="pending")
    model_version = Column(String, nullable=True)

    # Kept separate from `verdict` on purpose: the gap between what the model
    # predicted and what HR decided is the training signal for the next model.
    hr_decision = Column(String, nullable=True)
    hr_decided_at = Column(DateTime, nullable=True)
