import React, { useState, useEffect, useRef } from 'react';
import {
  AlertCircle,
  BarChart3,
  Calendar,
  Check,
  ChevronLeft,
  ChevronRight,
  FileJson,
  Play,
  RotateCcw,
  Settings2,
  TrendingUp,
  Upload,
  Users,
  WalletCards,
} from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import KpiCard from '../components/common/KpiCard';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

function ProgressBarAnimationStyle() {
  return (
    <style>{`
      @keyframes progressShimmer {
        0% { transform: translateX(-120%); }
        100% { transform: translateX(120%); }
      }
    `}</style>
  );
}

function SimulaStagione() {
  const [step, setStep] = useState(1);
  const [rosa, setRosa] = useState(null);
  const [calendario, setCalendario] = useState(null);
  const [formation, setFormation] = useState('3-4-3');
  const [myTeam, setMyTeam] = useState('');
  const [nSimulations, setNSimulations] = useState(100);
  const [settings, setSettings] = useState({
    mvpBonusEnabled: false,
    cleanSheetEnabled: false,
    defenseModifierEnabled: true,
  });

  const [simulating, setSimulating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [savedRosas, setSavedRosas] = useState([]);
  const [selectedRosaName, setSelectedRosaName] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);

  const progressIntervalRef = useRef(null);

  useEffect(() => {
    const initializeData = () => {
      console.log('[SimulaStagione] Initializing...');
      loadSavedRosas();
      loadSavedCalendar();
      loadSessionState();
      console.log('[SimulaStagione] Initialization complete');
      setIsInitialized(true);
    };
    initializeData();
  }, []);

  useEffect(() => {
    if (simulating) {
      progressIntervalRef.current = setInterval(async () => {
        try {
          const response = await fetch('/api/simulation-progress');
          const data = await response.json();

          if (data.is_running) {
            setProgress(Number(data.progress) || 0);
            setProgressText(
              data.message ||
              `Scenario ${data.current_scenario || 1}: ${data.completed || 0}/${data.total || 0} simulazioni`
            );
          } else if (data.error) {
            setError(data.error || 'Errore simulazione');
            setSimulating(false);
            clearInterval(progressIntervalRef.current);
          } else if (Number(data.progress) >= 100) {
            setProgress(100);
            setProgressText('Simulazione completata!');
            clearInterval(progressIntervalRef.current);
            await fetchSimulationResult();
          }

        } catch (err) {
          console.error('Error fetching progress:', err);
        }
      }, 500);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    }
  }, [simulating]);

  useEffect(() => {
    if (isInitialized) {
      saveSessionState();
    }
  }, [
    step,
    rosa,
    formation,
    myTeam,
    nSimulations,
    settings,
    simulating,
    progress,
    progressText,
    result,
    error,
    selectedRosaName,
    isInitialized,
  ]);

  const loadSavedRosas = () => {
    try {
      const rosas = JSON.parse(localStorage.getItem('completa_rosa_library') || '[]');
      setSavedRosas(rosas);
    } catch (err) {
      console.error('Error loading saved rosas:', err);
    }
  };

  const loadSavedCalendar = () => {
    try {
      const savedCal = localStorage.getItem('simula_stagione_calendar');
      if (savedCal) {
        setCalendario(JSON.parse(savedCal));
      }
    } catch (err) {
      console.error('Error loading saved calendar:', err);
    }
  };

  const loadSessionState = () => {
    try {
      const saved = sessionStorage.getItem('simula_stagione_session');
      if (saved) {
        const data = JSON.parse(saved);
        if (data.step) setStep(data.step);
        if (data.rosa) setRosa(data.rosa);
        if (data.formation) setFormation(data.formation);
        if (data.myTeam) setMyTeam(data.myTeam);
        if (data.nSimulations) setNSimulations(data.nSimulations);
        if (data.settings) setSettings(data.settings);
        if (data.result) setResult(data.result);
        if (data.error) setError(data.error);
        if (data.selectedRosaName) setSelectedRosaName(data.selectedRosaName);

        if (data.simulating) {
          setSimulating(true);
          setProgress(data.progress || 0);
          setProgressText(data.progressText || 'Ripresa simulazione...');
        }
      }
    } catch (err) {
      console.error('Error loading session state:', err);
    }
  };

  const saveSessionState = () => {
    try {
      sessionStorage.setItem(
        'simula_stagione_session',
        JSON.stringify({
          step,
          rosa,
          formation,
          myTeam,
          nSimulations,
          settings,
          simulating,
          progress,
          progressText,
          result,
          error,
          selectedRosaName,
        })
      );
    } catch (err) {
      console.error('Error saving session state:', err);
    }
  };

  const fetchSimulationResult = async () => {
    try {
      const response = await fetch('/api/simulation-result');
      if (response.ok) {
        const data = await response.json();
        setResult(data);
        setSimulating(false);
        setProgress(100);
        setProgressText('Completato!');
        saveSessionState();
      }
    } catch (err) {
      console.error('Error fetching result:', err);
    }
  };

  const handleDeleteCalendar = () => {
    if (confirm('Eliminare il calendario caricato?')) {
      localStorage.removeItem('simula_stagione_calendar');
      setCalendario(null);
      saveSessionState();
    }
  };

  const handleUploadRosa = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        setRosa(parsed);
        setSelectedRosaName('');
      } catch (err) {
        alert('File JSON non valido');
      }
    };
    reader.readAsText(file);
  };

  const handleSelectSavedRosa = (rosaData) => {
    const players = rosaData.roster
      .filter((slot) => slot.player !== null)
      .map((slot) => ({
        id: slot.player.id,
        nome: slot.player.nome,
        squadra: slot.player.squadra,
        ruolo: slot.player.ruolo,
        fm_weighted: slot.player.fm_weighted,
        price_credits: slot.customPrice || slot.player.price_credits,
      }));

    setRosa({ players, name: rosaData.name });
    setSelectedRosaName(rosaData.name);
  };

  const handleUploadCalendar = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload-calendar', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Errore upload calendario');
      }

      const data = await response.json();
      setCalendario(data);
      localStorage.setItem('simula_stagione_calendar', JSON.stringify(data));
      alert(`Calendario caricato: ${data.teams.length} squadre, ${data.total_matchdays} giornate`);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleStartSimulation = async () => {
    if (!rosa || !calendario || !myTeam.trim()) {
      alert('Completa tutti i campi prima di avviare');
      return;
    }

    try {
      setSimulating(true);
      setProgress(0);
      setProgressText('Avvio simulazione...');
      setError(null);

      let rosaPayload;
      if (rosa.players && Array.isArray(rosa.players)) {
        rosaPayload = rosa.players.map((p) => ({ player: p }));
      } else if (Array.isArray(rosa)) {
        rosaPayload = rosa.map((p) => (p.player ? p : { player: p }));
      } else {
        throw new Error('Formato rosa non valido');
      }

      const response = await fetch('/api/simulate-season', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rosa: rosaPayload,
          formation,
          my_team: myTeam,
          settings,
          n_simulations: nSimulations,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Errore avvio simulazione');
      }

      const data = await response.json();
      setResult(data);
      setSimulating(false);
      setProgress(100);
      setProgressText('Completato!');
    } catch (err) {
      setError(err.message);
      setSimulating(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    }
  };

  const handleReset = () => {
    setStep(1);
    setFormation('3-4-3');
    setMyTeam('');
    setNSimulations(100);
    setSimulating(false);
    setProgress(0);
    setProgressText('');
    setResult(null);
    setError(null);
    setSelectedRosaName('');
    sessionStorage.removeItem('simula_stagione_session');
  };

  if (simulating) {
    return (
      <>
        <ProgressBarAnimationStyle />
        <div className="min-h-full bg-[#0B0E14]">
        <div className="mx-auto w-full max-w-[1100px] px-4 py-4 sm:px-6 sm:py-8">
          <PageHeader
            title="Simula Stagione"
            description="Simulazione Monte Carlo in corso..."
          />

          <main className="mt-5">
            <Card className="overflow-hidden border border-slate-800/90 bg-[#0F172A] shadow-[0_14px_40px_rgba(0,0,0,0.22)]">
              <div className="h-1 bg-gradient-to-r from-sky-400 via-violet-400 to-sky-400" />
              <CardContent className="px-5 py-8 sm:px-10 sm:py-12">
                <div className="mx-auto max-w-2xl text-center">
                  <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-sky-400/20 bg-sky-400/[0.07] shadow-[0_0_35px_rgba(56,189,248,0.10)]">
                    <div className="absolute inset-2 rounded-xl border border-sky-400/15" />
                    <div className="absolute inset-[7px] rounded-full border border-violet-400/15 border-t-sky-300 animate-[spin_1.6s_linear_infinite]" />
                    <div className="absolute inset-[13px] rounded-full border border-sky-300/10 border-b-violet-300 animate-[spin_1.1s_linear_infinite_reverse]" />
                    <div className="h-3 w-3 rounded-full bg-gradient-to-br from-sky-300 to-violet-400 shadow-[0_0_18px_rgba(56,189,248,0.45)] animate-pulse" />
                  </div>
                  <h2 className="mt-5 text-xl font-semibold text-slate-100">
                    Simulazione in corso
                  </h2>
                  <p className="mt-2 text-sm text-slate-500">
                    {(() => {
                      const match = String(progressText || '').match(/(?:\D*)(\d+)\s*\/\s*(\d+)\s+simulazioni/i);
                      return match ? `${match[1]} / ${match[2]} simulazioni` : 'Elaborazione simulazione...';
                    })()}
                  </p>

                  <div className="mt-8">
                    <div className="relative">
                      <div className="h-4 overflow-hidden rounded-full border border-slate-700/80 bg-slate-950/80 shadow-[inset_0_1px_3px_rgba(0,0,0,0.35)]">
                        <div
                          className="relative h-full overflow-hidden rounded-full bg-gradient-to-r from-sky-400 via-blue-500 to-violet-500 transition-[width] duration-500 ease-out"
                          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
                        >
                          <div className="absolute inset-0 bg-[linear-gradient(110deg,transparent_0%,rgba(255,255,255,0.05)_35%,rgba(255,255,255,0.22)_50%,rgba(255,255,255,0.05)_65%,transparent_100%)] animate-[progressShimmer_1.8s_linear_infinite]" />
                          <div className="absolute inset-y-0 right-0 w-8 bg-white/20 blur-md" />
                        </div>
                      </div>

                      <div className="pointer-events-none absolute inset-0 rounded-full ring-1 ring-sky-400/10" />
                    </div>

                    <div className="mt-3 flex items-center justify-between text-xs">
                      <span className="text-slate-600">Avanzamento simulazione</span>
                      <span className="font-semibold tabular-nums text-transparent bg-clip-text bg-gradient-to-r from-sky-300 to-violet-300">
                        {progress.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </main>
        </div>
      </div>
      </>
    );
  }

  if (result) {
    const aggStats = result.aggregate_statistics || {};

    return (
      <div className="min-h-full bg-[#0B0E14]">
        <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
          <PageHeader
            title="Simula Stagione"
            description="Risultati simulazione Monte Carlo"
            actions={
              <Button type="button" variant="outline" onClick={handleReset}>
                <RotateCcw className="h-4 w-4" />
                Nuova simulazione
              </Button>
            }
          />

          <main className="mt-5 space-y-5">
            <Alert className="border-emerald-400/20 bg-emerald-400/[0.055]">
              <Check className="h-4 w-4 text-emerald-300" />
              <AlertDescription className="text-emerald-100/90">
                Simulazione completata!{' '}
                {result.total_simulations || nSimulations * 3} simulazioni totali.
              </AlertDescription>
            </Alert>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                label="Posizione media"
                value={aggStats.mean_position?.toFixed(1) || 'N/A'}
                detail={`Mediana: ${aggStats.median_position?.toFixed(1) || 'N/A'}`}
                icon={TrendingUp}
              />
              <KpiCard
                label="Punti medi"
                value={aggStats.mean_points?.toFixed(1) || 'N/A'}
                detail={`±${aggStats.std_points?.toFixed(1) || 'N/A'}`}
                icon={BarChart3}
              />
              <KpiCard
                label="Probabilità vittoria"
                value={`${aggStats.probability_win?.toFixed(1) || 0}%`}
                detail="1° posto"
                icon={TrophyIcon}
                tone="success"
              />
              <KpiCard
                label="Probabilità Top 3"
                value={`${aggStats.probability_top3?.toFixed(1) || 0}%`}
                detail="Podio"
                icon={Users}
              />
            </div>

            {(result.best_result || result.worst_result) && (
              <div className="grid gap-3 lg:grid-cols-3">
                {result.best_result && (
                  <Card className="border-emerald-400/15 bg-[#0F172A]">
                    <CardHeader className="px-5 pb-3">
                      <Badge className="w-fit border-emerald-300/20 bg-emerald-400/10 text-emerald-300">
                        Miglior caso
                      </Badge>
                    </CardHeader>
                    <CardContent className="grid grid-cols-2 gap-3">
                      <CaseMetric
                        label="Posizione"
                        value={result.best_result.final_position || 'N/A'}
                      />
                      <CaseMetric
                        label="Punti"
                        value={result.best_result.total_points?.toFixed(1) || 'N/A'}
                      />
                    </CardContent>
                  </Card>
                )}

                <Card className="border-sky-400/15 bg-[#0F172A]">
                  <CardHeader className="px-5 pb-3">
                    <Badge className="w-fit border-sky-300/20 bg-sky-400/10 text-sky-300">
                      Posizione più probabile
                    </Badge>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-3">
                    <CaseMetric
                      label="Posizione"
                      value={(() => {
                        const distribution = aggStats.position_distribution || {};
                        const entry = Object.entries(distribution).sort(
                          ([, a], [, b]) => Number(b) - Number(a)
                        )[0];
                        return entry ? `${entry[0]}°` : 'N/A';
                      })()}
                    />
                    <CaseMetric
                      label="Probabilità"
                      value={(() => {
                        const distribution = aggStats.position_distribution || {};
                        const entry = Object.entries(distribution).sort(
                          ([, a], [, b]) => Number(b) - Number(a)
                        )[0];
                        return entry ? `${Number(entry[1]).toFixed(1)}%` : 'N/A';
                      })()}
                    />
                  </CardContent>
                </Card>

                {result.worst_result && (
                  <Card className="border-red-400/15 bg-[#0F172A]">
                    <CardHeader className="px-5 pb-3">
                      <Badge variant="destructive" className="w-fit">
                        Peggior caso
                      </Badge>
                    </CardHeader>
                    <CardContent className="grid grid-cols-2 gap-3">
                      <CaseMetric
                        label="Posizione"
                        value={result.worst_result.final_position || 'N/A'}
                      />
                      <CaseMetric
                        label="Punti"
                        value={result.worst_result.total_points?.toFixed(1) || 'N/A'}
                      />
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {aggStats.position_distribution &&
              Object.keys(aggStats.position_distribution).length > 0 && (
                <Card className="border-slate-800/90 bg-[#0F172A]">
                  <CardHeader className="px-5 pb-4">
                    <CardTitle className="text-sm">Distribuzione posizioni</CardTitle>
                    <CardDescription>Probabilità per posizione finale</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(aggStats.position_distribution)
                      .sort(([a], [b]) => Number(a) - Number(b))
                      .map(([position, probability]) => (
                        <div
                          key={position}
                          className="grid grid-cols-[38px_1fr_55px] items-center gap-3"
                        >
                          <span className="text-sm font-semibold text-slate-300">
                            {position}°
                          </span>
                          <div className="h-2 overflow-hidden rounded-full bg-slate-900">
                            <div
                              className="h-full rounded-full bg-sky-400 transition-all"
                              style={{ width: `${probability}%` }}
                            />
                          </div>
                          <span className="text-right text-xs font-semibold text-sky-300">
                            {probability.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                  </CardContent>
                </Card>
              )}

          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1180px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title="Simula Stagione"
          description="Simulazione Monte Carlo stagione fantacalcio"
        />

        <main className="mt-5 space-y-5">
          {error && (
            <ErrorState
              title="Errore simulazione"
              message={error}
              onRetry={handleStartSimulation}
              className="py-4"
            />
          )}

          <div className="rounded-2xl border border-slate-800/90 bg-[#0F172A] px-3 py-4 sm:px-5">
            <div className="flex min-w-[680px] items-start">
              {[
                { number: 1, label: 'Rosa' },
                { number: 2, label: 'Calendario' },
                { number: 3, label: 'Configurazione' },
                { number: 4, label: 'Simula' },
              ].map((item, index, arr) => {
                const active = step === item.number;
                const completed = step > item.number;

                return (
                  <React.Fragment key={item.number}>
                    <button
                      type="button"
                      onClick={() => setStep(item.number)}
                      className="group flex shrink-0 appearance-none flex-col items-center gap-2 border-0 bg-transparent p-0 text-inherit outline-none"
                    >
                      <span
                        className={`flex h-9 w-9 items-center justify-center rounded-full border text-xs font-bold transition-all ${
                          completed
                            ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'
                            : active
                              ? 'border-sky-400/40 bg-sky-400 text-slate-950 shadow-[0_0_0_4px_rgba(56,189,248,0.08)]'
                              : 'border-slate-700 bg-slate-950/70 text-slate-500'
                        }`}
                      >
                        {completed ? <Check className="h-4 w-4" /> : item.number}
                      </span>
                      <span
                        className={`text-[11px] font-semibold ${
                          completed
                            ? 'text-emerald-300'
                            : active
                              ? 'text-slate-100'
                              : 'text-slate-600'
                        }`}
                      >
                        {item.label}
                      </span>
                    </button>

                    {index < arr.length - 1 && (
                      <div
                        className={`mx-3 mt-[18px] h-px min-w-12 flex-1 ${
                          completed ? 'bg-emerald-400/30' : 'bg-slate-800'
                        }`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {step === 1 && (
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="border-b border-slate-800/70 px-5 py-4">
                <CardTitle className="text-sm">Carica rosa</CardTitle>
                <CardDescription>
                  Seleziona una rosa salvata oppure importa un file JSON
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5 p-5">
                {savedRosas.length > 0 && (
                  <div>
                    <div className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Rose salvate
                    </div>

                    <div className="grid gap-3 md:grid-cols-2">
                      {savedRosas.map((rosaData, idx) => {
                        const filledCount = rosaData.roster.filter(
                          (r) => r.player
                        ).length;
                        const isSelected = selectedRosaName === rosaData.name;

                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSelectSavedRosa(rosaData)}
                            className={`rounded-xl border p-4 text-left transition-all ${
                              isSelected
                                ? 'border-sky-400/35 bg-sky-400/[0.06]'
                                : 'border-slate-800/80 bg-slate-950/20 hover:border-slate-700 hover:bg-slate-900/40'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex min-w-0 items-center gap-3">
                                <div
                                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
                                    isSelected
                                      ? 'border-sky-400/25 bg-sky-400/10 text-sky-300'
                                      : 'border-slate-700 bg-slate-900 text-slate-500'
                                  }`}
                                >
                                  <Users className="h-4 w-4" />
                                </div>
                                <div className="min-w-0">
                                  <div className="truncate text-sm font-semibold text-slate-100">
                                    {rosaData.name}
                                  </div>
                                  <div className="mt-1 text-xs text-slate-500">
                                    {filledCount} giocatori ·{' '}
                                    {new Date(rosaData.date).toLocaleDateString()}
                                  </div>
                                </div>
                              </div>

                              {isSelected && (
                                <Badge variant="success">Selezionata</Badge>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/20 p-5">
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-slate-500">
                      <FileJson className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">
                        Oppure importa da file
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        Formato JSON della rosa salvata
                      </div>
                    </div>
                  </div>

                  <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2.5 transition hover:border-sky-400/35 hover:bg-slate-950">
                    <span className="truncate text-sm text-slate-500">Nessun file selezionato</span>
                    <span className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-sky-400/25 bg-sky-400/[0.06] px-3 py-1.5 text-xs font-semibold text-sky-300">
                      <Upload className="h-3.5 w-3.5" />
                      Scegli file
                    </span>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleUploadRosa}
                      className="sr-only"
                    />
                  </label>

                  {rosa && !selectedRosaName && (
                    <Alert className="mt-3 border-sky-400/15 bg-sky-400/[0.04]">
                      <AlertCircle className="h-4 w-4 text-sky-300" />
                      <AlertDescription>
                        Rosa caricata: {rosa.players?.length || rosa.length || 0}{' '}
                        giocatori
                      </AlertDescription>
                    </Alert>
                  )}
                </div>

                <StepActions
                  backDisabled
                  nextDisabled={!rosa}
                  onNext={() => setStep(2)}
                />
              </CardContent>
            </Card>
          )}

          {step === 2 && (
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="border-b border-slate-800/70 px-5 py-4">
                <CardTitle className="text-sm">Carica calendario lega</CardTitle>
                <CardDescription>
                  Upload del calendario fantacalcio
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-5 p-5">
                {calendario ? (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.04] p-5">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.08] text-emerald-300">
                            <Calendar className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-slate-100">
                              Calendario caricato
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              {calendario.teams?.length || 0} squadre ·{' '}
                              {calendario.total_matchdays || 0} giornate
                            </div>
                          </div>
                        </div>

                        <Button
                          type="button"
                          variant="outline"
                          onClick={handleDeleteCalendar}
                          className="border-red-400/15 text-red-300 hover:bg-red-400/[0.06]"
                        >
                          Elimina calendario
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/20 p-5">
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-slate-500">
                          <Upload className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-slate-200">
                            Carica un nuovo calendario
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            Sostituirà il calendario attuale
                          </div>
                        </div>
                      </div>
                      <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2.5 transition hover:border-sky-400/35 hover:bg-slate-950">
                        <span className="truncate text-sm text-slate-500">Seleziona nuovo file</span>
                        <span className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-sky-400/25 bg-sky-400/[0.06] px-3 py-1.5 text-xs font-semibold text-sky-300">
                          <Upload className="h-3.5 w-3.5" />
                          Scegli file
                        </span>
                        <input
                          type="file"
                          accept=".xlsx,.xls,.csv"
                          onChange={handleUploadCalendar}
                          className="sr-only"
                        />
                      </label>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/20 p-5">
                    <div className="flex items-start gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-slate-500">
                        <Upload className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200">
                          Seleziona calendario
                        </div>
                        <div className="mt-1 text-xs text-slate-500">
                          XLSX, XLS o CSV
                        </div>
                      </div>
                    </div>
                    <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2.5 transition hover:border-sky-400/35 hover:bg-slate-950">
                      <span className="truncate text-sm text-slate-500">Nessun file selezionato</span>
                      <span className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-sky-400/25 bg-sky-400/[0.06] px-3 py-1.5 text-xs font-semibold text-sky-300">
                        <Upload className="h-3.5 w-3.5" />
                        Scegli file
                      </span>
                      <input
                        type="file"
                        accept=".xlsx,.xls,.csv"
                        onChange={handleUploadCalendar}
                        className="sr-only"
                      />
                    </label>
                  </div>
                )}

                <StepActions
                  onBack={() => setStep(1)}
                  onNext={() => setStep(3)}
                  nextDisabled={!calendario}
                />
              </CardContent>
            </Card>
          )}

          {step === 3 && (
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="border-b border-slate-800/70 px-5 py-4">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Settings2 className="h-4 w-4 text-sky-300" />
                  Configurazione simulazione
                </CardTitle>
                <CardDescription>
                  Imposta squadra e numero di simulazioni
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6 p-5">
                <div>
                  <label
                    htmlFor="myteam"
                    className="mb-2 block text-xs font-medium text-slate-400"
                  >
                    Nome squadra
                  </label>
                  {calendario?.teams && calendario.teams.length > 0 ? (
                    <div className="relative overflow-hidden rounded-lg">
                      <div className="absolute inset-x-0 top-0 z-10 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
                      <select
                        id="myteam"
                        value={myTeam}
                        onChange={(e) => setMyTeam(e.target.value)}
                        className="h-10 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100 outline-none focus:border-sky-400/40 focus:ring-2 focus:ring-sky-400/10"
                      >
                        <option value="">Seleziona squadra...</option>
                        {calendario.teams.map((team, idx) => (
                          <option key={idx} value={team}>
                            {team}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <Input
                      id="myteam"
                      type="text"
                      placeholder="Il mio team..."
                      value={myTeam}
                      onChange={(e) => setMyTeam(e.target.value)}
                    />
                  )}
                </div>

                <div className="rounded-xl border border-sky-400/10 bg-sky-400/[0.025] p-4">
                  <div className="flex items-end justify-between gap-3">
                    <div>
                      <label
                        htmlFor="nsim"
                        className="text-xs font-medium text-slate-400"
                      >
                        Simulazioni per scenario
                      </label>
                      <div className="mt-1 text-2xl font-bold text-sky-300">
                        {nSimulations}
                      </div>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      Totale
                      <div className="mt-1 font-semibold text-slate-200">
                        {nSimulations * 3}
                      </div>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent rounded-full" />
                    <input
                      id="nsim"
                      type="range"
                      min="10"
                      max="1000"
                      step="10"
                      value={nSimulations}
                      onChange={(e) => setNSimulations(Number(e.target.value))}
                      className="mt-5 w-full accent-sky-400"
                    />
                  </div>
                  <div className="mt-2 flex justify-between text-[10px] text-slate-600">
                    <span>10</span>
                    <span>500</span>
                    <span>1000</span>
                  </div>
                </div>

                <div>
                  <div className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                    Opzioni avanzate
                  </div>
                  <div className="grid gap-2 md:grid-cols-3">
                    <ToggleField
                      checked={settings.defenseModifierEnabled}
                      onChange={(checked) =>
                        setSettings({ ...settings, defenseModifierEnabled: checked })
                      }
                      label="Modificatore Difesa"
                    />
                    <ToggleField
                      checked={settings.mvpBonusEnabled}
                      onChange={(checked) =>
                        setSettings({ ...settings, mvpBonusEnabled: checked })
                      }
                      label="Bonus MVP"
                    />
                    <ToggleField
                      checked={settings.cleanSheetEnabled}
                      onChange={(checked) =>
                        setSettings({ ...settings, cleanSheetEnabled: checked })
                      }
                      label="Clean Sheet Portiere"
                    />
                  </div>
                </div>

                <StepActions
                  onBack={() => setStep(2)}
                  onNext={() => setStep(4)}
                  nextDisabled={!myTeam.trim()}
                />
              </CardContent>
            </Card>
          )}

          {step === 4 && (
            <Card className="border-sky-400/20 bg-[#0F172A]">
              <CardHeader className="border-b border-slate-800/70 px-5 py-4">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Play className="h-4 w-4 text-sky-300" />
                  Pronto per simulare
                </CardTitle>
                <CardDescription>
                  Verifica la configurazione e avvia il motore Monte Carlo
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-5 p-5">
                <div className="grid gap-2 sm:grid-cols-2">
                  <SummaryItem
                    label="Rosa"
                    value={`${rosa?.players?.length || rosa?.length || 0} giocatori`}
                  />
                  <SummaryItem
                    label="Calendario"
                    value={`${calendario?.teams?.length || 0} squadre`}
                  />
                  <SummaryItem label="Squadra" value={myTeam} />
                  <SummaryItem
                    label="Simulazioni"
                    value={`${nSimulations * 3} totali`}
                  />
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950/25 p-4">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="h-5 w-5 text-sky-300" />
                    <div>
                      <div className="text-sm font-semibold text-slate-200">
                        Configurazione pronta
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        La simulazione utilizzerà tutte le impostazioni sopra
                      </div>
                    </div>
                  </div>
                </div>

                <StepActions
                  onBack={() => setStep(3)}
                  onNext={handleStartSimulation}
                  nextLabel="Avvia simulazione"
                  nextIcon={Play}
                  nextDisabled={false}
                />
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}

function ToggleField({ checked, onChange, label }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-950/20 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-sky-400"
      />
    </label>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/20 px-4 py-3">
      <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-slate-600">
        {label}
      </div>
      <div className="mt-1 truncate text-sm font-semibold text-slate-200">{value}</div>
    </div>
  );
}

function CaseMetric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/25 p-4">
      <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-slate-600">
        {label}
      </div>
      <div className="mt-1 text-xl font-bold text-slate-100">{value}</div>
    </div>
  );
}

function StepActions({
  onBack,
  onNext,
  nextDisabled,
  backDisabled = false,
  nextLabel = 'Avanti',
  nextIcon: NextIcon = ChevronRight,
}) {
  return (
    <div className="flex flex-col-reverse gap-2 border-t border-slate-800/70 pt-4 sm:flex-row sm:items-center sm:justify-between">
      <Button
        type="button"
        variant="outline"
        onClick={onBack}
        disabled={backDisabled}
        className="w-full sm:w-auto"
      >
        <ChevronLeft className="h-4 w-4" />
        Indietro
      </Button>

      <Button
        type="button"
        onClick={onNext}
        disabled={nextDisabled}
        className="w-full sm:w-auto"
      >
        {nextLabel}
        <NextIcon className="h-4 w-4" />
      </Button>
    </div>
  );
}

function TrophyIcon({ className = 'h-5 w-5' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M6 9H3V5h3" />
      <path d="M18 9h3V5h-3" />
      <path d="M6 5h12v5a6 6 0 0 1-12 0V5Z" />
      <path d="M12 16v4" />
      <path d="M8 21h8" />
    </svg>
  );
}

export default SimulaStagione;
