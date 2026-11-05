import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { User, Shield, ArrowLeft } from 'lucide-react';

export const Login = () => {
  const { login, allEmployees } = useAppContext();
  const navigate = useNavigate();
  
  const [loginView, setLoginView] = useState('selection'); // 'selection', 'employee', 'hr'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRoleSelect = (role) => {
    if (role === 'employee' && allEmployees.length === 0) {
      alert("Error: Cannot find employees. Is the backend server running?");
      return;
    }
    setLoginView(role);
    setError('');
    setUsername('');
    setPassword('');
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (loginView === 'employee') {
      if (username === 'employee 1' && password === '@1') {
        login('employee', 'emp_1');
        navigate('/employee/dashboard');
      } else if (username === 'employee 2' && password === '@2') {
        login('employee', 'emp_2');
        navigate('/employee/dashboard');
      } else {
        setError('Invalid employee credentials.');
      }
    } else if (loginView === 'hr') {
      if (username === 'hr1' && password === '@hr1') {
        login('hr', 'org_1');
        navigate('/hr/dashboard');
      } else if (username === 'hr2' && password === '@hr2') {
        login('hr', 'org_2');
        navigate('/hr/dashboard');
      } else {
        setError('Invalid HR credentials.');
      }
    }
  };

  if (loginView !== 'selection') {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center">
        <div className="w-full max-w-md card">
          <button 
            onClick={() => setLoginView('selection')}
            className="flex items-center gap-2 text-text-secondary hover:text-text-main mb-6 transition-colors"
          >
            <ArrowLeft size={16} /> Back
          </button>
          
          <h2 className="text-2xl mb-6 font-serif">
            {loginView === 'employee' ? 'Employee Login' : 'HR / Admin Login'}
          </h2>

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-1">Username</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-surface-nested border border-subtle rounded-lg px-4 py-2 text-text-main focus:outline-none focus:border-accent-gold transition-colors"
                placeholder={loginView === 'employee' ? 'e.g. employee 1' : 'e.g. hr1'}
              />
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-1">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface-nested border border-subtle rounded-lg px-4 py-2 text-text-main focus:outline-none focus:border-accent-gold transition-colors"
                placeholder="Enter password"
              />
            </div>
            
            {error && (
              <p className="text-status-error text-sm">{error}</p>
            )}

            <button type="submit" className="btn-primary w-full mt-4 py-3">
              Sign In
            </button>
          </form>
          
          <div className="mt-6 p-4 bg-surface-nested rounded-lg border border-subtle">
            <p className="text-xs text-text-secondary mb-2 font-medium">Demo Credentials:</p>
            {loginView === 'employee' ? (
              <ul className="text-xs text-text-secondary space-y-1">
                <li>Username: <strong className="text-text-main">employee 1</strong> | Pass: <strong className="text-text-main">@1</strong> (Shreya)</li>
                <li>Username: <strong className="text-text-main">employee 2</strong> | Pass: <strong className="text-text-main">@2</strong> (Adithya)</li>
              </ul>
            ) : (
              <ul className="text-xs text-text-secondary space-y-1">
                <li>Username: <strong className="text-text-main">hr1</strong> | Pass: <strong className="text-text-main">@hr1</strong> (Nimbus Labs)</li>
                <li>Username: <strong className="text-text-main">hr2</strong> | Pass: <strong className="text-text-main">@hr2</strong> (Veltrix Corp)</li>
              </ul>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center">
      <div className="text-center mb-12">
        <h2 className="text-3xl mb-4 text-text-secondary">Welcome to</h2>
        <h1 className="text-5xl tracking-wide mb-2 flex items-center justify-center gap-3">
          OnboardAI <span className="w-2 h-2 rounded-full bg-accent-gold mt-4"></span>
        </h1>
        <p className="text-text-secondary max-w-md mx-auto mt-6">
          Intelligent, adaptive onboarding powered by specialized ML agents.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
        <button 
          onClick={() => handleRoleSelect('employee')}
          className="card group cursor-pointer border-transparent hover:border-accent-gold/50 transition-all text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-accent-gold/5 rounded-bl-full -z-10 group-hover:bg-accent-gold/10 transition-colors"></div>
          <div className="w-12 h-12 rounded-lg bg-surface-nested flex items-center justify-center mb-6 text-text-secondary group-hover:text-accent-gold transition-colors">
            <User size={24} />
          </div>
          <h3 className="text-xl mb-2 font-serif">I'm a new hire</h3>
          <p className="text-sm text-text-secondary">
            Log in to experience your personalized onboarding flow, AI guidance, and tasks.
          </p>
        </button>

        <button 
          onClick={() => handleRoleSelect('hr')}
          className="card group cursor-pointer border-transparent hover:border-accent-gold/50 transition-all text-left relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-accent-gold/5 rounded-bl-full -z-10 group-hover:bg-accent-gold/10 transition-colors"></div>
          <div className="w-12 h-12 rounded-lg bg-surface-nested flex items-center justify-center mb-6 text-text-secondary group-hover:text-accent-gold transition-colors">
            <Shield size={24} />
          </div>
          <h3 className="text-xl mb-2 font-serif">I'm HR / Admin</h3>
          <p className="text-sm text-text-secondary">
            Log in to the HR dashboard to view cross-organization metrics and manage exceptions.
          </p>
        </button>
      </div>
    </div>
  );
};
