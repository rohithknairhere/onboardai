import React from 'react';
import { clsx } from 'clsx';
import { Check } from 'lucide-react';
import { stages } from '../mockData';

export const StageTracker = ({ currentStage }) => {
  return (
    <div className="w-full flex items-center justify-between relative mt-4 mb-8">
      <div className="absolute left-0 right-0 top-4 h-[1px] bg-subtle -z-10" />
      {stages.map((stage, index) => {
        const isCompleted = index < currentStage;
        const isCurrent = index === currentStage;
        
        return (
          <div key={stage} className="flex flex-col items-center gap-2 relative z-10 w-24">
            <div className={clsx(
              "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300",
              isCompleted ? "bg-accent-gold text-base" : 
              isCurrent ? "bg-surface-main border-2 border-accent-gold text-accent-gold" : 
              "bg-surface-main border border-subtle text-text-secondary"
            )}>
              {isCompleted ? <Check size={16} strokeWidth={3} /> : <span className="text-sm font-medium">{index + 1}</span>}
            </div>
            <span className={clsx(
              "text-xs font-sans text-center transition-colors",
              isCompleted || isCurrent ? "text-text-main font-medium" : "text-text-secondary"
            )}>
              {stage}
            </span>
          </div>
        );
      })}
    </div>
  );
};
