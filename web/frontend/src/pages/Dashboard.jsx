import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CalendarDays,
  Database,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  GitCompareArrows,
  Heart,
  Search,
  Settings,
  Shield,
  Target,
  Upload,
  Zap,
  Users,
} from 'lucide-react';
import { utilityApi } from '../api/client';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

function DashboardDialog({ title, description, children, onClose, tone = 'default' }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-3 backdrop-blur-sm sm:p-5"
      role="presentation"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        className={[
          'flex max-h-[92vh] w-full max-w-2xl flex-col gap-5 overflow-y-auto rounded-2xl border',
          'bg-[#0F172A] p-4 shadow-2xl shadow-black/40 sm:p-6',
          tone === 'danger'
            ? 'border-red-500/40'
            : 'border-slate-700/80',
        ].join(' ')}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dashboard-dialog-title"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2
              id="dashboard-dialog-title"
              className="text-lg font-semibold tracking-tight text-slate-50 sm:text-xl"
            >
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-sm leading-6 text-slate-400">
                {description}
              </p>
            )}
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Chiudi finestra"
            className="shrink-0 rounded-xl border border-slate-700/70 bg-slate-900/50 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            ×
          </Button>
        </div>

        {children}
      </div>
    </div>
  );
}

function ResultAlert({ result, successTitle, errorTitle, detail }) {
  if (!result) return null;

  return (
    <Alert
      variant={result.success ? 'success' : 'destructive'}
      className="border-slate-700/80 bg-slate-900/70"
    >
      {result.success ? (
        <Database className="h-5 w-5 shrink-0" aria-hidden="true" />
      ) : (
        <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
      )}

      <div className="min-w-0 flex-1">
        <AlertTitle>{result.success ? successTitle : errorTitle}</AlertTitle>
        <AlertDescription>{result.message}</AlertDescription>
        {detail && <p className="mt-2 text-xs opacity-90">{detail}</p>}
      </div>
    </Alert>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
  subtitle,
  accent = 'cyan',
  footer,
}) {
  const accents = {
    cyan: {
      icon: 'bg-cyan-400/10 text-cyan-300 ring-cyan-400/15',
      value: 'text-slate-50',
    },
    violet: {
      icon: 'bg-violet-400/10 text-violet-300 ring-violet-400/15',
      value: 'text-slate-50',
    },
    green: {
      icon: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/15',
      value: 'text-emerald-300',
    },
    yellow: {
      icon: 'bg-amber-400/10 text-amber-300 ring-amber-400/15',
      value: 'text-slate-50',
    },
    red: {
      icon: 'bg-rose-400/10 text-rose-300 ring-rose-400/15',
      value: 'text-slate-50',
    },
  };

  const palette = accents[accent] || accents.cyan;

  return (
    <Card className="group overflow-hidden border-slate-800/90 bg-[#111827]/90 shadow-none transition-colors hover:border-slate-700">
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className={`flex h-9 w-9 items-center justify-center rounded-xl ring-1 ${palette.icon}`}>
            <Icon className="h-4.5 w-4.5" />
          </div>
          {footer && (
            <span className="text-[11px] font-medium text-emerald-300">
              {footer}
            </span>
          )}
        </div>

        <div className="mt-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">
            {label}
          </p>
          <p className={`mt-1 truncate text-2xl font-semibold tracking-tight sm:text-[28px] ${palette.value}`}>
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function QuickAction({ icon: Icon, title, description, onClick, tone = 'cyan' }) {
  const tones = {
    cyan: 'bg-cyan-400/10 text-cyan-300',
    violet: 'bg-violet-400/10 text-violet-300',
    green: 'bg-emerald-400/10 text-emerald-300',
    yellow: 'bg-amber-400/10 text-amber-300',
    blue: 'bg-blue-400/10 text-blue-300',
    purple: 'bg-fuchsia-400/10 text-fuchsia-300',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex min-h-[88px] items-center gap-3 rounded-xl border border-slate-800/90 bg-[#111827]/75 p-3.5 text-left transition-all hover:border-slate-700 hover:bg-[#162033] focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
    >
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tones[tone] || tones.cyan}`}>
        <Icon className="h-5 w-5" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold text-slate-100">{title}</div>
        <div className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">
          {description}
        </div>
      </div>

      <span
        aria-hidden="true"
        className="text-lg text-slate-600 transition-all group-hover:translate-x-0.5 group-hover:text-slate-300"
      >
        →
      </span>
    </button>
  );
}

function SectionHeading({ eyebrow, title, action }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-400/80">
            {eyebrow}
          </p>
        )}
        <h2 className="mt-1 text-base font-semibold tracking-tight text-slate-100 sm:text-lg">
          {title}
        </h2>
      </div>
      {action}
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [showSeasonUpdateModal, setShowSeasonUpdateModal] = useState(false);
  const [showCalendarioModal, setShowCalendarioModal] = useState(false);
  const [calendarioUploading, setCalendarioUploading] = useState(false);
  const [calendarioResult, setCalendarioResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const navigate = useNavigate();

  const isSeasonUpdatePeriod = () => {
    const now = new Date();
    const year = now.getFullYear();
    const startDate = new Date(year, 6, 15);
    const endDate = new Date(year, 7, 18);
    return now >= startDate && now <= endDate;
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [healthRes, favoritesRes] = await Promise.all([
        utilityApi.health(),
        utilityApi.getFavorites(),
      ]);

      setStats({
        totalPlayers: healthRes.data.players_count,
        favorites: favoritesRes.data.length,
        dataLoaded: healthRes.data.data_loaded,
      });

      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('Il file deve essere in formato .xlsx o .xls');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/update-listone', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Errore durante l'aggiornamento");
      }

      setUploadResult({
        success: true,
        message: result.message,
        playersCount: result.players_count,
      });

      await loadDashboard();
    } catch (err) {
      setUploadResult({ success: false, message: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleCalendarioUpload = async (file) => {
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setCalendarioResult({
        success: false,
        message: 'Il file deve essere in formato .csv',
      });
      return;
    }

    setCalendarioUploading(true);
    setCalendarioResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(
        '/api/upload-calendario-csv',
        {
          method: 'POST',
          body: formData,
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Errore durante il caricamento');
      }

      setCalendarioResult({
        success: true,
        message: result.message,
        totalMatches: result.total_matches,
      });
    } catch (err) {
      setCalendarioResult({ success: false, message: err.message });
    } finally {
      setCalendarioUploading(false);
    }
  };

  const handleCalendarioDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleCalendarioUpload(file);
  };

  const closeModal = () => {
    setShowUpdateModal(false);
    setUploadResult(null);
  };

  if (loading) {
    return (
      <LoadingState
        message="Caricamento dashboard..."
        className="min-h-[60vh]"
      />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Dashboard non disponibile"
        message={error}
        onRetry={loadDashboard}
        className="min-h-[60vh]"
      />
    );
  }

  const quickActions = [
    {
      title: 'Cerca giocatore',
      description: 'Trova e filtra i giocatori',
      icon: Search,
      onClick: () => navigate('/players'),
      tone: 'cyan',
    },
    {
      title: 'Confronta',
      description: 'Confronta 2-3 giocatori',
      icon: GitCompareArrows,
      onClick: () => navigate('/compare'),
      tone: 'violet',
    },
    {
      title: 'Rosa',
      description: 'Crea e ottimizza la tua rosa',
      icon: Target,
      onClick: () => navigate('/rosa'),
      tone: 'green',
    },
    {
      title: 'Rigoristi',
      description: 'Gerarchie rigori e calci piazzati',
      icon: Zap,
      onClick: () => navigate('/tiratori'),
      tone: 'yellow',
    },
    {
      title: 'Squadre',
      description: 'Analizza le squadre di Serie A',
      icon: Shield,
      onClick: () => navigate('/teams'),
      tone: 'blue',
    },
    {
      title: 'Calendario',
      description: 'Carica il calendario di Serie A',
      icon: CalendarDays,
      onClick: () => setShowCalendarioModal(true),
      tone: 'purple',
    },
  ];

  return (
    <div className="min-h-full bg-[#0B0E14] text-slate-50">
      <main className="mx-auto w-full max-w-[1640px] px-4 py-5 sm:px-6 sm:py-6 xl:px-8">
        <section className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <KpiCard
              icon={Users}
              label="Giocatori totali"
              value={stats?.totalPlayers || 0}
              subtitle="Database completo"
              accent="cyan"
            />
            <KpiCard
              icon={Heart}
              label="Preferiti"
              value={stats?.favorites || 0}
              subtitle="Giocatori salvati"
              accent="red"
            />
            <KpiCard
              icon={Shield}
              label="Squadre"
              value="20"
              subtitle="Serie A"
              accent="blue"
            />
            <KpiCard
              icon={Database}
              label="Database"
              value={stats?.dataLoaded ? 'Operativo' : 'Non caricato'}
              subtitle={stats?.dataLoaded ? 'Dati disponibili' : 'Carica il listone'}
              accent="green"
            />
            <KpiCard
              icon={CalendarDays}
              label="Stagione"
              value="2026/27"
              subtitle="Giornata corrente"
              accent="violet"
            />
          </div>

          <section className="space-y-3">
            <SectionHeading eyebrow="Navigazione" title="Azioni rapide" />
            <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
              {quickActions.map((action) => (
                <QuickAction key={action.title} {...action} />
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <SectionHeading eyebrow="Database" title="Gestione dati" />
            <div className="grid gap-3 lg:grid-cols-2">
              <Card className="border-slate-800/90 bg-[#111827]/75 shadow-none">
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300 ring-1 ring-cyan-400/10">
                      <Upload className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="text-sm font-semibold text-slate-100 sm:text-base">
                        Aggiorna listone
                      </CardTitle>
                      <CardDescription className="mt-1 text-xs leading-5 text-slate-500">
                        Carica il file Excel delle quotazioni.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    type="button"
                    onClick={() => setShowUpdateModal(true)}
                    className="h-10 w-full rounded-xl bg-cyan-400 font-semibold text-slate-950 hover:bg-cyan-300"
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                    Carica file Excel
                  </Button>
                </CardContent>
              </Card>

              {isSeasonUpdatePeriod() && (
                <Card className="border-amber-400/25 bg-amber-400/[0.06] shadow-none">
                  <CardHeader className="pb-3">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/10">
                        <AlertTriangle className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <CardTitle className="text-sm font-semibold text-slate-100 sm:text-base">
                          Aggiornamento stagione
                        </CardTitle>
                        <CardDescription className="mt-1 text-xs leading-5 text-amber-100/60">
                          Procedura speciale disponibile nel periodo previsto.
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setShowSeasonUpdateModal(true)}
                      className="h-10 w-full rounded-xl border-amber-400/30 bg-transparent text-amber-200 hover:bg-amber-400/10 hover:text-amber-100"
                    >
                      <Settings className="h-4 w-4" />
                      Apri procedura
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </section>

          <section className="grid gap-3 lg:grid-cols-3">
            <Card className="border-slate-800/90 bg-[#111827]/65 shadow-none lg:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-slate-100">
                  Stato applicazione
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Riepilogo rapido del sistema e del database.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-800/80 bg-slate-950/20 p-3">
                  <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">
                    Database
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        stats?.dataLoaded ? 'bg-emerald-400' : 'bg-rose-400'
                      }`}
                    />
                    <span className="text-sm font-medium text-slate-100">
                      {stats?.dataLoaded ? 'Operativo' : 'Non caricato'}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800/80 bg-slate-950/20 p-3">
                  <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">
                    Giocatori
                  </p>
                  <p className="mt-2 text-lg font-semibold text-slate-100">
                    {stats?.totalPlayers || 0}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-800/80 bg-slate-950/20 p-3">
                  <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">
                    Preferiti
                  </p>
                  <p className="mt-2 text-lg font-semibold text-slate-100">
                    {stats?.favorites || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-800/90 bg-[#111827]/65 shadow-none">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-slate-100">
                  Stagione corrente
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Configurazione attiva.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border border-violet-400/15 bg-violet-400/[0.06] p-3.5">
                  <div className="flex items-center gap-2 text-violet-300">
                    <CalendarDays className="h-4 w-4" />
                    <span className="text-[11px] font-semibold uppercase tracking-[0.12em]">
                      Serie A
                    </span>
                  </div>
                  <p className="mt-3 text-xl font-semibold tracking-tight text-slate-50">
                    2026/27
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Dati della stagione corrente
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>
        </section>
      </main>

      {showUpdateModal && (
        <DashboardDialog
          title="Aggiorna listone"
          description="Carica il file Excel delle quotazioni Fantacalcio.it (.xlsx o .xls)."
          onClose={closeModal}
        >
          <div className="relative rounded-2xl border border-dashed border-slate-700 bg-slate-950/30 p-5 transition-colors hover:border-cyan-400/50 hover:bg-cyan-400/[0.03] sm:p-8">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              disabled={uploading}
              id="file-upload"
              className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
            />
            <label
              htmlFor="file-upload"
              className="pointer-events-none flex cursor-pointer flex-col items-center justify-center gap-3 text-center"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-300 ring-1 ring-cyan-400/10">
                <FileSpreadsheet className="h-7 w-7" aria-hidden="true" />
              </div>
              <span className="text-sm font-semibold text-slate-100">
                {uploading
                  ? 'Caricamento in corso...'
                  : 'Clicca per selezionare il file'}
              </span>
              <span className="text-xs text-slate-500">
                Formati supportati: .xlsx e .xls
              </span>
            </label>
          </div>

          {uploadResult ? (
            <>
              <ResultAlert
                result={uploadResult}
                successTitle="Aggiornamento completato"
                errorTitle="Aggiornamento non riuscito"
                detail={
                  uploadResult.success && uploadResult.playersCount
                    ? `Giocatori totali: ${uploadResult.playersCount}`
                    : undefined
                }
              />
              {uploadResult.success && (
                <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.06] px-4 py-3">
                  <p className="text-sm font-semibold text-amber-200">
                    ⚠️ Riavvio richiesto
                  </p>
                  <p className="mt-1 text-xs leading-5 text-amber-100/70">
                    Il listone è stato aggiornato correttamente. Riavvia
                    l&apos;applicazione per rendere effettive tutte le modifiche.
                  </p>
                </div>
              )}
              <Button
                type="button"
                className="h-10 w-full rounded-xl bg-cyan-400 font-semibold text-slate-950 hover:bg-cyan-300"
                onClick={closeModal}
              >
                Chiudi
              </Button>
            </>
          ) : (
            <Button
              type="button"
              variant="outline"
              className="h-10 w-full rounded-xl border-slate-700 bg-transparent"
              onClick={closeModal}
              disabled={uploading}
            >
              Annulla
            </Button>
          )}
        </DashboardDialog>
      )}

      {showSeasonUpdateModal && (
        <DashboardDialog
          title="Attenzione: aggiornamento fine stagione"
          description="Questa procedura è riservata al cambio di stagione."
          onClose={() => setShowSeasonUpdateModal(false)}
          tone="danger"
        >
          <Alert
            variant="destructive"
            className="border-red-500/30 bg-red-500/[0.06]"
          >
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <AlertTitle>Usare solo nel periodo corretto</AlertTitle>
              <AlertDescription>
                <p>
                  Durante il campionato potrebbe sovrascrivere dati della stagione
                  corrente, resettare classifiche e statistiche o corrompere i
                  calcoli dell&apos;applicazione.
                </p>
                <ul className="mt-3 list-disc space-y-1 pl-5">
                  <li>Dopo la fine della stagione (38 giornate)</li>
                  <li>Prima dell&apos;inizio della prima giornata</li>
                  <li>Nel periodo: 15 luglio - 18 agosto</li>
                </ul>
              </AlertDescription>
            </div>
          </Alert>

          <p className="text-xs leading-5 text-slate-500">
            Leggi attentamente la guida nella cartella{' '}
            <strong className="text-slate-300">
              Aggiornamento_Fine_Stagione
            </strong>{' '}
            prima di procedere.
          </p>

          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowSeasonUpdateModal(false)}
              className="rounded-xl border-slate-700 bg-transparent"
            >
              Annulla
            </Button>

            <Button
              type="button"
              variant="destructive"
              onClick={async () => {
                try {
                  const response = await fetch(
                    '/api/open-season-update-folder',
                    {
                      method: 'POST',
                    }
                  );

                  if (response.ok) setShowSeasonUpdateModal(false);
                } catch (err) {
                  console.error('Error opening folder:', err);
                }
              }}
              className="rounded-xl"
            >
              <FolderOpen className="h-4 w-4" aria-hidden="true" />
              Apri cartella
            </Button>
          </div>
        </DashboardDialog>
      )}

      {showCalendarioModal && (
        <DashboardDialog
          title="Carica calendario Serie A"
          description="Importa un file CSV scaricato da FBref."
          onClose={() => {
            setShowCalendarioModal(false);
            setCalendarioResult(null);
            setIsDragging(false);
          }}
        >
          <Card className="border-slate-800/90 bg-slate-950/20 shadow-none">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <FileText className="h-4 w-4 text-cyan-300" aria-hidden="true" />
                Come scaricare il CSV
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Segui questi passaggi per preparare il file.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="list-decimal space-y-2 pl-5 text-xs leading-5 text-slate-400">
                <li>
                  Apri{' '}
                  <a
                    href="https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-300 hover:text-cyan-200 hover:underline"
                  >
                    FBref Serie A{' '}
                    <ExternalLink
                      className="inline h-3.5 w-3.5"
                      aria-hidden="true"
                    />
                  </a>
                  .
                </li>
                <li>Scorri sotto la tabella e apri “Share & Export”.</li>
                <li>Seleziona “Get table as CSV (for Excel)”.</li>
                <li>Copia il testo in un file e salvalo come calendario.csv.</li>
                <li>Trascina il file nella zona sottostante.</li>
              </ol>
            </CardContent>
          </Card>

          <div
            onDrop={handleCalendarioDrop}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setIsDragging(false);
            }}
            className={[
              'relative rounded-2xl border border-dashed p-5 transition-colors sm:p-8',
              isDragging
                ? 'border-cyan-400 bg-cyan-400/[0.05]'
                : 'border-slate-700 bg-slate-950/30 hover:border-slate-600',
            ].join(' ')}
          >
            <input
              type="file"
              accept=".csv"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) handleCalendarioUpload(file);
              }}
              disabled={calendarioUploading}
              id="calendario-upload"
              className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
            />

            <label
              htmlFor="calendario-upload"
              className="pointer-events-none flex cursor-pointer flex-col items-center gap-3 text-center"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-400/10 text-violet-300 ring-1 ring-violet-400/10">
                <CalendarDays className="h-7 w-7" aria-hidden="true" />
              </div>

              <span className="text-sm font-semibold text-slate-100">
                {calendarioUploading
                  ? 'Caricamento in corso...'
                  : isDragging
                    ? 'Rilascia il file qui'
                    : 'Trascina qui il file CSV'}
              </span>

              <span className="text-xs text-slate-500">
                oppure clicca per selezionare · solo .csv
              </span>
            </label>
          </div>

          {calendarioResult ? (
            <>
              <ResultAlert
                result={calendarioResult}
                successTitle="Calendario caricato"
                errorTitle="Caricamento non riuscito"
                detail={
                  calendarioResult.success && calendarioResult.totalMatches
                    ? `Partite totali: ${calendarioResult.totalMatches}`
                    : undefined
                }
              />
              <Button
                type="button"
                className="h-10 w-full rounded-xl bg-cyan-400 font-semibold text-slate-950 hover:bg-cyan-300"
                onClick={() => {
                  setShowCalendarioModal(false);
                  setCalendarioResult(null);
                  setIsDragging(false);
                }}
              >
                Chiudi
              </Button>
            </>
          ) : (
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCalendarioModal(false);
                  setCalendarioResult(null);
                  setIsDragging(false);
                }}
                disabled={calendarioUploading}
                className="rounded-xl border-slate-700 bg-transparent"
              >
                Annulla
              </Button>

              <Button
                type="button"
                onClick={() =>
                  window.open(
                    'https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures',
                    '_blank'
                  )
                }
                className="rounded-xl bg-cyan-400 font-semibold text-slate-950 hover:bg-cyan-300"
              >
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                Apri FBref
              </Button>
            </div>
          )}
        </DashboardDialog>
      )}
    </div>
  );
}

export default Dashboard;
