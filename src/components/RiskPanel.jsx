import React from 'react';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

const BAND_STYLES = {
  high: { text: 'text-status-error', bar: 'bg-status-error', box: 'border-status-error/30 bg-status-error/5' },
  moderate: { text: 'text-accent-gold', bar: 'bg-accent-gold', box: 'border-accent-gold/30 bg-accent-gold/5' },
  low: { text: 'text-status-success', bar: 'bg-status-success', box: 'border-status-success/30 bg-status-success/5' },
};

export const RiskBadge = ({ band, probability }) => {
  const style = BAND_STYLES[band] || BAND_STYLES.low;
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 bg-surface-main rounded-full overflow-hidden border border-subtle">
        <div className={clsx('h-full', style.bar)} style={{ width: `${(probability || 0) * 100}%` }} />
      </div>
      <span className={clsx('text-xs font-medium', style.text)}>
        {Math.round((probability || 0) * 100)}%
      </span>
    </div>
  );
};

export const RiskPanel = ({ risk }) => {
  if (!risk) return null;

  if (!risk.available) {
    return (
      <div className="card-nested p-4 text-xs text-text-secondary">
        {risk.detail || 'Risk model unavailable.'}
      </div>
    );
  }

  const style = BAND_STYLES[risk.band] || BAND_STYLES.low;

  return (
    <div className={clsx('card-nested p-4 border', style.box)}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity size={16} className={style.text} />
          <h3 className="text-sm font-medium">Onboarding stall risk</h3>
        </div>
        {risk.model_version && (
          <span className="text-[10px] text-text-secondary font-mono">{risk.model_version}</span>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-1">
        <span className={clsx('text-3xl font-serif', style.text)}>
          {Math.round(risk.probability * 100)}%
        </span>
        <span className={clsx('text-xs uppercase tracking-wider', style.text)}>{risk.band}</span>
      </div>
      <div className="w-full h-1.5 bg-surface-main rounded-full overflow-hidden border border-subtle mb-4">
        <div className={clsx('h-full', style.bar)} style={{ width: `${risk.probability * 100}%` }} />
      </div>

      <p className="text-[10px] uppercase tracking-wider text-text-secondary mb-2">
        What is driving this
      </p>
      <ul className="space-y-2">
        {(risk.drivers || []).map((driver) => {
          const up = driver.contribution > 0;
          return (
            <li key={driver.feature} className="flex items-start gap-2 text-xs">
              {up
                ? <TrendingUp size={13} className="text-status-error shrink-0 mt-0.5" />
                : <TrendingDown size={13} className="text-status-success shrink-0 mt-0.5" />}
              <span className="text-text-secondary">
                <span className="text-text-main">{driver.label}</span>
                {driver.value != null && (
                  <span className="font-mono"> ({Number(driver.value).toLocaleString(undefined, { maximumFractionDigits: 1 })})</span>
                )}
                {up ? ' increases' : ' reduces'} risk
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
