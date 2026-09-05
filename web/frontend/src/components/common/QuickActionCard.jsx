import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function QuickActionCard({
  icon: Icon,
  title,
  description,
  onClick,
  iconColor = 'var(--fm-primary)',
  iconBg = 'var(--fm-primary-muted)',
  className = ''
}) {
  return (
    <button
      type="button"
      className={`quick-action-card ${className}`}
      onClick={onClick}
    >
      <div
        className="quick-action-icon"
        style={{
          backgroundColor: iconBg,
          color: iconColor
        }}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="quick-action-content">
        <div className="quick-action-title">{title}</div>
        <div className="quick-action-description">{description}</div>
      </div>
      <ArrowRight className="quick-action-arrow h-4 w-4" />
    </button>
  );
}
