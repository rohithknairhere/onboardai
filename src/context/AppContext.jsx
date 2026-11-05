import React, { createContext, useContext, useState, useEffect } from 'react';
import { stages as mockStages } from '../mockData';

const AppContext = createContext();

import { API_BASE_URL } from '../config';

export const AppProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null); // null means not logged in
  const [role, setRole] = useState(null); // 'employee' or 'hr'
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [allEmployees, setAllEmployees] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [stages, setStages] = useState(mockStages);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [standardDocs, setStandardDocs] = useState([
    { id: 1, name: "Employee Handbook", description: "General company policies and procedures", mandatory: true },
    { id: 2, name: "Safety Guidelines", description: "Workplace safety and emergency protocols", mandatory: true }
  ]);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees`);
      if (res.ok) {
        const data = await res.json();
        setAllEmployees(data);
      }
    } catch (e) {
      console.error("Failed to fetch employees", e);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/organizations`);
      if (res.ok) {
        const data = await res.json();
        setOrganizations(data);
      }
    } catch (e) {
      console.error("Failed to fetch organizations", e);
    }
  };

  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      await Promise.all([fetchEmployees(), fetchOrganizations()]);
      setLoading(false);
    };
    initData();
  }, []);

  // currentUser is a snapshot taken at login, so without this it never picks up
  // task completions, uploads or stage changes fetched into allEmployees.
  useEffect(() => {
    setCurrentUser(prev => {
      if (!prev || prev.id === 'admin') return prev;
      const fresh = allEmployees.find(e => e.id === prev.id);
      return fresh || prev;
    });
  }, [allEmployees]);

  const login = (roleType, entityId = null) => {
    // Pick up anything that changed since the page loaded (uploads, HR
    // decisions, a demo reset); currentUser follows allEmployees once it lands.
    fetchEmployees();
    setRole(roleType);
    if (roleType === 'employee') {
      const emp = allEmployees.find(e => e.id === (entityId || 'emp_1'));
      setCurrentUser(emp);
    } else {
      setCurrentUser({ name: 'Admin User', id: 'admin', orgId: entityId || 'all' });
    }
  };

  const logout = () => {
    setCurrentUser(null);
    setRole(null);
    setIsChatOpen(false);
  };

  const toggleChat = () => setIsChatOpen(!isChatOpen);

  const getOrganization = (orgId) => organizations.find(o => o.id === orgId);

  const updateEmployeeTask = async (empId, taskId, completed) => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees/${empId}/task/${taskId}?completed=${completed}`, {
        method: 'PUT'
      });
      if (res.ok) {
        await fetchEmployees();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const hrOverrideStep = async (empId, stageIndex) => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees/${empId}/stage?stage=${stageIndex}`, {
        method: 'PUT'
      });
      if (res.ok) {
        await fetchEmployees();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const hrUpdateDoc = async (empId, docId, status, reason = "") => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees/${empId}/document/${docId}?status=${status}&reason=${encodeURIComponent(reason)}`, {
        method: 'PUT'
      });
      if (res.ok) {
        await fetchEmployees();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const uploadDocument = async (empId, file, requiredDocId = null) => {
    const form = new FormData();
    form.append('file', file);
    if (requiredDocId) form.append('required_doc_id', requiredDocId);

    const res = await fetch(`${API_BASE_URL}/employees/${empId}/documents/upload`, {
      method: 'POST',
      body: form
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Upload failed (${res.status})`);
    }

    const data = await res.json();
    await fetchEmployees();
    return data;
  };

  const fetchRiskOverview = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/risk/overview`);
      return res.ok ? await res.json() : { employees: [] };
    } catch (e) {
      console.error('Failed to fetch risk overview', e);
      return { employees: [] };
    }
  };

  const fetchEmployeeRisk = async (empId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees/${empId}/risk`);
      return res.ok ? await res.json() : { available: false };
    } catch (e) {
      console.error('Failed to fetch risk', e);
      return { available: false };
    }
  };

  const fetchKnowledgeGaps = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/knowledge/gaps`);
      return res.ok ? await res.json() : { gaps: [], corpus: null };
    } catch (e) {
      console.error('Failed to fetch knowledge gaps', e);
      return { gaps: [], corpus: null };
    }
  };

  const fetchEmployeeUploads = async (empId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees/${empId}/uploads`);
      return res.ok ? await res.json() : [];
    } catch (e) {
      console.error('Failed to fetch uploads', e);
      return [];
    }
  };

  const recordUploadDecision = async (uploadId, decision, reason = '') => {
    const res = await fetch(`${API_BASE_URL}/uploads/${uploadId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, reason })
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || 'Failed to record decision');
    }
    const data = await res.json();
    await fetchEmployees();
    return data;
  };

  const handleAddStandardDoc = () => {
    const name = prompt("Enter standard document name:");
    if (!name) return;
    const desc = prompt("Enter short description:");
    setStandardDocs([...standardDocs, { id: Date.now(), name, description: desc || "", mandatory: true }]);
  };

  const handleEditStandardDoc = (id) => {
    const doc = standardDocs.find(d => d.id === id);
    if (!doc) return;
    const newName = prompt("Edit name:", doc.name);
    if (!newName) return;
    const newDesc = prompt("Edit description:", doc.description);
    setStandardDocs(standardDocs.map(d => d.id === id ? { ...d, name: newName, description: newDesc || "" } : d));
  };

  const handleDeleteStandardDoc = (id) => {
    if (confirm("Are you sure you want to delete this standard document?")) {
      setStandardDocs(standardDocs.filter(d => d.id !== id));
    }
  };

  return (
    <AppContext.Provider value={{
      currentUser,
      role,
      isChatOpen,
      allEmployees,
      organizations,
      stages,
      loading,
      theme,
      standardDocs,
      toggleTheme,
      login,
      logout,
      toggleChat,
      setIsChatOpen,
      getOrganization,
      updateEmployeeTask,
      hrOverrideStep,
      hrUpdateDoc,
      uploadDocument,
      fetchEmployeeUploads,
      recordUploadDecision,
      fetchRiskOverview,
      fetchEmployeeRisk,
      fetchKnowledgeGaps,
      handleAddStandardDoc,
      handleEditStandardDoc,
      handleDeleteStandardDoc
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);
