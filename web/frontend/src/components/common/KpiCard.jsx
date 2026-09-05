import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const toneClasses = {
  default: 'text-foreground',
  primary: 'text-primary',
  success: 'text-emerald-300',
  warning: 'text-amber-300',
  danger: 'text-red-300'
};

export default function KpiCard({ label, value, detail, trend, icon: Icon, tone = 'default', className }) {
  return (
    <Card className={cn('min-w-0', className)}>
      <CardContent className="flex items-start justify-between gap-4 p-5">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">{label}</p>
          <p className={cn('mt-3 truncate text-3xl font-bold tracking-tight', toneClasses[tone] || toneClasses.default)}>{value}</p>
          {(detail || trend) && <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">{detail && <span>{detail}</span>}{trend && <span className="inline-flex items-center gap-1 text-emerald-300"><ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />{trend}</span>}</div>}
        </div>
        {Icon && <div className="rounded-md bg-primary/10 p-2.5 text-primary"><Icon className="h-5 w-5" aria-hidden="true" /></div>}
      </CardContent>
    </Card>
  );
}
