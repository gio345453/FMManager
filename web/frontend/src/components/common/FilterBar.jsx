import React from 'react';
import { cn } from '@/lib/utils';

export default function FilterBar({ children, title = 'Filtri', actions, className }) {
  return <section aria-label={title} className={cn('rounded-lg border border-border bg-card p-4', className)}><div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div className="grid min-w-0 flex-1 grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">{children}</div>{actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}</div></section>;
}
