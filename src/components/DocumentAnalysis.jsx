import React from 'react';
import { clsx } from 'clsx';
import { Check, X, AlertTriangle, Info, Cpu } from 'lucide-react';

const VERDICT_STYLES = {
  auto_approved: {
    label: 'Auto-approved',
    box: 'bg-status-success/10 border-status-success/30',
    text: 'text-status-success',
  },
  auto_rejected: {
    label: 'Auto-rejected',
    box: 'bg-status-error/10 border-status-error/30',
    text: 'text-status-error',
  },
  needs_review: {
    label: 'Needs human review',
    box: 'bg-accent-gold/10 border-accent-gold/30',
    text: 'text-accent-gold',
  },
};

const CheckIcon = ({ check }) => {
  if (check.passed && check.severity !== 'warning') {
    return <Check size={14} className="text-status-success shrink-0 mt-0.5" />;
  }
  if (check.severity === 'blocking') {
    return <X size={14} className="text-status-error shrink-0 mt-0.5" />;
  }
  if (check.severity === 'warning') {
    return <AlertTriangle size={14} className="text-accent-gold shrink-0 mt-0.5" />;
  }
  return <Info size={14} className="text-text-secondary shrink-0 mt-0.5" />;
};

const formatType = (value) => (value ? value.replace(/_/g, ' ') : 'unknown');

export const DocumentAnalysis = ({ upload }) => {
  if (!upload) return null;

  const validations = upload.validations || {};
  const checks = validations.checks || [];
  const style = VERDICT_STYLES[upload.verdict] || VERDICT_STYLES.needs_review;
  const confidence = upload.predicted_confidence;
  const fields = upload.extracted_fields || {};
  const dates = fields.dates || {};
  const identifiers = fields.identifiers || {};

  return (
    <div className={clsx('rounded-lg border p-3 mt-3', style.box)}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Cpu size={14} className={style.text} />
          <span className={clsx('text-xs font-medium uppercase tracking-wider', style.text)}>
            {style.label}
          </span>
        </div>
        {upload.model_version && (
          <span className="text-[10px] text-text-secondary font-mono">{upload.model_version}</span>
        )}
      </div>

      {validations.reason && (
        <p className="text-xs text-text-main mb-3">{validations.reason}</p>
      )}

      {upload.predicted_type && (
        <div className="mb-3">
          <div className="flex justify-between text-[11px] text-text-secondary mb-1">
            <span>Classified as <strong className="text-text-main">{formatType(upload.predicted_type)}</strong></span>
            {confidence != null && <span>{(confidence * 100).toFixed(1)}%</span>}
          </div>
          {confidence != null && (
            <div className="w-full h-1 bg-surface-main rounded-full overflow-hidden border border-subtle">
              <div className="h-full bg-accent-gold" style={{ width: `${confidence * 100}%` }} />
            </div>
          )}
        </div>
      )}

      {checks.length > 0 && (
        <ul className="space-y-1.5 mb-3">
          {checks.map((check) => (
            <li key={check.check} className="flex items-start gap-2 text-[11px] text-text-secondary">
              <CheckIcon check={check} />
              <span>{check.message}</span>
            </li>
          ))}
        </ul>
      )}

      {(dates.expiry || dates.issue || Object.keys(identifiers).length > 0) && (
        <div className="pt-2 border-t border-subtle/50">
          <p className="text-[10px] uppercase tracking-wider text-text-secondary mb-1.5">
            Extracted fields
          </p>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
            {dates.issue && (
              <><span className="text-text-secondary">Issued</span><span className="text-text-main">{dates.issue}</span></>
            )}
            {dates.expiry && (
              <><span className="text-text-secondary">Expires</span><span className="text-text-main">{dates.expiry}</span></>
            )}
            {Object.entries(identifiers).map(([key, value]) => (
              <React.Fragment key={key}>
                <span className="text-text-secondary">{key.replace(/_/g, ' ')}</span>
                <span className="text-text-main font-mono truncate" title={value}>{value}</span>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {upload.hr_decision && (
        <p className="text-[10px] text-text-secondary mt-3 pt-2 border-t border-subtle/50">
          HR recorded: <strong className="text-text-main">{upload.hr_decision}</strong>
          {' — this decision is stored as a training label.'}
        </p>
      )}
    </div>
  );
};
