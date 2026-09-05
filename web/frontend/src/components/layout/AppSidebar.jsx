import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  GitCompareArrows,
  LayoutDashboard,
  RefreshCw,
  Settings,
  Shield,
  Star,
  Target,
  Trophy,
  Users,
  Zap,
  Gavel,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { SheetClose } from '@/components/ui/sheet';

export const navigationGroups = [
  {
    label: 'Analisi',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true, accent: 'cyan' },
      { to: '/players', label: 'Giocatori', icon: Users, accent: 'violet' },
      { to: '/teams', label: 'Squadre', icon: Shield, accent: 'emerald' },
      { to: '/tiratori', label: 'Tiratori', icon: Zap, accent: 'amber' },
      { to: '/compare', label: 'Confronto', icon: GitCompareArrows, accent: 'purple' },
    ],
  },
  {
    label: 'Rosa',
    items: [
      { to: '/rosa', label: 'Rosa', icon: Target, accent: 'emerald' },
      { to: '/asta', label: 'Asta', icon: Gavel, accent: 'amber' },
      { to: '/schiera-formazione', label: 'Schiera formazione', icon: Trophy, accent: 'cyan' },
      { to: '/goalkeeper-rotation', label: 'Rotazione Portieri', icon: RefreshCw, accent: 'blue' },
      { to: '/favorites', label: 'Preferiti', icon: Star, accent: 'pink' },
    ],
  },
  {
    label: 'Simulazione',
    items: [
      { to: '/simula-stagione', label: 'Simula Stagione', icon: CalendarRange, accent: 'violet' },
    ],
  },
  {
    label: 'Sistema',
    items: [
      { to: '/settings', label: 'Impostazioni', icon: Settings, accent: 'slate' },
    ],
  },
];

const NAV_ACCENTS = {
  cyan: {
    icon: 'text-cyan-300 bg-cyan-400/[0.08] border-cyan-400/15',
    active: 'border-cyan-400/20 bg-cyan-400/[0.09] text-cyan-200 shadow-[0_0_24px_rgba(34,211,238,0.08)]',
    hover: 'hover:border-cyan-400/15 hover:bg-cyan-400/[0.045]',
  },
  violet: {
    icon: 'text-violet-300 bg-violet-400/[0.08] border-violet-400/15',
    active: 'border-violet-400/20 bg-violet-400/[0.09] text-violet-200 shadow-[0_0_24px_rgba(167,139,250,0.08)]',
    hover: 'hover:border-violet-400/15 hover:bg-violet-400/[0.045]',
  },
  purple: {
    icon: 'text-purple-300 bg-purple-400/[0.08] border-purple-400/15',
    active: 'border-purple-400/20 bg-purple-400/[0.09] text-purple-200 shadow-[0_0_24px_rgba(192,132,252,0.08)]',
    hover: 'hover:border-purple-400/15 hover:bg-purple-400/[0.045]',
  },
  emerald: {
    icon: 'text-emerald-300 bg-emerald-400/[0.08] border-emerald-400/15',
    active: 'border-emerald-400/20 bg-emerald-400/[0.09] text-emerald-200 shadow-[0_0_24px_rgba(52,211,153,0.08)]',
    hover: 'hover:border-emerald-400/15 hover:bg-emerald-400/[0.045]',
  },
  amber: {
    icon: 'text-amber-300 bg-amber-400/[0.08] border-amber-400/15',
    active: 'border-amber-400/20 bg-amber-400/[0.09] text-amber-200 shadow-[0_0_24px_rgba(251,191,36,0.08)]',
    hover: 'hover:border-amber-400/15 hover:bg-amber-400/[0.045]',
  },
  blue: {
    icon: 'text-blue-300 bg-blue-400/[0.08] border-blue-400/15',
    active: 'border-blue-400/20 bg-blue-400/[0.09] text-blue-200 shadow-[0_0_24px_rgba(96,165,250,0.08)]',
    hover: 'hover:border-blue-400/15 hover:bg-blue-400/[0.045]',
  },
  pink: {
    icon: 'text-pink-300 bg-pink-400/[0.08] border-pink-400/15',
    active: 'border-pink-400/20 bg-pink-400/[0.09] text-pink-200 shadow-[0_0_24px_rgba(244,114,182,0.08)]',
    hover: 'hover:border-pink-400/15 hover:bg-pink-400/[0.045]',
  },
  slate: {
    icon: 'text-slate-300 bg-slate-400/[0.07] border-slate-400/15',
    active: 'border-slate-600/50 bg-slate-800/55 text-slate-100 shadow-[0_0_22px_rgba(148,163,184,0.05)]',
    hover: 'hover:border-slate-700/80 hover:bg-slate-800/35',
  },
};

function NavigationItem({ item, collapsed, mobile, onNavigate }) {
  const Icon = item.icon;
  const accent = NAV_ACCENTS[item.accent] || NAV_ACCENTS.cyan;

  const link = (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'app-nav-item !border no-underline visited:no-underline',
          'transition-all duration-200',
          collapsed && 'app-nav-item-collapsed',
          isActive
            ? `app-nav-item-active ${accent.active}`
            : `border-transparent ${accent.hover} text-slate-300`,
        )
      }
      title={collapsed ? item.label : undefined}
    >
      <span
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border transition-all duration-200',
          accent.icon,
        )}
      >
        <Icon className="app-nav-icon h-4 w-4" aria-hidden="true" />
      </span>
      <span
        className={cn(
          'app-nav-label !no-underline !text-slate-300',
          collapsed && 'sr-only',
          mobile && 'visited:!text-slate-300',
        )}
      >
        {item.label}
      </span>
    </NavLink>
  );

  return mobile ? <SheetClose asChild>{link}</SheetClose> : link;
}

export default function AppSidebar({ collapsed = false, mobile = false, onToggle, onNavigate }) {
  return (
    <div className={cn('app-sidebar-inner', collapsed && 'app-sidebar-inner-collapsed')}>
      <div className="app-brand">
        <div className="app-brand-mark overflow-hidden !border-cyan-400/25 !bg-cyan-400/[0.08] shadow-[0_0_24px_rgba(34,211,238,0.08)]" aria-hidden="true">
          <img
            src="/icon.png"
            alt="FantaManager"
            className="h-full w-full object-cover"
          />
        </div>
        {!collapsed && (
          <div className="app-brand-copy">
            <span className="app-brand-title">FantaManager</span>
            <span className="app-brand-subtitle"></span>
          </div>
        )}
      </div>

      <nav className="app-navigation" aria-label="Navigazione principale">
        {navigationGroups.map(group => (
          <div className="app-nav-group" key={group.label}>
            {!collapsed && <div className="app-nav-group-label">{group.label}</div>}
            <div className="app-nav-group-items">
              {group.items.map(item => (
                <NavigationItem
                  key={item.to}
                  item={item}
                  collapsed={collapsed}
                  mobile={mobile}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {!mobile && (
        <div className="app-sidebar-footer">
          <Button
            type="button"
            variant="ghost"
            size={collapsed ? 'icon' : 'default'}
            className={cn('app-sidebar-toggle border border-slate-700/70 bg-slate-950/40 text-slate-400 shadow-none transition-all hover:border-cyan-400/25 hover:bg-cyan-400/[0.05] hover:text-cyan-300', !collapsed && 'app-sidebar-toggle-expanded')}
            onClick={onToggle}
            aria-label={collapsed ? 'Espandi sidebar' : 'Comprimi sidebar'}
            title={collapsed ? 'Espandi sidebar' : 'Comprimi sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                <span>Comprimi</span>
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
