import React from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function QuickAction({ label, description, icon: Icon, onClick, href, disabled = false, loading = false, className }) {
  const content = <><span className="flex min-w-0 flex-1 items-center gap-3 text-left">{Icon && <span className="rounded-md bg-primary/10 p-2 text-primary"><Icon className="h-5 w-5" aria-hidden="true" /></span>}<span className="min-w-0"><span className="block truncate font-semibold">{label}</span>{description && <span className="mt-1 block truncate text-xs font-normal text-muted-foreground">{description}</span>}</span></span>{loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <ArrowRight className="h-4 w-4 text-muted-foreground" aria-hidden="true" />}</>;

  return <Button type="button" variant="outline" className={cn('h-auto min-h-16 w-full justify-between py-3', className)} onClick={onClick} disabled={disabled || loading} asChild={Boolean(href)}>{href ? <a href={href}>{content}</a> : content}</Button>;
}
