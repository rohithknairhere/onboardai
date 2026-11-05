import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';
import { API_BASE_URL } from '../../config';
import { Send, Bot, ArrowLeft, Paperclip, X } from 'lucide-react';

export const EmployeeChat = () => {
  const { currentUser, getOrganization } = useAppContext();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [routingState, setRoutingState] = useState(null); // 'routing', 'Document Agent', 'IT Agent', etc.
  const messagesEndRef = useRef(null);

  const org = currentUser ? getOrganization(currentUser.orgId) : null;

  useEffect(() => {
    if (currentUser && messages.length === 0) {
      setMessages([
        {
          id: 1,
          sender: 'assistant',
          agent: 'Orchestrator Agent',
          text: `Hi ${currentUser.name.split(' ')[0]}! I'm your OnboardAI Assistant. I see you're joining ${org?.name || 'us'} as a ${currentUser.role}. I've tailored your onboarding flow based on your role requirements. How can I help you today?`
        }
      ]);
    }
  }, [currentUser, org, messages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, routingState]);

  if (!currentUser) return null;

  const handleSend = async (text = input) => {
    if (!text.trim()) return;
    
    const newMsg = { id: Date.now(), sender: 'user', text };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setIsTyping(true);
    setRoutingState('routing');

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, emp_id: currentUser?.id })
      });
      
      const data = await response.json();

      setRoutingState(data.agent || 'Orchestrator Agent');

      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        agent: data.agent || 'Orchestrator Agent',
        text: data.response,
        intent: data.intent,
        intentConfidence: data.intent_confidence,
        sentiment: data.sentiment,
        escalated: data.escalated,
        transferredFrom: data.transferred_from,
        redacted: data.redacted || []
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        agent: 'System',
        text: 'Error connecting to the agentic backend.'
      }]);
    } finally {
      setIsTyping(false);
      setRoutingState(null);
    }
  };

  const quickReplies = [
    "Upload my documents",
    "When is my KT session?",
    "What's my IT access status?",
    "I have a policy question"
  ];

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col bg-surface-main rounded-xl border border-subtle overflow-hidden shadow-soft animate-in slide-in-from-bottom-8 duration-500">
      <div className="h-16 border-b border-subtle flex items-center justify-between px-6 bg-surface-nested">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/employee/dashboard')} className="text-text-secondary hover:text-text-main transition-colors mr-2 hidden md:block">
            <ArrowLeft size={20} />
          </button>
          <div className="w-8 h-8 rounded-full bg-accent-gold/20 text-accent-gold flex items-center justify-center">
            <Bot size={18} />
          </div>
          <div>
            <h2 className="font-medium text-sm">OnboardAI Assistant</h2>
            <p className="text-xs text-status-success flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success"></span>
              Online
            </p>
          </div>
        </div>
        <button onClick={() => navigate('/employee/dashboard')} className="text-text-secondary hover:text-text-main transition-colors md:hidden">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-surface-nested">
        {messages.map(msg => (
          <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
            {msg.sender === 'assistant' && (
              <div className="flex items-center gap-2 mb-1 pl-1 flex-wrap">
                {msg.transferredFrom && (
                  <span className="text-[10px] text-text-secondary" title={`Routed to ${msg.transferredFrom}, which transferred it on`}>
                    {msg.transferredFrom} &rarr;
                  </span>
                )}
                <span className="text-[10px] uppercase tracking-wider text-accent-gold font-medium bg-accent-gold/10 px-2 py-0.5 rounded">
                  {msg.agent}
                </span>
                {msg.intent && (
                  <span className="text-[10px] text-text-secondary" title="Predicted by the intent classifier">
                    {msg.intent.replace(/_/g, ' ')}
                    {msg.intentConfidence != null && ` · ${Math.round(msg.intentConfidence * 100)}%`}
                  </span>
                )}
                {msg.escalated && (
                  <span className="text-[10px] uppercase tracking-wider text-status-error font-medium bg-status-error/10 px-2 py-0.5 rounded">
                    Escalated to HR
                  </span>
                )}
                {msg.redacted?.length > 0 && (
                  <span
                    className="text-[10px] text-text-secondary"
                    title={`Removed before sending to the model: ${msg.redacted.join(', ')}`}
                  >
                    {msg.redacted.length} identifier{msg.redacted.length > 1 ? 's' : ''} redacted
                  </span>
                )}
              </div>
            )}
            <div className={`max-w-[80%] md:max-w-[70%] p-3 rounded-2xl text-sm ${
              msg.sender === 'user' 
                ? 'bg-accent-gold text-base rounded-tr-sm' 
                : 'bg-surface-nested border border-subtle rounded-tl-sm'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}

        {routingState && (
          <div className="flex flex-col items-start">
             <div className="flex items-center gap-2 mb-1 pl-1">
                {routingState === 'routing' ? (
                  <span className="text-[10px] uppercase tracking-wider text-text-secondary font-medium bg-surface-nested px-2 py-0.5 rounded border border-subtle animate-pulse">
                    Routing to specialized agent...
                  </span>
                ) : (
                  <span className="text-[10px] uppercase tracking-wider text-accent-gold font-medium bg-accent-gold/10 px-2 py-0.5 rounded animate-pulse">
                    {routingState} analyzing...
                  </span>
                )}
              </div>
              {isTyping && routingState !== 'routing' && (
                <div className="bg-surface-nested border border-subtle p-3 rounded-2xl rounded-tl-sm w-16 flex justify-center gap-1">
                  <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></span>
                  <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></span>
                </div>
              )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-surface-nested border-t border-subtle">
        {messages.length === 1 && !isTyping && (
          <div className="flex flex-wrap gap-2 mb-4">
            {quickReplies.map((reply, i) => (
              <button 
                key={i}
                onClick={() => handleSend(reply)}
                className="text-xs bg-surface-main border border-subtle text-text-secondary hover:text-accent-gold hover:border-accent-gold/50 px-3 py-1.5 rounded-full transition-colors"
              >
                {reply}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2 bg-surface-main border border-subtle rounded-xl p-1 pr-2">
          <button className="p-2 text-text-secondary hover:text-accent-gold transition-colors">
            <Paperclip size={18} />
          </button>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-text-main placeholder-text-secondary"
          />
          <button 
            onClick={() => handleSend()}
            disabled={!input.trim()}
            className="w-8 h-8 flex items-center justify-center bg-accent-gold text-base rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-opacity-90 transition-all"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
