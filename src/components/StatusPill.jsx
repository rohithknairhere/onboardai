import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const StatusPill = ({ status, className }) => {
  let bgColor = '';
  let textColor = '';
  let dotColor = '';
  let label = '';

  switch (status) {
    case 'verified':
    case 'completed':
      bgColor = 'bg-status-success/10';
      textColor = 'text-status-success';
      dotColor = 'bg-status-success';
      label = status === 'verified' ? 'Verified' : 'Completed';
      break;
    case 'rejected':
    case 'blocked':
      bgColor = 'bg-status-error/10';
      textColor = 'text-status-error';
      dotColor = 'bg-status-error';
      label = status === 'rejected' ? 'Rejected' : 'Blocked';
      break;
    case 'in_progress':
    case 'pending':
    default:
      bgColor = 'bg-accent-gold/10';
      textColor = 'text-accent-gold';
      dotColor = 'bg-accent-gold';
      label = status === 'in_progress' ? 'In Progress' : 'Pending';
      break;
  }

  return (
    <div className={twMerge(clsx("status-pill", bgColor, textColor, className))}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", dotColor)}></span>
      {label}
    </div>
  );
};
