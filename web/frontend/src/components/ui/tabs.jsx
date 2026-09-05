import React from 'react';
import { cn } from '@/lib/utils';

const TabsContext = React.createContext(null);

function Tabs({ value, defaultValue, onValueChange, className, children }) {
  const [internalValue, setInternalValue] = React.useState(defaultValue);
  const activeValue = value === undefined ? internalValue : value;
  const handleChange = nextValue => {
    if (value === undefined) setInternalValue(nextValue);
    onValueChange?.(nextValue);
  };

  return <TabsContext.Provider value={{ activeValue, onValueChange: handleChange }}><div className={cn('w-full', className)}>{children}</div></TabsContext.Provider>;
}

const TabsList = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} role="tablist" className={cn('inline-flex h-11 max-w-full items-center justify-start gap-1 overflow-x-auto rounded-md bg-muted p-1', className)} {...props} />
));
TabsList.displayName = 'TabsList';

const TabsTrigger = React.forwardRef(({ className, value, children, ...props }, ref) => {
  const context = React.useContext(TabsContext);
  const isActive = context?.activeValue === value;
  return <button ref={ref} type="button" role="tab" aria-selected={isActive} tabIndex={isActive ? 0 : -1} onClick={() => context?.onValueChange(value)} className={cn('relative overflow-hidden inline-flex min-h-9 shrink-0 items-center justify-center rounded-sm px-3 text-sm font-medium text-muted-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-gradient-to-r before:from-sky-400/70 before:via-violet-400/45 before:to-transparent before:opacity-0 before:transition-opacity before:content-[""]', isActive && 'bg-card text-foreground shadow-sm before:opacity-100', className)} {...props}>{children}</button>;
});
TabsTrigger.displayName = 'TabsTrigger';

const TabsContent = React.forwardRef(({ className, value, children, ...props }, ref) => {
  const context = React.useContext(TabsContext);
  if (context?.activeValue !== value) return null;
  return <div ref={ref} role="tabpanel" tabIndex={0} className={cn('mt-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring', className)} {...props}>{children}</div>;
});
TabsContent.displayName = 'TabsContent';

export { Tabs, TabsList, TabsTrigger, TabsContent };
