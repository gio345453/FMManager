import React from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors', {
  variants: {
    variant: {
      default: 'border-transparent bg-primary text-primary-foreground',
      secondary: 'border-transparent bg-secondary text-secondary-foreground',
      outline: 'border-border text-foreground',
      success: 'border-transparent bg-emerald-500/15 text-emerald-300',
      warning: 'border-transparent bg-amber-500/15 text-amber-300',
      destructive: 'border-transparent bg-destructive/15 text-red-300'
    }
  },
  defaultVariants: { variant: 'default' }
});

const Badge = React.forwardRef(({ className, variant, ...props }, ref) => (
  <span ref={ref} className={cn(badgeVariants({ variant }), className)} {...props} />
));
Badge.displayName = 'Badge';

export { Badge, badgeVariants };
