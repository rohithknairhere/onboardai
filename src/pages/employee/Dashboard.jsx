import React, { useState, useRef } from 'react';
import { useAppContext } from '../../context/AppContext';
import { StageTracker } from '../../components/StageTracker';
import { StatusPill } from '../../components/StatusPill';
import { UploadCloud, CheckCircle2, Circle, FileText, Users, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

export const EmployeeDashboard = () => {
  const { currentUser, updateEmployeeTask, standardDocs, uploadDocument } = useAppContext();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [uploadNotice, setUploadNotice] = useState(null);
  const fileInputRef = useRef(null);
  const targetDocRef = useRef(null);

  if (!currentUser) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const sendFile = async (file, requiredDocId) => {
    if (!file) return;
    setUploadError(null);
    setUploadNotice(null);
    setUploading(requiredDocId || 'general');
    try {
      const result = await uploadDocument(currentUser.id, file, requiredDocId);
      // The upload response already carries the automated verdict, so say what
      // happened instead of implying the file is still waiting.
      const outcome = {
        auto_approved: { tone: 'success', text: 'verified automatically' },
        auto_rejected: { tone: 'error', text: 'could not be accepted' },
      }[result.verdict] || { tone: 'review', text: 'sent to HR for a quick review' };
      setUploadNotice({
        tone: outcome.tone,
        text: `${result.filename} ${outcome.text}.${result.reason && result.verdict !== 'auto_approved' ? ` ${result.reason}` : ''}`,
      });
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(null);
    }
  };

  const openPicker = (requiredDocId = null) => {
    targetDocRef.current = requiredDocId;
    fileInputRef.current?.click();
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    sendFile(file, targetDocRef.current);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    const pendingDoc = currentUser.requiredDocuments.find(
      d => d.status === 'pending' || d.status === 'rejected'
    );
    sendFile(file, pendingDoc?.id || null);
  };

  return (
    <div className="animate-in fade-in duration-500">
      {/* Header Section */}
      <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl mb-1">{currentUser.name}</h1>
          <p className="text-text-secondary">
            {currentUser.role} &middot; Started {currentUser.startDate}
          </p>
        </div>
        <div className="w-full md:w-64">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-text-secondary">Overall Progress</span>
            <span className="text-accent-gold font-medium">{currentUser.progress}%</span>
          </div>
          <div className="w-full h-2 bg-surface-nested rounded-full overflow-hidden">
            <div 
              className="h-full bg-accent-gold transition-all duration-1000 ease-out"
              style={{ width: `${currentUser.progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      <StageTracker currentStage={currentUser.stage} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-12">
        {/* Left Column: Tasks & Documents */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-xl mb-4 flex items-center gap-2">
              <CheckCircle2 className="text-text-secondary" /> Action Items
            </h2>
            <div className="space-y-3">
              {currentUser.tasks.map(task => (
                <div 
                  key={task.id} 
                  className="card-nested flex items-center justify-between cursor-pointer hover:border-accent-gold/50 transition-colors group"
                  onClick={() => updateEmployeeTask(currentUser.id, task.id, !task.completed)}
                >
                  <div className="flex items-center gap-3">
                    {task.completed ? (
                      <CheckCircle2 className="text-accent-gold" size={20} />
                    ) : (
                      <Circle className="text-text-secondary group-hover:text-accent-gold/50 transition-colors" size={20} />
                    )}
                    <span className={task.completed ? 'text-text-secondary line-through' : 'text-text-main'}>
                      {task.title}
                    </span>
                  </div>
                </div>
              ))}
              {currentUser.tasks.length === 0 && (
                <p className="text-text-secondary text-sm">No pending tasks for this stage.</p>
              )}
            </div>
          </div>

          <div className="card">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl flex items-center gap-2">
                <FileText className="text-text-secondary" /> Required Documents
              </h2>
              <div className="flex items-center gap-2 text-xs text-text-secondary bg-surface-nested px-3 py-1.5 rounded-md border border-subtle">
                <AlertCircle size={14} className="text-accent-gold" />
                <span>Tailored for {currentUser.role} at {currentUser.orgId === 'org_1' ? 'Nimbus Labs' : 'Veltrix Corp'}</span>
              </div>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              className="hidden"
              onChange={handleFileInput}
            />

            {uploadError && (
              <div className="mb-4 text-sm text-status-error bg-status-error/10 border border-status-error/30 rounded-lg px-3 py-2">
                {uploadError}
              </div>
            )}
            {uploadNotice && (
              <div className={`mb-4 text-sm rounded-lg px-3 py-2 border ${
                uploadNotice.tone === 'success' ? 'text-status-success bg-status-success/10 border-status-success/30'
                  : uploadNotice.tone === 'error' ? 'text-status-error bg-status-error/10 border-status-error/30'
                  : 'text-accent-gold bg-accent-gold/10 border-accent-gold/30'}`}>
                {uploadNotice.text}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div
                className={`border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 transition-colors ${
                  dragActive ? 'border-accent-gold bg-accent-gold/5' : 'border-subtle hover:border-text-secondary'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                {uploading === 'general' ? (
                  <Loader2 size={32} className="text-accent-gold mb-3 animate-spin" />
                ) : (
                  <UploadCloud size={32} className="text-text-secondary mb-3" />
                )}
                <p className="text-sm text-center mb-1">Drag and drop files here</p>
                <p className="text-xs text-text-secondary text-center mb-4">PDF, JPG, PNG up to 10MB</p>
                <button
                  type="button"
                  onClick={() => openPicker(null)}
                  disabled={uploading !== null}
                  className="btn-secondary text-sm py-1.5 disabled:opacity-50"
                >
                  Browse Files
                </button>
              </div>

              <div className="space-y-3">
                {currentUser.requiredDocuments.map(doc => (
                  <div key={doc.id} className="card-nested flex flex-col justify-center py-2 px-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm truncate mr-2" title={doc.name}>{doc.name}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <StatusPill status={doc.status} />
                        {doc.status !== 'verified' && (
                          <button
                            type="button"
                            onClick={() => openPicker(doc.id)}
                            disabled={uploading !== null}
                            className="text-xs text-accent-gold hover:underline disabled:opacity-50 disabled:no-underline"
                          >
                            {uploading === doc.id ? 'Uploading...' : 'Upload'}
                          </button>
                        )}
                      </div>
                    </div>
                    {doc.reason && (
                      <p className="text-xs text-status-error mt-1">{doc.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {currentUser.stage > 1 && (
            <div className="card">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl flex items-center gap-2">
                  <FileText className="text-text-secondary" /> Organizational Standard Documents
                </h2>
              </div>
              <p className="text-sm text-text-secondary mb-4">
                These documents have been made available to you because you successfully completed the Document Verification stage.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {standardDocs.map(doc => (
                  <div key={doc.id} className="card-nested p-4 flex flex-col justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-text-main mb-2">{doc.name}</h3>
                      <p className="text-xs text-text-secondary mb-4 line-clamp-2">{doc.description}</p>
                    </div>
                    <button className="btn-secondary text-xs py-1.5 self-start">Download PDF</button>
                  </div>
                ))}
                {standardDocs.length === 0 && (
                  <div className="col-span-full text-sm text-text-secondary">No standard documents available.</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: KT Tracker */}
        <div className="space-y-6">
          <div className="card h-full">
            <h2 className="text-xl mb-4 flex items-center gap-2">
              <Users className="text-text-secondary" /> Knowledge Transfer
            </h2>
            <p className="text-sm text-text-secondary mb-6">
              Your personalized KT plan based on similar {currentUser.department} roles.
            </p>
            
            <div className="space-y-4">
              {currentUser.ktSections.map(kt => (
                <div key={kt.id} className="relative pl-4 border-l-2 border-subtle py-1">
                  <div className={`absolute -left-[5px] top-3 w-2 h-2 rounded-full ${
                    kt.status === 'completed' ? 'bg-status-success' : 
                    kt.status === 'in_progress' ? 'bg-accent-gold' : 'bg-surface-nested border border-subtle'
                  }`}></div>
                  <h3 className="text-sm font-medium">{kt.name}</h3>
                  <p className="text-xs text-text-secondary mt-1">With {kt.contact}</p>
                </div>
              ))}
            </div>
            
            <div className="mt-8 p-4 bg-surface-nested rounded-lg border border-subtle text-sm">
              <div className="flex items-center gap-2 mb-2 text-text-main">
                <ShieldCheck size={16} className="text-status-success" />
                <span className="font-medium">IT Access Status</span>
              </div>
              <p className="text-text-secondary text-xs">
                Your hardware and software requests are being handled automatically by the IT Provisioning Agent.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
