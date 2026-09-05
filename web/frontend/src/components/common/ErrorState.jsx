import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function ErrorState({ title = 'Si è verificato un errore', message = 'Riprova tra poco.', onRetry, retryLabel = 'Riprova', className }) {
  return <Alert variant="destructive" className={cn('flex flex-wrap items-start gap-3', className)}><AlertCircle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" /><div className="min-w-0 flex-1"><AlertTitle>{title}</AlertTitle><AlertDescription>{message}</AlertDescription></div>{onRetry && <Button type="button" variant="outline" size="sm" onClick={onRetry}>{retryLabel}</Button>}</Alert>;
}
