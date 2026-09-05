import React from 'react';
import { cn } from '@/lib/utils';

const Separator = React.forwardRef(({ className, orientation = 'horizontal', ...props }, ref) => (
  <div ref={ref} role="separator" aria-orientation={orientation} className={cn('shrink-0 bg-border', orientation === 'vertical' ? 'h-full w-px' : 'h-px w-full', className)} {...props} />
));
Separator.displayName = 'Separator';

export { Separator };
