import React from 'react';
import { Menu, Settings } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetDescription, SheetTitle } from '@/components/ui/sheet';
import AppSidebar from '@/components/layout/AppSidebar';

const routeLabels = {
  '/': { title: 'Dashboard', subtitle: 'Panoramica generale di FMManager' },
  '/players': { title: 'Giocatori', subtitle: 'Database completo giocatori' },
  '/teams': { title: 'Squadre', subtitle: 'Analisi squadre Serie A' },
  '/tiratori': { title: 'Tiratori', subtitle: 'Statistiche tiri e conclusioni' },
  '/compare': { title: 'Confronto', subtitle: 'Confronta giocatori' },
  '/rosa': { title: 'Rosa', subtitle: 'Crea e ottimizza la tua rosa' },
  '/asta': { title: 'Asta', subtitle: "Assistente decisionale per l'asta" },
  '/goalkeeper-rotation': { title: 'Rotazione Portieri', subtitle: 'Analizza rotazione portieri' },
  '/simula-stagione': { title: 'Simula Stagione', subtitle: 'Simulazione Monte Carlo' },
  '/favorites': { title: 'Preferiti', subtitle: 'Giocatori salvati' },
  '/settings': { title: 'Impostazioni', subtitle: 'Configurazione sistema' },
};

function getPageInfo(pathname) {
  if (routeLabels[pathname]) return routeLabels[pathname];
  if (pathname.startsWith('/players/')) return { title: 'Dettaglio Giocatore', subtitle: 'Statistiche e analisi' };
  if (pathname.startsWith('/teams/')) return { title: 'Dettaglio Squadra', subtitle: 'Rosa e statistiche' };
  return { title: 'FMManager', subtitle: 'Football analytics' };
}

export default function AppShell({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const pageInfo = getPageInfo(location.pathname);

  React.useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <aside className={collapsed ? 'app-sidebar app-sidebar-collapsed' : 'app-sidebar'}>
        <AppSidebar collapsed={collapsed} onToggle={() => setCollapsed(value => !value)} />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="app-mobile-sheet p-0 [&_a]:no-underline [&_a]:visited:no-underline [&>button]:h-9 [&>button]:w-9 [&>button]:rounded-xl [&>button]:border [&>button]:border-slate-700/70 [&>button]:bg-slate-950/40 [&>button]:text-slate-400 [&>button]:opacity-100 [&>button]:shadow-none [&>button]:transition-all [&>button]:hover:border-cyan-400/25 [&>button]:hover:bg-cyan-400/[0.05] [&>button]:hover:text-cyan-300 [&>button]:focus-visible:ring-1 [&>button]:focus-visible:ring-cyan-400/30 [&>button_svg]:h-4 [&>button_svg]:w-4">
          <SheetTitle className="sr-only">Navigazione FMManager</SheetTitle>
          <SheetDescription className="sr-only">Apri una sezione dell'applicazione</SheetDescription>
          <AppSidebar mobile onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="app-shell-main">
        <header className="app-header">
          <div className="app-header-left">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="app-mobile-menu-button md:hidden h-9 w-9 border border-slate-700/70 bg-slate-950/40 text-slate-400 shadow-none transition-all hover:border-cyan-400/25 hover:bg-cyan-400/[0.05] hover:text-cyan-300 focus-visible:ring-1 focus-visible:ring-cyan-400/30"
              onClick={() => setMobileOpen(true)}
              aria-label="Apri navigazione"
              title="Apri navigazione"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-400/15 bg-slate-400/[0.07] text-slate-300 transition-all duration-200">
                <Menu className="h-4 w-4" aria-hidden="true" />
              </span>
            </Button>
            <div>
              <h1 className="app-header-title">{pageInfo.title}</h1>
              <div className="app-header-eyebrow">{pageInfo.subtitle}</div>
            </div>
          </div>
          <div className="app-header-right">
            <div className="app-header-status">
              <span className="app-header-status-indicator"></span>
              Operativo
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-9 w-9 border border-slate-700/70 bg-slate-950/40 text-slate-400 shadow-none transition-all hover:border-slate-600/80 hover:bg-slate-800/55 hover:text-slate-100"
              onClick={() => navigate('/settings')}
              aria-label="Apri impostazioni"
              title="Impostazioni"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-400/15 bg-slate-400/[0.07] text-slate-300 transition-all duration-200">
                <Settings className="h-4 w-4" aria-hidden="true" />
              </span>
            </Button>
          </div>
        </header>
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
