import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export default function SimulationProgress({ value = 0, scenario, totalScenarios, label = 'Simulazione in corso', className }) {
  const progress = Math.min(100, Math.max(0, Number(value) || 0));
  const complete = progress >= 100;
  return <div role="status" aria-live="polite" className={cn('rounded-lg border border-border bg-card p-4', className)}><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2 text-sm font-medium text-foreground">{complete && <CheckCircle2 className="h-4 w-4 text-emerald-400" aria-hidden="true" />}{label}</div><span className="text-sm font-semibold text-primary">{Math.round(progress)}%</span></div><Progress value={progress} className="mt-3" />{scenario !== undefined && <p className="mt-2 text-xs text-muted-foreground">Scenario {scenario}{totalScenarios ? ` di ${totalScenarios}` : ''}</p>}</div>;
}
