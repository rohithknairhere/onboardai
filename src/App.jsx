import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { EmployeeDashboard } from './pages/employee/Dashboard';
import { EmployeeChat } from './pages/employee/Chat';
import { HrDashboard } from './pages/hr/Dashboard';
import { HrEmployeeDetail } from './pages/hr/EmployeeDetail';
import { EvaluationLab } from './pages/hr/EvaluationLab';

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/employee/dashboard" element={<EmployeeDashboard />} />
            <Route path="/employee/chat" element={<EmployeeChat />} />
            <Route path="/hr/dashboard" element={<HrDashboard />} />
            <Route path="/hr/employee/:id" element={<HrEmployeeDetail />} />
            <Route path="/hr/evaluation" element={<EvaluationLab />} />
          </Route>
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
