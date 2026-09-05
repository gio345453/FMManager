import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'relative overflow-hidden inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-gradient-to-r before:from-sky-400/70 before:via-violet-400/45 before:to-transparent before:content-[""]',
  {
    variants: {
      variant: {
        default: 'bg-sky-400 text-slate-950 hover:bg-sky-400/90 px-4',
        secondary: 'border border-border bg-secondary px-4 text-secondary-foreground hover:bg-accent',
        ghost: 'px-3 text-muted-foreground hover:bg-accent hover:text-foreground before:hidden',
        outline: 'border border-border bg-transparent px-4 text-foreground hover:bg-accent',
      },
      size: {
        default: 'h-11',
        sm: 'h-9 min-h-9 px-3',
        icon: 'h-11 w-11 min-w-11 p-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Component = asChild ? Slot : 'button';

    return (
      <Component
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
