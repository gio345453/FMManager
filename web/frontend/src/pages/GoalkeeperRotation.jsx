import React, { useState, useEffect } from 'react';
import {
  Calendar,
  ChevronRight,
  Search,
  Shield,
  Target,
  TrendingUp,
  X,
} from 'lucide-react';
import { playersApi } from '../api/client';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import KpiCard from '../components/common/KpiCard';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { PlayerAvatar } from '../components/common/PlayerMedia';

const calendarScrollbarStyles = `
  .calendar-scroll {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.38) rgba(15, 23, 42, 0.55);
    scrollbar-gutter: stable;
  }

  .calendar-scroll::-webkit-scrollbar {
    height: 7px;
  }

  .calendar-scroll::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(51, 65, 85, 0.45);
    border-radius: 999px;
  }

  .calendar-scroll::-webkit-scrollbar-thumb {
    background: linear-gradient(90deg, rgba(71, 85, 105, 0.9), rgba(100, 116, 139, 0.85));
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 999px;
  }

  .calendar-scroll::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(90deg, rgba(100, 116, 139, 0.95), rgba(148, 163, 184, 0.9));
  }
`;

function GoalkeeperRotation() {
  const [goalkeepers, setGoalkeepers] = useState([]);
  const [allGoalkeepers, setAllGoalkeepers] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searching, setSearching] = useState(false);
  const [fromMatchday, setFromMatchday] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadAllGoalkeepers();
    loadSessionData();
  }, []);

  const loadAllGoalkeepers = async () => {
    try {
      setLoadingList(true);
      const res = await playersApi.getAll({ role: 'P' });
      setAllGoalkeepers(res.data || []);
    } catch (err) {
      console.error('Error loading goalkeepers:', err);
    } finally {
      setLoadingList(false);
    }
  };

  const loadSessionData = () => {
    try {
      const saved = sessionStorage.getItem('goalkeeper_rotation_session');
      if (saved) {
        const data = JSON.parse(saved);
        if (data.goalkeepers) setGoalkeepers(data.goalkeepers);
        if (data.fromMatchday) setFromMatchday(data.fromMatchday);
        if (data.result) setResult(data.result);
        if (data.error) setError(data.error);
      }
    } catch (err) {
      console.error('Error loading session data:', err);
    }
  };

  const saveSessionData = () => {
    try {
      sessionStorage.setItem(
        'goalkeeper_rotation_session',
        JSON.stringify({
          goalkeepers,
          fromMatchday,
          result,
          error,
        })
      );
    } catch (err) {
      console.error('Error saving session data:', err);
    }
  };

  useEffect(() => {
    if (goalkeepers.length > 0 || result || error) {
      saveSessionData();
    }
  }, [goalkeepers, fromMatchday, result, error]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (searchTerm.length >= 2) {
        setSearching(true);
        try {
          const res = await playersApi.getAll({
            search: searchTerm,
            role: 'P',
          });
          setSearchResults(res.data.slice(0, 20));
        } catch (err) {
          console.error('Search error:', err);
          setSearchResults([]);
        }
        setSearching(false);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const addGoalkeeper = (player) => {
    if (goalkeepers.length >= 3) {
      alert('Massimo 3 portieri');
      return;
    }
    if (goalkeepers.find((g) => g.id === player.id)) {
      alert('Portiere già aggiunto');
      return;
    }
    setGoalkeepers([...goalkeepers, player]);
    setSearchTerm('');
    setSearchResults([]);
  };

  const removeGoalkeeper = (id) => {
    setGoalkeepers(goalkeepers.filter((g) => g.id !== id));
  };

  const handleAnalyze = async () => {
    if (goalkeepers.length < 2) {
      alert('Seleziona almeno 2 portieri');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      goalkeepers.forEach((gk) => {
        params.append('goalkeeper_ids', gk.id);
      });
      if (fromMatchday > 1) {
        params.append('from_matchday', fromMatchday);
      }

      const response = await fetch(
        `/api/goalkeeper-rotation/analyze?${params.toString()}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Errore analisi rotazione');
      }

      const data = await response.json();
      setResult(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setGoalkeepers([]);
    setResult(null);
    setError(null);
    setFromMatchday(1);
    sessionStorage.removeItem('goalkeeper_rotation_session');
  };

  const getDifficultyColor = (difficulty) => {
    if (difficulty <= 2) return '#10B981';
    if (difficulty <= 3) return '#F59E0B';
    return '#EF4444';
  };

  const getDifficultyLabel = (difficulty) => {
    if (difficulty <= 2) return 'Facile';
    if (difficulty <= 3) return 'Media';
    return 'Difficile';
  };

  if (loading) {
    return (
      <LoadingState
        message="Analisi rotazione in corso..."
        className="py-16"
      />
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <style>{calendarScrollbarStyles}</style>
      <div className="mx-auto w-full max-w-[1500px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title="Rotazione Portieri"
          description="Analizza la rotazione ottimale per 2-3 portieri"
        />

        <main className="mt-5 space-y-5">
          {error && !result && (
            <ErrorState
              title="Errore analisi"
              message={error}
              onRetry={handleAnalyze}
              className="py-4"
            />
          )}

          {!result && (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <KpiCard
                  label="Portieri selezionati"
                  value={`${goalkeepers.length}/3`}
                  icon={Shield}
                  tone={goalkeepers.length >= 2 ? 'success' : 'primary'}
                />
                <KpiCard
                  label="Disponibili"
                  value={allGoalkeepers.length}
                  icon={UsersIcon}
                />
                <KpiCard
                  label="Giornata di partenza"
                  value={fromMatchday}
                  icon={Calendar}
                />
              </div>

              <div className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
                <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A]">
                  <div className="border-b border-slate-800/70 px-5 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="text-sm font-semibold text-slate-100">
                          Seleziona portieri
                        </h2>
                        <p className="mt-1 text-xs text-slate-500">
                          Scegli da 2 a 3 portieri per costruire la rotazione
                        </p>
                      </div>
                      <Badge variant="secondary">
                        {goalkeepers.length}/3
                      </Badge>
                    </div>
                  </div>

                  <div className="space-y-5 p-5">
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />
                      <Input
                        id="search"
                        type="text"
                        placeholder="Cerca portiere..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                      {searching && (
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500">
                          Ricerca...
                        </span>
                      )}

                      {searchResults.length > 0 && (
                        <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-40 max-h-72 overflow-auto rounded-xl border border-slate-700 bg-[#111827] p-1.5 shadow-2xl">
                          {searchResults.map((player) => (
                            <button
                              type="button"
                              key={player.id}
                              onClick={() => addGoalkeeper(player)}
                              className="group flex w-full items-center gap-3 rounded-lg border border-slate-700/60 bg-[#111827] px-3 py-2.5 text-left transition-all hover:border-emerald-400/45 hover:bg-emerald-500/15"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="truncate text-sm font-semibold text-slate-100 group-hover:text-emerald-50">
                                  {player.nome}
                                </div>
                                <div className="mt-1 text-xs text-slate-400">
                                  {player.squadra}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                                  FM
                                </div>
                                <div className="text-sm font-semibold text-sky-300">
                                  {player.fm_weighted?.toFixed(2) || '-'}
                                </div>
                              </div>
                              <Badge
                                variant="outline"
                                className="border-amber-300/20 bg-amber-400/[0.06] text-amber-300"
                              >
                                P
                              </Badge>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="mb-2 flex items-center justify-between">
                        <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                          Tutti i portieri
                        </div>
                        <span className="text-xs text-slate-600">
                          {allGoalkeepers.length} disponibili
                        </span>
                      </div>

                      {loadingList ? (
                        <div className="rounded-xl border border-slate-800/70 bg-slate-950/25 px-4 py-8 text-center text-sm text-slate-500">
                          Caricamento portieri...
                        </div>
                      ) : (
                        <div className="max-h-[420px] overflow-auto pr-1">
                          <div className="space-y-2">
                            {allGoalkeepers.map((player) => {
                              const selected = goalkeepers.find(
                                (g) => g.id === player.id
                              );

                              return (
                                <button
                                  type="button"
                                  key={player.id}
                                  onClick={() => addGoalkeeper(player)}
                                  className={`group flex w-full items-center gap-3 rounded-xl border px-3.5 py-3 text-left transition-all ${
                                    selected
                                      ? 'border-sky-400/25 bg-sky-400/[0.07]'
                                      : 'border-slate-800/80 bg-slate-950/20 hover:border-slate-700 hover:bg-slate-900/40'
                                  }`}
                                >
                                  <div
                                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                                      selected
                                        ? 'border-sky-400/25 bg-sky-400/10 text-sky-300'
                                        : 'border-slate-700 bg-slate-900 text-slate-500'
                                    }`}
                                  >
                                    <Shield className="h-4 w-4" />
                                  </div>
                                  <div className="min-w-0 flex-1">
                                    <div className="truncate text-sm font-semibold text-slate-100">
                                      {player.nome}
                                    </div>
                                    <div className="mt-1 text-xs text-slate-500">
                                      {player.squadra}
                                    </div>
                                  </div>
                                  <div className="hidden text-right sm:block">
                                    <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                                      FM
                                    </div>
                                    <div className="text-sm font-semibold text-sky-300">
                                      {player.fm_weighted?.toFixed(2) || '-'}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                                      Prezzo
                                    </div>
                                    <div className="text-xs font-medium text-slate-300">
                                      {player.price_credits?.toFixed(1) || '-'} cr
                                    </div>
                                  </div>
                                  <ChevronRight className="h-4 w-4 text-slate-700 group-hover:text-sky-300" />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A]">
                  <div className="border-b border-slate-800/70 px-5 py-4">
                    <h2 className="text-sm font-semibold text-slate-100">
                      Portieri selezionati
                    </h2>
                    <p className="mt-1 text-xs text-slate-500">
                      Questi saranno utilizzati per l'analisi
                    </p>
                  </div>

                  <div className="space-y-5 p-5">
                    {goalkeepers.length === 0 ? (
                      <EmptyState
                        icon={Shield}
                        title="Nessun portiere"
                        description="Cerca o seleziona almeno 2 portieri"
                      />
                    ) : (
                      <div className="space-y-2.5">
                        {goalkeepers.map((gk, idx) => (
                          <div
                            key={gk.id}
                            className="flex items-center gap-3 rounded-xl border border-sky-400/15 bg-sky-400/[0.045] p-3.5"
                          >
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-sky-400/20 bg-sky-400/[0.08] text-sky-300">
                              <span className="text-xs font-bold">{idx + 1}</span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="truncate text-sm font-semibold text-slate-100">
                                {gk.nome}
                              </div>
                              <div className="mt-1 text-xs text-slate-500">
                                {gk.squadra} · FM {gk.fm_weighted?.toFixed(2) || '-'}
                              </div>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeGoalkeeper(gk.id)}
                              className="text-slate-500 hover:bg-red-400/10 hover:text-red-300"
                              aria-label={`Rimuovi ${gk.nome}`}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <label
                            htmlFor="matchday"
                            className="text-sm font-semibold text-slate-200"
                          >
                            Giornata di inizio
                          </label>
                          <p className="mt-1 text-xs text-slate-500">
                            Da quale giornata vuoi calcolare la rotazione?
                          </p>
                        </div>
                        <Badge variant="secondary">{fromMatchday}/38</Badge>
                      </div>

                      <div className="relative">
                        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent rounded-full" />
                        <input
                          id="matchday"
                          type="range"
                          min="1"
                          max="38"
                          value={fromMatchday}
                          onChange={(e) =>
                            setFromMatchday(Number(e.target.value))
                          }
                          className="mt-4 w-full accent-sky-400"
                        />
                      </div>

                      <div className="mt-2 flex justify-between text-[10px] text-slate-600">
                        <span>1</span>
                        <span>19</span>
                        <span>38</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 sm:flex-row">
                      <Button
                        type="button"
                        onClick={handleAnalyze}
                        disabled={goalkeepers.length < 2}
                        className="w-full sm:flex-1"
                      >
                        <TrendingUp className="h-4 w-4" />
                        Analizza rotazione
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleReset}
                        className="w-full sm:w-auto"
                      >
                        Reset
                      </Button>
                    </div>
                  </div>
                </section>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              <Alert className="border-emerald-400/20 bg-emerald-400/[0.055]">
                <TrendingUp className="h-4 w-4 text-emerald-300" />
                <AlertDescription className="text-emerald-100/90">
                  Analisi completata! Rotazione ottimale calcolata per{' '}
                  <strong>{result.total_matchdays}</strong> giornate.
                </AlertDescription>
              </Alert>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <KpiCard
                  label="Overall abbinamento"
                  value={
                    result.combinations?.overall_rating?.toFixed(1) || 'N/A'
                  }
                  detail="Valutazione 0-10"
                  icon={TrendingUp}
                />
                <KpiCard
                  label="Partite facili"
                  value={result.combinations?.green_matchdays || 0}
                  detail="Difficoltà bassa"
                  icon={Shield}
                  tone="success"
                />
                <KpiCard
                  label="Partite medie"
                  value={result.combinations?.yellow_matchdays || 0}
                  detail="Difficoltà media"
                  icon={Calendar}
                  tone="warning"
                />
                <KpiCard
                  label="Partite difficili"
                  value={result.combinations?.red_matchdays || 0}
                  detail="Difficoltà alta"
                  icon={Target}
                  tone="danger"
                />
              </div>

              {result.combinations?.goalkeeper_usage && (
                <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A]">
                  <div className="border-b border-slate-800/70 px-5 py-4">
                    <h2 className="text-sm font-semibold text-slate-100">
                      Utilizzo portieri
                    </h2>
                    <p className="mt-1 text-xs text-slate-500">
                      Distribuzione delle presenze nella rotazione ottimizzata
                    </p>
                  </div>

                  <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">
                    {Object.entries(result.combinations.goalkeeper_usage).map(
                      ([name, count]) => {
                        const goalkeeper = allGoalkeepers.find((gk) => gk.nome === name);
                        return (
                        <div
                          key={name}
                          className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4"
                        >
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 shrink-0 overflow-hidden rounded-full border border-sky-400/20 bg-slate-900/70">
                              {goalkeeper?.id ? (
                                <PlayerAvatar playerId={goalkeeper.id} size="small" />
                              ) : (
                                <Shield className="m-2.5 h-5 w-5 text-slate-500" />
                              )}
                            </div>
                            <div className="min-w-0 truncate text-sm font-semibold text-slate-100">
                              {name}
                            </div>
                          </div>
                          <div className="mt-3 flex items-end justify-between">
                            <div>
                              <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                                Partite
                              </div>
                              <div className="mt-1 text-2xl font-bold text-sky-300">
                                {count}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                                Quota
                              </div>
                              <div className="mt-1 text-sm font-semibold text-slate-200">
                                {(
                                  (count / result.total_matchdays) *
                                  100
                                ).toFixed(1)}
                                %
                              </div>
                            </div>
                          </div>
                        </div>
                        );
                      })}

                  </div>
                </section>
              )}

              <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A]">
                <div className="border-b border-slate-800/70 px-5 py-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <h2 className="text-sm font-semibold text-slate-100">
                        Calendario completo
                      </h2>
                      <p className="mt-1 text-xs text-slate-500">
                        Scorri orizzontalmente · Colori = difficoltà · Evidenziato = scelta consigliata
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2 text-[11px]">
                      {[1, 2.5, 4].map((difficulty) => (
                        <span
                          key={difficulty}
                          className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-950/30 px-2.5 py-1 text-slate-400"
                        >
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{ background: getDifficultyColor(difficulty) }}
                          />
                          {getDifficultyLabel(difficulty)}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {result.grids && result.grids.length > 0 && (
                  <div className="calendar-scroll overflow-x-auto p-3 sm:p-5">
                    <div className="inline-flex min-w-full flex-col gap-3">
                      {result.grids.map((gkGrid) => (
                        <div key={gkGrid.goalkeeper_id} className="flex flex-col gap-2">
                          <div className="flex items-center gap-2 px-1">
                            <Shield className="h-4 w-4 text-slate-500" />
                            <div>
                              <div className="text-sm font-semibold text-slate-200">
                                {gkGrid.goalkeeper_name}
                              </div>
                              <div className="text-[10px] text-slate-600">
                                {gkGrid.team}
                              </div>
                            </div>
                          </div>

                          <div className="calendar-scroll flex gap-2 overflow-x-auto pb-2">
                            {gkGrid.grid.map((cell, matchdayIdx) => {
                              const matchday = result.from_matchday + matchdayIdx;
                              const bestChoice =
                                result.combinations?.best_choice_per_matchday?.[matchdayIdx];
                              const isBest = bestChoice?.goalkeeper === gkGrid.goalkeeper_name;

                              const bg =
                                cell.color === 'green'
                                  ? '#10B981'
                                  : cell.color === 'yellow'
                                    ? '#F59E0B'
                                    : cell.color === 'red'
                                      ? '#EF4444'
                                      : '#6B7280';

                              return (
                                <div
                                  key={matchday}
                                  className="relative flex shrink-0 flex-col"
                                >
                                  <div className="mb-1 text-center text-[10px] font-semibold text-slate-500">
                                    {matchday}
                                  </div>
                                  <div
                                    className={`relative flex h-[72px] w-[90px] flex-col items-center justify-center rounded-lg border px-2 py-2 text-center ${
                                      isBest
                                        ? 'border-amber-400/60 ring-2 ring-amber-400/20'
                                        : 'border-slate-700/50'
                                    }`}
                                    style={{
                                      backgroundColor: bg,
                                      opacity: cell.playable ? 0.92 : 0.2,
                                    }}
                                  >
                                    {isBest && (
                                      <div
                                        className="absolute -right-2 -top-2 rounded-full border border-amber-300/35 bg-[#0F172A] px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-amber-300 shadow-[0_0_12px_rgba(251,191,36,0.12)]"
                                        title="Scelta consigliata"
                                        aria-label="Scelta consigliata"
                                      >
                                        TOP
                                      </div>
                                    )}
                                    <div className="truncate text-[11px] font-semibold text-white">
                                      {cell.opponent}
                                    </div>
                                    {cell.playable && (
                                      <>
                                        <div className="mt-1 text-[9px] font-medium text-white/80">
                                          {cell.is_home ? 'CASA' : 'TRASF.'}
                                        </div>
                                        <div className="mt-0.5 text-[10px] font-bold text-white">
                                          {cell.difficulty_score?.toFixed(1)}
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}

                      <div className="mt-2 flex flex-col gap-2 rounded-xl border border-slate-800/80 bg-slate-950/25 p-4">
                        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                          <span className="rounded-full border border-amber-300/35 bg-[#0F172A] px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-[0.08em] text-amber-300">
                            TOP
                          </span>
                          Scelte consigliate
                        </div>
                        <div className="calendar-scroll flex gap-2 overflow-x-auto pb-2">
                          {result.grids[0].grid.map((_, matchdayIdx) => {
                            const matchday = result.from_matchday + matchdayIdx;
                            const bestChoice =
                              result.combinations?.best_choice_per_matchday?.[matchdayIdx];

                            return (
                              <div
                                key={matchday}
                                className="flex shrink-0 flex-col items-center gap-1"
                              >
                                <div className="text-[10px] font-semibold text-slate-500">
                                  {matchday}
                                </div>
                                {bestChoice && (
                                  <div className="flex h-[72px] w-[90px] flex-col items-center justify-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/70 px-2 py-2">
                                    <span className="text-center text-xs font-semibold text-slate-200">
                                      {bestChoice.goalkeeper?.split(' ').pop()}
                                    </span>
                                    <Badge
                                      variant="outline"
                                      className="text-[10px]"
                                      style={{
                                        borderColor:
                                          bestChoice.color === 'green'
                                            ? '#10B981'
                                            : bestChoice.color === 'yellow'
                                              ? '#F59E0B'
                                              : '#EF4444',
                                        color:
                                          bestChoice.color === 'green'
                                            ? '#10B981'
                                            : bestChoice.color === 'yellow'
                                              ? '#F59E0B'
                                              : '#EF4444',
                                      }}
                                    >
                                      {bestChoice.difficulty?.toFixed(1)}
                                    </Badge>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              <div className="flex justify-end">
                <Button type="button" onClick={handleReset}>
                  <RotateCcwIcon />
                  Nuova analisi
                </Button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function UsersIcon({ className = 'h-5 w-5' }) {
  return (
    <UsersGlyph className={className} aria-hidden="true" />
  );
}

function UsersGlyph(props) {
  const { className } = props;
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function RotateCcwIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M3 12a9 9 0 1 0 3-6.7" />
      <path d="M3 4v6h6" />
    </svg>
  );
}

export default GoalkeeperRotation;
