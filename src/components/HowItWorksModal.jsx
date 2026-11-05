import React from 'react';
import { X, Bot, Cpu, Network } from 'lucide-react';

export const HowItWorksModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-base/80 backdrop-blur-sm p-4">
      <div className="card w-full max-w-lg relative animate-in fade-in zoom-in duration-200">
        <button 
          onClick={onClose}
          className="absolute right-4 top-4 text-text-secondary hover:text-text-main transition-colors"
        >
          <X size={20} />
        </button>
        
        <h2 className="text-2xl mb-2">How OnboardAI Works</h2>
        <p className="text-text-secondary text-sm mb-6">
          Unlike static checklists, OnboardAI uses a specialized multi-agent architecture to adapt to each organization.
        </p>
        
        <div className="space-y-4">
          <div className="card-nested flex gap-4 items-start">
            <div className="mt-1 p-2 bg-accent-gold/10 rounded-lg text-accent-gold">
              <Network size={20} />
            </div>
            <div>
              <h3 className="text-base font-medium mb-1 font-sans">Orchestrator Agent</h3>
              <p className="text-sm text-text-secondary">
                Routes intents to specialized sub-agents based on context. It knows if you need HR policy help or IT access.
              </p>
            </div>
          </div>
          
          <div className="card-nested flex gap-4 items-start">
            <div className="mt-1 p-2 bg-status-success/10 rounded-lg text-status-success">
              <Bot size={20} />
            </div>
            <div>
              <h3 className="text-base font-medium mb-1 font-sans">Specialized Sub-Agents</h3>
              <p className="text-sm text-text-secondary">
                Document Agent handles verifications; IT Agent provisions access; KT Agent coordinates handovers.
              </p>
            </div>
          </div>
          
          <div className="card-nested flex gap-4 items-start">
            <div className="mt-1 p-2 bg-text-main/10 rounded-lg text-text-main">
              <Cpu size={20} />
            </div>
            <div>
              <h3 className="text-base font-medium mb-1 font-sans">ML-Driven Personalization</h3>
              <p className="text-sm text-text-secondary">
                Learns from industry data and historical onboarding flows to tailor required documents, training, and KT plans per employee profile and org.
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="btn-primary">
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
