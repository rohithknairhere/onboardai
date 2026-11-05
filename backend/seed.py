from datetime import date, timedelta

from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)


def _days_ago(n: int) -> str:
    """Start dates relative to today.

    Hard-coded dates rot: the original fixture used dates that had drifted into
    the future, so the UI read "Started <future date>" and the risk model's
    elapsed-time feature collapsed to its floor for every employee.
    """
    return (date.today() - timedelta(days=n)).strftime("%b %d, %Y")

organizations_data = [
  {
    "id": "org_1",
    "name": "Nimbus Labs",
    "industry": "Fintech Startup",
    "logo": "N",
  },
  {
    "id": "org_2",
    "name": "Veltrix Corp",
    "industry": "Manufacturing Enterprise",
    "logo": "V",
  }
]

employees_data = [
  {
    "id": "emp_1",
    "name": "Shreya",
    "role": "Senior Frontend Engineer",
    "department": "Engineering",
    "orgId": "org_1",
    "startDate": _days_ago(25),
    "status": "in_progress", 
    "stage": 2, 
    "progress": 45,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "verified" },
      { "id": "doc_2", "name": "Govt ID / Passport", "status": "pending" },
      { "id": "doc_3", "name": "Direct Deposit Form", "status": "pending" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Systems & Access", "status": "in_progress", "contact": "Alex Wong" },
      { "id": "kt_2", "name": "Ongoing Work (Sprint 42)", "status": "pending", "contact": "Maria Garcia" },
      { "id": "kt_3", "name": "Key Relationships", "status": "pending", "contact": "Alex Wong" },
    ],
    "tasks": [
      { "id": "t_1", "title": "Sign Offer Letter", "completed": True },
      { "id": "t_2", "title": "Upload ID", "completed": False },
      { "id": "t_3", "title": "Request AWS Access", "completed": False },
    ],
    "auditLog": [
      { "time": "2 hours ago", "action": "Offer letter signed and verified." },
      { "time": "1 day ago", "action": "Onboarding initiated by HR." }
    ]
  },
  {
    "id": "emp_2",
    "name": "Adithya",
    "role": "Plant Manager",
    "department": "Operations",
    "orgId": "org_2",
    "startDate": _days_ago(22),
    "status": "blocked",
    "stage": 1,
    "progress": 20,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "verified" },
      { "id": "doc_2", "name": "Safety Certification", "status": "rejected", "reason": "Expired document provided" },
      { "id": "doc_3", "name": "Background Check Consent", "status": "pending" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Safety Protocols", "status": "pending", "contact": "Dr. Evans" },
      { "id": "kt_2", "name": "Shift Handover", "status": "pending", "contact": "James T." },
    ],
    "tasks": [
      { "id": "t_1", "title": "Upload Safety Cert", "completed": False },
    ],
    "auditLog": [
      { "time": "10 mins ago", "action": "HR rejected Safety Certification (Expired)." }
    ]
  },
  {
    "id": "emp_3",
    "name": "Aisha Patel",
    "role": "Product Designer",
    "department": "Design",
    "orgId": "org_1",
    "startDate": _days_ago(45),
    "status": "completed",
    "stage": 5,
    "progress": 100,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "verified" },
      { "id": "doc_2", "name": "Govt ID", "status": "verified" },
      { "id": "doc_3", "name": "IP Agreement", "status": "verified" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Design System overview", "status": "completed", "contact": "Design Team" },
    ],
    "tasks": [
      { "id": "t_1", "title": "Attend Orientation", "completed": True },
    ],
    "auditLog": [
      { "time": "3 days ago", "action": "Onboarding completed successfully." }
    ]
  },
  {
    "id": "emp_4",
    "name": "David Chen",
    "role": "Logistics Coordinator",
    "department": "Supply Chain",
    "orgId": "org_2",
    "startDate": _days_ago(5),
    "status": "in_progress",
    "stage": 0,
    "progress": 5,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "pending" },
      { "id": "doc_2", "name": "Govt ID", "status": "pending" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Vendor Management System", "status": "pending", "contact": "Sarah L." }
    ],
    "tasks": [
      { "id": "t_1", "title": "Sign Offer Letter", "completed": False }
    ],
    "auditLog": [
      { "time": "Just now", "action": "Welcome email sent." }
    ]
  },
  {
    "id": "emp_5",
    "name": "Elena Rodriguez",
    "role": "Compliance Officer",
    "department": "Legal",
    "orgId": "org_1",
    "startDate": _days_ago(31),
    "status": "in_progress",
    "stage": 4,
    "progress": 80,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "verified" },
      { "id": "doc_2", "name": "Govt ID", "status": "verified" },
      { "id": "doc_3", "name": "Bar Association Cert", "status": "verified" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Internal Policies", "status": "completed", "contact": "Legal VP" }
    ],
    "tasks": [
      { "id": "t_1", "title": "Complete AML Training", "completed": False }
    ],
    "auditLog": [
      { "time": "1 hour ago", "action": "IT Access Provisioned." }
    ]
  },
  {
    "id": "emp_6",
    "name": "James Wilson",
    "role": "Assembly Line Lead",
    "department": "Operations",
    "orgId": "org_2",
    "startDate": _days_ago(38),
    "status": "in_progress",
    "stage": 3,
    "progress": 60,
    "requiredDocuments": [
      { "id": "doc_1", "name": "Offer Letter Signed", "status": "verified" },
      { "id": "doc_2", "name": "Safety Certification", "status": "verified" },
    ],
    "ktSections": [
      { "id": "kt_1", "name": "Equipment Training", "status": "in_progress", "contact": "Marcus T." }
    ],
    "tasks": [
      { "id": "t_1", "title": "Complete Equipment Training", "completed": False }
    ],
    "auditLog": [
      { "time": "Yesterday", "action": "Safety Cert verified by HR." }
    ]
  }
]


def seed():
    db = SessionLocal()
    
    # clear existing data
    for upload in db.query(models.DocumentUpload).all():
        try:
            import storage
            storage.resolve(upload.stored_path).unlink(missing_ok=True)
        except Exception:
            pass
    db.query(models.DocumentUpload).delete()
    db.query(models.Event).delete()
    db.query(models.AuditLog).delete()
    db.query(models.Task).delete()
    db.query(models.KTSection).delete()
    db.query(models.RequiredDocument).delete()
    db.query(models.Employee).delete()
    db.query(models.Organization).delete()
    
    for org_data in organizations_data:
        org = models.Organization(
            id=org_data["id"],
            name=org_data["name"],
            industry=org_data["industry"],
            logo=org_data["logo"]
        )
        db.add(org)
    
    for emp_data in employees_data:
        emp = models.Employee(
            id=emp_data["id"],
            name=emp_data["name"],
            role=emp_data["role"],
            department=emp_data["department"],
            orgId=emp_data["orgId"],
            startDate=emp_data["startDate"],
            status=emp_data["status"],
            stage=emp_data["stage"],
            progress=emp_data["progress"]
        )
        db.add(emp)
        
        for doc in emp_data.get("requiredDocuments", []):
            db.add(models.RequiredDocument(
                id=doc["id"] + "_" + emp.id,
                name=doc["name"],
                status=doc["status"],
                reason=doc.get("reason"),
                empId=emp.id
            ))
            
        for kt in emp_data.get("ktSections", []):
            db.add(models.KTSection(
                id=kt["id"] + "_" + emp.id,
                name=kt["name"],
                status=kt["status"],
                contact=kt["contact"],
                empId=emp.id
            ))
            
        for t in emp_data.get("tasks", []):
            db.add(models.Task(
                id=t["id"] + "_" + emp.id,
                title=t["title"],
                completed=t["completed"],
                empId=emp.id
            ))
            
        for log in emp_data.get("auditLog", []):
            db.add(models.AuditLog(
                time=log["time"],
                action=log["action"],
                empId=emp.id
            ))
            
    db.commit()
    db.close()
    print("Database seeded!")

if __name__ == "__main__":
    seed()
