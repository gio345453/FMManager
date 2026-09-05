import React from 'react';
import { cn } from '@/lib/utils';

const Select = React.forwardRef(({ className, children, ...props }, ref) => (
  <div className="relative overflow-hidden rounded-md">
    <div className="absolute inset-x-0 top-0 z-10 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
    <select ref={ref} className={cn('flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50', className)} {...props}>
      {children}
    </select>
  </div>
));
Select.displayName = 'Select';

export { Select };
