from pydantic import BaseModel
from typing import List, Optional

class TaskBase(BaseModel):
    id: str
    title: str
    completed: bool
    empId: str

class Task(TaskBase):
    class Config:
        from_attributes = True

class RequiredDocumentBase(BaseModel):
    id: str
    name: str
    status: str
    reason: Optional[str] = None
    empId: str

class RequiredDocument(RequiredDocumentBase):
    class Config:
        from_attributes = True

class KTSectionBase(BaseModel):
    id: str
    name: str
    status: str
    contact: str
    empId: str

class KTSection(KTSectionBase):
    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    time: str
    action: str
    empId: str

class AuditLog(AuditLogBase):
    log_id: int
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    id: str
    name: str
    role: str
    department: str
    orgId: str
    startDate: str
    status: str
    stage: int
    progress: int

class Employee(EmployeeBase):
    requiredDocuments: List[RequiredDocument] = []
    ktSections: List[KTSection] = []
    tasks: List[Task] = []
    auditLog: List[AuditLog] = []
    
    class Config:
        orm_mode = True

class OrganizationBase(BaseModel):
    id: str
    name: str
    industry: str
    logo: str

class Organization(OrganizationBase):
    class Config:
        orm_mode = True
