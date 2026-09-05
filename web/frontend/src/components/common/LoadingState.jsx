import React from 'react';
import { Loader2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export default function LoadingState({ message = 'Caricamento in corso…', rows = 3, className }) {
  return <div role="status" aria-live="polite" className={cn('space-y-3 p-6', className)}><div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />{message}</div>{Array.from({ length: rows }, (_, index) => <Skeleton key={index} className="h-10 w-full" />)}<span className="sr-only">{message}</span></div>;
}
