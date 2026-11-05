import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';
import { API_BASE_URL } from '../../config';
import { StageTracker } from '../../components/StageTracker';
import { StatusPill } from '../../components/StatusPill';
import { DocumentAnalysis } from '../../components/DocumentAnalysis';
import { RiskPanel } from '../../components/RiskPanel';
import { ArrowLeft, FileCheck, History, Check, X, ShieldAlert, UploadCloud } from 'lucide-react';

export const HrEmployeeDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    allEmployees, getOrganization, hrOverrideStep, hrUpdateDoc,
    fetchEmployeeUploads, recordUploadDecision, fetchEmployeeRisk,
  } = useAppContext();

  const employee = allEmployees.find(e => e.id === id);
  const [rejectReason, setRejectReason] = useState('');
  const [activeDoc, setActiveDoc] = useState(null); // for showing reject input
  const [providedDocs, setProvidedDocs] = useState([]);
  const [ktDocs, setKtDocs] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [risk, setRisk] = useState(null);

  const loadUploads = useCallback(async () => {
    if (!id) return;
    setUploads(await fetchEmployeeUploads(id));
  }, [id, fetchEmployeeUploads]);

  const loadRisk = useCallback(async () => {
    if (!id) return;
    setRisk(await fetchEmployeeRisk(id));
  }, [id, fetchEmployeeRisk]);

  useEffect(() => { loadUploads(); }, [loadUploads]);
  useEffect(() => { loadRisk(); }, [loadRisk, allEmployees]);

  if (!employee) return <div>Employee not found</div>;

  const org = getOrganization(employee.orgId);

  // The list arrives newest-first, so the first hit is the current attempt.
  const latestUploadFor = (docId) => uploads.find(u => u.required_doc_id === docId);

  const applyDecision = async (docId, decision, reason = '') => {
    const upload = latestUploadFor(docId);
    if (upload) {
      await recordUploadDecision(upload.id, decision, reason);
      await loadUploads();
    } else {
      await hrUpdateDoc(employee.id, docId, decision, reason);
    }
  };

  const handleApprove = (docId) => {
    applyDecision(docId, 'verified');
    setActiveDoc(null);
  };

  const handleReject = (docId) => {
    if (!rejectReason) {
      alert("Please provide a reason for rejection.");
      return;
    }
    applyDecision(docId, 'rejected', rejectReason);
    setRejectReason('');
    setActiveDoc(null);
  };

  return (
    <div className="animate-in fade-in duration-500">
      <button 
        onClick={() => navigate('/hr/dashboard')}
        className="flex items-center gap-2 text-text-secondary hover:text-text-main transition-colors text-sm mb-6"
      >
        <ArrowLeft size={16} /> Back to Dashboard
      </button>

      <div className="mb-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
        <div>
          <h1 className="text-3xl mb-1">{employee.name}</h1>
          <div className="flex items-center gap-3 text-text-secondary">
            <span>{employee.role}</span>
            <span>&middot;</span>
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded bg-accent-gold/20 text-accent-gold flex items-center justify-center text-[10px] font-bold">
                {org.logo}
              </span>
              <span>{org.name} ({org.industry})</span>
            </div>
            <span>&middot;</span>
            <StatusPill status={employee.status} />
          </div>
        </div>
        
        <div className="card-nested border-dashed border-status-error/50 bg-status-error/5 p-4 md:w-80 flex flex-col items-center text-center">
          <ShieldAlert size={20} className="text-status-error mb-2" />
          <h3 className="text-sm font-medium mb-1">Human-in-the-Loop Override</h3>
          <p className="text-xs text-text-secondary mb-3">
            Manually advance or rollback the ML-driven onboarding stage.
          </p>
          <div className="flex gap-2">
            <button 
              onClick={() => hrOverrideStep(employee.id, Math.max(0, employee.stage - 1))}
              className="btn-secondary text-xs py-1 px-3"
              disabled={employee.stage === 0}
            >
              Rollback
            </button>
            <button 
              onClick={() => hrOverrideStep(employee.id, Math.min(5, employee.stage + 1))}
              className="bg-status-error text-base text-xs font-medium px-3 py-1 rounded-lg transition-colors hover:bg-opacity-90 disabled:opacity-50"
              disabled={employee.stage === 5}
            >
              Force Advance
            </button>
          </div>
        </div>
      </div>

      <StageTracker currentStage={employee.stage} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-12">
        {/* Left Col: Document Verification Queue */}
        <div className="flex flex-col gap-6">
          <div className="card h-fit">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl flex items-center gap-2">
                <FileCheck className="text-text-secondary" /> Document Queue
              </h2>
            </div>

            <div className="space-y-4">
              {employee.requiredDocuments.map(doc => {
                const upload = latestUploadFor(doc.id);
                const awaitingLabel = upload && !upload.hr_decision;
                return (
                <div key={doc.id} className="card-nested p-4 flex flex-col">
                  <div className="flex justify-between items-start mb-3">
                    <div className="min-w-0 mr-2">
                      <h3 className="text-sm font-medium">{doc.name}</h3>
                      {upload ? (
                        <a
                          href={`${API_BASE_URL}/uploads/${upload.id}/file`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-accent-gold hover:underline truncate block mt-1"
                          title={upload.filename}
                        >
                          {upload.filename}
                        </a>
                      ) : (
                        <p className="text-xs text-text-secondary mt-1">No file uploaded yet</p>
                      )}
                    </div>
                    <StatusPill status={doc.status} />
                  </div>

                  {upload && <DocumentAnalysis upload={upload} />}

                  {(doc.status !== 'verified' || awaitingLabel) && (
                    <div className="flex justify-end gap-2 mt-2 pt-3 border-t border-subtle">
                      {activeDoc === doc.id ? (
                        <div className="w-full flex items-center gap-2">
                          <input 
                            type="text" 
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="Reason for rejection..."
                            className="flex-1 bg-surface-main border border-subtle rounded-lg px-3 py-1.5 text-xs text-text-main outline-none focus:border-status-error transition-colors"
                            autoFocus
                          />
                          <button 
                            onClick={() => handleReject(doc.id)}
                            className="bg-status-error text-base p-1.5 rounded-lg hover:bg-opacity-90"
                            title="Confirm Reject"
                          >
                            <Check size={14} />
                          </button>
                          <button 
                            onClick={() => {setActiveDoc(null); setRejectReason('');}}
                            className="bg-surface-main border border-subtle text-text-secondary p-1.5 rounded-lg hover:text-text-main"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <>
                          <button 
                            onClick={() => setActiveDoc(doc.id)}
                            className="text-xs border border-status-error text-status-error hover:bg-status-error/10 px-3 py-1 rounded-md transition-colors"
                          >
                            Reject
                          </button>
                          <button 
                            onClick={() => handleApprove(doc.id)}
                            className="text-xs bg-status-success text-base hover:bg-opacity-90 px-3 py-1 rounded-md transition-colors"
                          >
                            Approve
                          </button>
                        </>
                      )}
                    </div>
                  )}
                  {doc.reason && doc.status === 'rejected' && (
                    <div className="mt-2 text-xs text-status-error bg-status-error/10 p-2 rounded">
                      Rejection Reason: {doc.reason}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>

          <div className="card h-fit">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl flex items-center gap-2">
                <UploadCloud className="text-text-secondary" /> Provide Documents
              </h2>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Upload forms, welcome letters, or organization policies that this employee must receive.
            </p>
            
            <div 
              className="border-2 border-dashed border-subtle hover:border-text-secondary rounded-xl flex flex-col items-center justify-center p-6 transition-colors cursor-pointer mb-4"
              onClick={() => {
                const docName = prompt("Enter the name of the document you are providing:");
                if (docName) setProvidedDocs([...providedDocs, { id: Date.now(), name: docName, date: new Date().toLocaleDateString() }]);
              }}
            >
              <UploadCloud size={32} className="text-text-secondary mb-3" />
              <p className="text-sm text-center mb-1">Click or drag files here</p>
              <p className="text-xs text-text-secondary text-center">PDF, DOCX up to 15MB</p>
            </div>

            {providedDocs.length > 0 && (
              <div className="space-y-3 mt-4">
                <h3 className="text-sm font-medium mb-2">Sent to Employee</h3>
                {providedDocs.map(doc => (
                  <div key={doc.id} className="card-nested flex items-center justify-between py-2 px-3">
                    <span className="text-sm text-text-main truncate mr-2">{doc.name}</span>
                    <span className="text-xs text-text-secondary shrink-0">{doc.date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card h-fit">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl flex items-center gap-2">
                <UploadCloud className="text-text-secondary" /> Knowledge Transfer (KT)
              </h2>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Upload role-specific manuals, codebases, or technical documentation for KT.
            </p>
            
            <div 
              className="border-2 border-dashed border-subtle hover:border-text-secondary rounded-xl flex flex-col items-center justify-center p-6 transition-colors cursor-pointer mb-4"
              onClick={() => {
                const docName = prompt("Enter the name of the KT document:");
                if (docName) setKtDocs([...ktDocs, { id: Date.now(), name: docName, date: new Date().toLocaleDateString() }]);
              }}
            >
              <UploadCloud size={32} className="text-text-secondary mb-3" />
              <p className="text-sm text-center mb-1">Click or drag KT files here</p>
              <p className="text-xs text-text-secondary text-center">PDF, MD, MP4 up to 50MB</p>
            </div>

            {ktDocs.length > 0 && (
              <div className="space-y-3 mt-4">
                <h3 className="text-sm font-medium mb-2">KT Docs Provided</h3>
                {ktDocs.map(doc => (
                  <div key={doc.id} className="card-nested flex items-center justify-between py-2 px-3">
                    <span className="text-sm text-text-main truncate mr-2">{doc.name}</span>
                    <span className="text-xs text-text-secondary shrink-0">{doc.date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Risk + Activity Log */}
        <div className="flex flex-col gap-6">
        <RiskPanel risk={risk} />

        <div className="card h-fit">
          <h2 className="text-xl mb-6 flex items-center gap-2">
            <History className="text-text-secondary" /> Activity & Audit Log
          </h2>
          
          <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-subtle before:bg-gradient-to-b before:from-transparent before:via-subtle before:to-transparent">
            {employee.auditLog.map((log, i) => (
              <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-4 h-4 rounded-full border-2 border-surface-main bg-accent-gold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 ml-1 md:ml-0 z-10"></div>
                <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] card-nested p-3">
                  <div className="flex items-center justify-between mb-1">
                    <time className="text-xs text-text-secondary">{log.time}</time>
                  </div>
                  <div className="text-sm text-text-main">{log.action}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        </div>
      </div>
    </div>
  );
};
