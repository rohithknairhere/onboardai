import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';
import { StatusPill } from '../../components/StatusPill';
import { RiskBadge } from '../../components/RiskPanel';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Users, Clock, AlertTriangle, FileCheck, Filter, Plus, Edit2, Trash2, FileText, HelpCircle } from 'lucide-react';

export const HrDashboard = () => {
  const {
    allEmployees,
    getOrganization,
    currentUser,
    standardDocs,
    handleAddStandardDoc,
    handleEditStandardDoc,
    handleDeleteStandardDoc,
    fetchRiskOverview,
    fetchKnowledgeGaps,
  } = useAppContext();
  const navigate = useNavigate();

  const defaultOrg = (currentUser && currentUser.orgId !== 'all') ? currentUser.orgId : 'all';
  const [filterOrg, setFilterOrg] = useState(defaultOrg);
  const [riskById, setRiskById] = useState({});
  const [knowledge, setKnowledge] = useState({ gaps: [], corpus: null });

  useEffect(() => {
    let cancelled = false;
    fetchRiskOverview().then(data => {
      if (cancelled) return;
      setRiskById(Object.fromEntries((data.employees || []).map(r => [r.id, r])));
    });
    return () => { cancelled = true; };
  }, [fetchRiskOverview, allEmployees]);

  useEffect(() => {
    let cancelled = false;
    fetchKnowledgeGaps().then(data => { if (!cancelled) setKnowledge(data); });
    return () => { cancelled = true; };
  }, [fetchKnowledgeGaps]);

  const filteredEmployees = filterOrg === 'all' 
    ? allEmployees 
    : allEmployees.filter(e => e.orgId === filterOrg);

  const atRisk = filteredEmployees
    .filter(e => riskById[e.id])
    .sort((a, b) => riskById[b.id].probability - riskById[a.id].probability)
    .slice(0, 4);

  const blockedCount = filteredEmployees.filter(e => e.status === 'blocked').length;
  const pendingDocsCount = filteredEmployees.reduce((acc, emp) => 
    acc + emp.requiredDocuments.filter(d => d.status === 'pending').length, 0
  );

  // Prepare chart data based on stages
  const stageData = [0, 1, 2, 3, 4, 5].map(stageIdx => {
    const stageNames = ["Pre-boarding", "Docs", "IT Setup", "KT", "Compliance", "Orientation"];
    return {
      name: stageNames[stageIdx],
      count: filteredEmployees.filter(e => e.stage === stageIdx).length
    };
  });

  return (
    <div className="animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-8">
        <div>
          <h1 className="text-3xl mb-1">Overview</h1>
          <p className="text-text-secondary">Cross-organization onboarding status</p>
        </div>
        
        <div className="flex items-center gap-2 bg-surface-nested border border-subtle p-1 rounded-lg">
          <Filter size={16} className="text-text-secondary ml-2" />
          <select 
            value={filterOrg} 
            onChange={(e) => setFilterOrg(e.target.value)}
            disabled={currentUser?.orgId !== 'all'}
            className="bg-transparent border-none outline-none text-sm py-1 pr-2 cursor-pointer text-text-main disabled:opacity-50"
          >
            <option value="all" className="bg-surface-main text-text-main">All Organizations</option>
            <option value="org_1" className="bg-surface-main text-text-main">Nimbus Labs (Fintech)</option>
            <option value="org_2" className="bg-surface-main text-text-main">Veltrix Corp (Manufacturing)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-text-secondary mb-1">Active Onboardings</p>
              <p className="text-3xl font-serif text-accent-gold">{filteredEmployees.length}</p>
            </div>
            <Users className="text-text-secondary" />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-text-secondary mb-1">Avg Time-to-Onboard</p>
              <p className="text-3xl font-serif text-text-main">12<span className="text-lg font-sans text-text-secondary ml-1">days</span></p>
            </div>
            <Clock className="text-text-secondary" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-text-secondary mb-1">Pending Docs</p>
              <p className="text-3xl font-serif text-text-main">{pendingDocsCount}</p>
            </div>
            <FileCheck className="text-text-secondary" />
          </div>
        </div>

        <div className="card border-status-error/30">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-status-error mb-1">Blocked / Escalated</p>
              <p className="text-3xl font-serif text-status-error">{blockedCount}</p>
            </div>
            <AlertTriangle className="text-status-error" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="card lg:col-span-2">
          <h2 className="text-xl mb-6">Pipeline Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stageData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(140, 130, 117, 0.1)" vertical={false} />
                <XAxis dataKey="name" stroke="#8C8275" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#8C8275" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip 
                  cursor={{fill: 'rgba(212, 175, 55, 0.05)'}}
                  contentStyle={{ backgroundColor: '#1F2421', border: '1px solid rgba(140, 130, 117, 0.2)', borderRadius: '8px' }}
                  itemStyle={{ color: '#D4AF37' }}
                />
                <Bar dataKey="count" fill="#D4AF37" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-accent-gold" size={18} />
            <h3 className="text-lg">Predicted stall risk</h3>
          </div>
          <p className="text-xs text-text-secondary mb-5">
            Ranked by a model trained on onboarding outcomes. Highest risk first.
          </p>

          <div className="space-y-3">
            {atRisk.map(emp => {
              const risk = riskById[emp.id];
              return (
                <button
                  key={emp.id}
                  onClick={() => navigate(`/hr/employee/${emp.id}`)}
                  className="w-full text-left card-nested p-3 hover:border-accent-gold/50 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-sm text-text-main truncate">{emp.name}</span>
                    <RiskBadge band={risk.band} probability={risk.probability} />
                  </div>
                  {risk.top_driver && (
                    <p className="text-[11px] text-text-secondary truncate">
                      Driven by {risk.top_driver.label}
                    </p>
                  )}
                </button>
              );
            })}
            {atRisk.length === 0 && (
              <p className="text-sm text-text-secondary">
                No risk scores yet. Train the model with <code>python -m ml.train_risk</code>.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="card mb-8">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle className="text-text-secondary" />
          <h2 className="text-xl">Documentation gaps</h2>
        </div>
        <p className="text-sm text-text-secondary mb-6">
          Questions employees asked the assistant that your policy documents do not
          answer. Each one is a page worth writing.
          {knowledge.corpus && (
            <span className="text-text-secondary">
              {' '}Corpus: {knowledge.corpus.documents} documents, {knowledge.corpus.chunks} sections.
            </span>
          )}
        </p>

        {knowledge.gaps.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-text-secondary">
                <tr>
                  <th className="pb-3 font-medium">Question</th>
                  <th className="pb-3 font-medium w-28">Employees</th>
                  <th className="pb-3 font-medium w-24">Times</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-subtle">
                {knowledge.gaps.slice(0, 8).map((gap, i) => (
                  <tr key={i}>
                    <td className="py-3 pr-4 text-text-main">{gap.question}</td>
                    <td className="py-3 text-text-secondary">{gap.distinct_employees}</td>
                    <td className="py-3 text-text-secondary">{gap.times_asked}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-text-secondary">
            No gaps recorded yet. They appear when the assistant cannot answer a
            policy question from your documents.
          </p>
        )}
      </div>

      <div className="card mb-8">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-2">
            <FileText className="text-text-secondary" />
            <h2 className="text-xl">Organizational Standard Documents</h2>
          </div>
          <button 
            onClick={handleAddStandardDoc}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <Plus size={14} /> Add Document
          </button>
        </div>
        <p className="text-sm text-text-secondary mb-6">
          These standard documents are automatically dispatched to employees <strong>only after</strong> they successfully clear Stage 1 (Document Verification).
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {standardDocs.map(doc => (
            <div key={doc.id} className="card-nested p-4 flex flex-col justify-between group">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-sm font-medium text-text-main pr-4">{doc.name}</h3>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEditStandardDoc(doc.id)} className="text-text-secondary hover:text-accent-gold transition-colors">
                      <Edit2 size={14} />
                    </button>
                    <button onClick={() => handleDeleteStandardDoc(doc.id)} className="text-text-secondary hover:text-status-error transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-text-secondary mb-4 line-clamp-2">{doc.description}</p>
              </div>
              <div className="mt-auto">
                <span className="text-[10px] uppercase font-bold tracking-wider text-accent-gold bg-accent-gold/10 px-2 py-1 rounded">
                  Triggers after Stage 1
                </span>
              </div>
            </div>
          ))}
          {standardDocs.length === 0 && (
            <div className="col-span-full text-center p-8 border-2 border-dashed border-subtle rounded-xl text-text-secondary text-sm">
              No standard documents added yet.
            </div>
          )}
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="p-6 border-b border-subtle">
          <h2 className="text-xl">Active Employees</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface-nested text-text-secondary">
              <tr>
                <th className="px-6 py-4 font-medium">Name & Role</th>
                <th className="px-6 py-4 font-medium">Organization</th>
                <th className="px-6 py-4 font-medium">Current Stage</th>
                <th className="px-6 py-4 font-medium">Progress</th>
                <th className="px-6 py-4 font-medium">Stall Risk</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {filteredEmployees.map(emp => {
                const org = getOrganization(emp.orgId);
                const stageNames = ["Pre-boarding", "Docs", "IT Setup", "KT", "Compliance", "Orientation"];
                return (
                  <tr 
                    key={emp.id} 
                    onClick={() => navigate(`/hr/employee/${emp.id}`)}
                    className="hover:bg-surface-nested transition-colors cursor-pointer group"
                  >
                    <td className="px-6 py-4">
                      <div className="font-medium text-text-main group-hover:text-accent-gold transition-colors">{emp.name}</div>
                      <div className="text-xs text-text-secondary">{emp.role}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                         <span className="w-5 h-5 rounded bg-accent-gold/10 text-accent-gold flex items-center justify-center text-[10px] font-bold">
                          {org.logo}
                        </span>
                        <span className="text-text-secondary">{org.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">
                      {stageNames[emp.stage]}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-16 h-1.5 bg-surface-main rounded-full overflow-hidden border border-subtle">
                          <div 
                            className={`h-full ${emp.status === 'blocked' ? 'bg-status-error' : 'bg-accent-gold'}`} 
                            style={{ width: `${emp.progress}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-text-secondary">{emp.progress}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {riskById[emp.id] ? (
                        <RiskBadge
                          band={riskById[emp.id].band}
                          probability={riskById[emp.id].probability}
                        />
                      ) : (
                        <span className="text-xs text-text-secondary">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusPill status={emp.status} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
