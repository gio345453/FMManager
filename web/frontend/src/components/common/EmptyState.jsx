import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function EmptyState({ title = 'Nessun risultato', description, action, icon: Icon = Inbox, className }) {
  return <div className={cn('flex flex-col items-center justify-center rounded-lg border border-dashed border-border p-8 text-center', className)}><Icon className="h-8 w-8 text-muted-foreground" aria-hidden="true" /><h3 className="mt-3 text-base font-semibold text-foreground">{title}</h3>{description && <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>}{action && <Button className="mt-4" onClick={action.onClick} variant={action.variant}>{action.label}</Button>}</div>;
}
