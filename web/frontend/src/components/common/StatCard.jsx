import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatCard({
  icon: Icon,
  label,
  value,
  subValue,
  delta,
  deltaLabel,
  iconColor = 'var(--fm-primary)',
  iconBg = 'var(--fm-primary-muted)',
  className = ''
}) {
  const showDelta = delta !== undefined && delta !== null;
  const isPositive = delta > 0;

  return (
    <div className={`stat-card ${className}`}>
      <div className="stat-card-header">
        <div
          className="stat-card-icon"
          style={{
            backgroundColor: iconBg,
            color: iconColor
          }}
        >
          <Icon className="h-5 w-5" />
        </div>
        {showDelta && (
          <div className={`stat-card-delta ${isPositive ? 'stat-card-delta-positive' : 'stat-card-delta-negative'}`}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            <span>{isPositive ? '+' : ''}{delta}</span>
          </div>
        )}
      </div>

      <div className="stat-card-content">
        <div className="stat-card-value">{value}</div>
        {subValue && <div className="stat-card-subvalue">{subValue}</div>}
        <div className="stat-card-label">{label}</div>
        {deltaLabel && <div className="stat-card-delta-label">{deltaLabel}</div>}
      </div>
    </div>
  );
}
