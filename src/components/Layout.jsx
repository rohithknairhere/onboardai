import React from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { useAppContext } from '../context/AppContext';
import { MessageSquare } from 'lucide-react';

export const Layout = () => {
  const { currentUser, role } = useAppContext();
  const location = useLocation();
  const navigate = useNavigate();
  
  if (!currentUser && location.pathname !== '/login') {
    return <Navigate to="/login" replace />;
  }

  // Floating chat button only for employees and not if already on the chat full page
  const showChatFloat = role === 'employee' && location.pathname !== '/employee/chat';

  return (
    <div className="min-h-screen bg-base text-text-main flex flex-col font-sans">
      <Header />
      <main className="flex-1 w-full max-w-6xl mx-auto p-6 relative">
        <Outlet />
      </main>
      
      {showChatFloat && (
        <button 
          onClick={() => navigate('/employee/chat')}
          className="fixed bottom-8 right-8 w-14 h-14 bg-accent-gold rounded-full flex items-center justify-center text-base shadow-soft hover:bg-opacity-90 active:scale-95 transition-all z-40 group"
          title="Open Assistant"
        >
          <MessageSquare size={24} className="text-base group-hover:scale-110 transition-transform" />
          <span className="absolute top-0 right-0 w-3 h-3 bg-status-success rounded-full border-2 border-base"></span>
        </button>
      )}
    </div>
  );
};
