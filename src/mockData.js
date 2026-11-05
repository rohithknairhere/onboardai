export const organizations = [
  {
    id: "org_1",
    name: "Nimbus Labs",
    industry: "Fintech Startup",
    logo: "N",
  },
  {
    id: "org_2",
    name: "Veltrix Corp",
    industry: "Manufacturing Enterprise",
    logo: "V",
  }
];

export const employees = [
  {
    id: "emp_1",
    name: "Sarah Jenkins",
    role: "Senior Frontend Engineer",
    department: "Engineering",
    orgId: "org_1",
    startDate: "Oct 12, 2026",
    status: "in_progress", 
    stage: 2, 
    progress: 45,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "verified" },
      { id: "doc_2", name: "Govt ID / Passport", status: "pending" },
      { id: "doc_3", name: "Direct Deposit Form", status: "pending" },
    ],
    ktSections: [
      { id: "kt_1", name: "Systems & Access", status: "in_progress", contact: "Alex Wong" },
      { id: "kt_2", name: "Ongoing Work (Sprint 42)", status: "pending", contact: "Maria Garcia" },
      { id: "kt_3", name: "Key Relationships", status: "pending", contact: "Alex Wong" },
    ],
    tasks: [
      { id: "t_1", title: "Sign Offer Letter", completed: true },
      { id: "t_2", title: "Upload ID", completed: false },
      { id: "t_3", title: "Request AWS Access", completed: false },
    ],
    auditLog: [
      { time: "2 hours ago", action: "Offer letter signed and verified." },
      { time: "1 day ago", action: "Onboarding initiated by HR." }
    ]
  },
  {
    id: "emp_2",
    name: "Marcus Thorne",
    role: "Plant Manager",
    department: "Operations",
    orgId: "org_2",
    startDate: "Oct 15, 2026",
    status: "blocked",
    stage: 1,
    progress: 20,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "verified" },
      { id: "doc_2", name: "Safety Certification", status: "rejected", reason: "Expired document provided" },
      { id: "doc_3", name: "Background Check Consent", status: "pending" },
    ],
    ktSections: [
      { id: "kt_1", name: "Safety Protocols", status: "pending", contact: "Dr. Evans" },
      { id: "kt_2", name: "Shift Handover", status: "pending", contact: "James T." },
    ],
    tasks: [
      { id: "t_1", title: "Upload Safety Cert", completed: false },
    ],
    auditLog: [
      { time: "10 mins ago", action: "HR rejected Safety Certification (Expired)." }
    ]
  },
  {
    id: "emp_3",
    name: "Aisha Patel",
    role: "Product Designer",
    department: "Design",
    orgId: "org_1",
    startDate: "Oct 1, 2026",
    status: "completed",
    stage: 5,
    progress: 100,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "verified" },
      { id: "doc_2", name: "Govt ID", status: "verified" },
      { id: "doc_3", name: "IP Agreement", status: "verified" },
    ],
    ktSections: [
      { id: "kt_1", name: "Design System overview", status: "completed", contact: "Design Team" },
    ],
    tasks: [
      { id: "t_1", title: "Attend Orientation", completed: true },
    ],
    auditLog: [
      { time: "3 days ago", action: "Onboarding completed successfully." }
    ]
  },
  {
    id: "emp_4",
    name: "David Chen",
    role: "Logistics Coordinator",
    department: "Supply Chain",
    orgId: "org_2",
    startDate: "Oct 18, 2026",
    status: "in_progress",
    stage: 0,
    progress: 5,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "pending" },
      { id: "doc_2", name: "Govt ID", status: "pending" },
    ],
    ktSections: [
      { id: "kt_1", name: "Vendor Management System", status: "pending", contact: "Sarah L." }
    ],
    tasks: [
      { id: "t_1", title: "Sign Offer Letter", completed: false }
    ],
    auditLog: [
      { time: "Just now", action: "Welcome email sent." }
    ]
  },
  {
    id: "emp_5",
    name: "Elena Rodriguez",
    role: "Compliance Officer",
    department: "Legal",
    orgId: "org_1",
    startDate: "Oct 20, 2026",
    status: "in_progress",
    stage: 4,
    progress: 80,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "verified" },
      { id: "doc_2", name: "Govt ID", status: "verified" },
      { id: "doc_3", name: "Bar Association Cert", status: "verified" },
    ],
    ktSections: [
      { id: "kt_1", name: "Internal Policies", status: "completed", contact: "Legal VP" }
    ],
    tasks: [
      { id: "t_1", title: "Complete AML Training", completed: false }
    ],
    auditLog: [
      { time: "1 hour ago", action: "IT Access Provisioned." }
    ]
  },
  {
    id: "emp_6",
    name: "James Wilson",
    role: "Assembly Line Lead",
    department: "Operations",
    orgId: "org_2",
    startDate: "Oct 5, 2026",
    status: "in_progress",
    stage: 3,
    progress: 60,
    requiredDocuments: [
      { id: "doc_1", name: "Offer Letter Signed", status: "verified" },
      { id: "doc_2", name: "Safety Certification", status: "verified" },
    ],
    ktSections: [
      { id: "kt_1", name: "Equipment Training", status: "in_progress", contact: "Marcus T." }
    ],
    tasks: [
      { id: "t_1", title: "Complete Equipment Training", completed: false }
    ],
    auditLog: [
      { time: "Yesterday", action: "Safety Cert verified by HR." }
    ]
  }
];

export const stages = [
  "Pre-boarding",
  "Documents",
  "IT Setup",
  "Knowledge Transfer",
  "Compliance",
  "Orientation"
];
