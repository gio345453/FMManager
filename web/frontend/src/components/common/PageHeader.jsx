import React from 'react';
import { cn } from '@/lib/utils';

export default function PageHeader({ title, description, actions, eyebrow, className }) {
  return (
    <header className={cn('flex flex-col gap-4 border-b border-border px-4 py-6 sm:flex-row sm:items-end sm:justify-between sm:px-6 lg:px-8', className)}>
      <div className="min-w-0">
        {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</p>}
        <h2 className="text-2xl font-bold tracking-tight text-foreground">{title}</h2>
        {description && <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
