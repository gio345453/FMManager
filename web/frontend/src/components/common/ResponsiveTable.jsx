import React from 'react';
import { cn } from '@/lib/utils';

export default function ResponsiveTable({ children, caption, mobileContent, className }) {
  return <div className={cn('min-w-0', className)}>{mobileContent && <div className="block md:hidden">{mobileContent}</div>}<div className={cn(mobileContent && 'hidden md:block', 'w-full overflow-x-auto rounded-lg border border-border')}><table className="w-full min-w-[640px] text-sm">{caption && <caption className="sr-only">{caption}</caption>}{children}</table></div></div>;
}
