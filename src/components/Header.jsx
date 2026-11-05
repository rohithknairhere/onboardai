import React, { useState } from 'react';
import { Sparkles, Info, LogOut, Sun, Moon, FlaskConical } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { HowItWorksModal } from './HowItWorksModal';
import { useNavigate } from 'react-router-dom';

export const Header = () => {
  const { currentUser, role, logout, getOrganization, theme, toggleTheme } = useAppContext();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const org = currentUser && role === 'employee' ? getOrganization(currentUser.orgId) : null;

  return (
    <>
      <header className="h-16 border-b border-subtle bg-base flex items-center justify-between px-6 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="text-accent-gold">
            <Sparkles size={24} />
          </div>
          <h1 className="text-xl m-0 leading-none tracking-wide">OnboardAI</h1>
        </div>
        
        <div className="flex items-center gap-6">
          {role === 'hr' && (
            <div className="flex items-center gap-4 text-sm">
              <button onClick={() => navigate('/hr/dashboard')}
                className="text-text-secondary hover:text-text-main transition-colors">Dashboard</button>
              <button onClick={() => navigate('/hr/evaluation')}
                className="flex items-center gap-1 text-accent-gold hover:opacity-80 transition-opacity">
                <FlaskConical size={16} /> Evaluation Lab
              </button>
            </div>
          )}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 text-text-secondary hover:text-text-main transition-colors text-sm"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 text-text-secondary hover:text-text-main transition-colors text-sm"
          >
            <Info size={16} />
            <span>How it works</span>
          </button>
          
          {currentUser && (
            <div className="flex items-center gap-4 border-l border-subtle pl-6">
              {org && (
                <div className="flex items-center gap-2 px-3 py-1 bg-surface-nested rounded-full border border-subtle">
                  <span className="w-5 h-5 rounded bg-accent-gold/20 text-accent-gold flex items-center justify-center text-xs font-bold font-sans">
                    {org.logo}
                  </span>
                  <span className="text-xs text-text-secondary">{org.name}</span>
                </div>
              )}
              
              <div className="text-sm font-medium">{currentUser.name}</div>
              
              <button 
                onClick={handleLogout}
                className="text-text-secondary hover:text-text-main transition-colors"
                title="Log out"
              >
                <LogOut size={18} />
              </button>
            </div>
          )}
        </div>
      </header>
      
      <HowItWorksModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
};
