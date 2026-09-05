import React from 'react';
import { cn } from '@/lib/utils';

const Range = React.forwardRef(({ className, ...props }, ref) => (
  <div className="relative w-full">
    <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent rounded-full" />
    <input
      ref={ref}
      type="range"
      className={cn('w-full accent-sky-400', className)}
      {...props}
    />
  </div>
));
Range.displayName = 'Range';

export { Range };
