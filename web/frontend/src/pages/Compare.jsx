import React, { useState, useEffect } from 'react';
import { GitCompareArrows, X, Trophy, Users, ChevronRight, UserRound, BarChart3, TrendingUp, Shield, Star, Lightbulb } from 'lucide-react';
import { playersApi } from '../api/client';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { PlayerAvatar } from '../components/common/PlayerMedia';

function Compare() {
  const [selectedIds, setSelectedIds] = useState(['', '', '']);
  const [selectedPlayers, setSelectedPlayers] = useState([null, null, null]);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSlot, setActiveSlot] = useState(null);
  const [roleFilter, setRoleFilter] = useState('Tutti');
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  useEffect(() => {
    loadRecommendations();
  }, [selectedIds]);

  const loadRecommendations = async () => {
    try {
      setLoadingRecommendations(true);
      const validIds = selectedIds.filter((id) => id);
      const selectedIdsStr = validIds.length > 0 ? validIds.join(',') : null;
      const res = await playersApi.recommend(selectedIdsStr, 500, 5);
      setRecommendations(res.data);
      setLoadingRecommendations(false);
    } catch (err) {
      setLoadingRecommendations(false);
    }
  };

  const searchPlayers = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const params = { search: query };
      if (roleFilter !== 'Tutti') {
        params.role = roleFilter;
      }
      const res = await playersApi.getAll(params);
      setSearchResults(res.data.slice(0, 10));
    } catch (err) {
      setSearchResults([]);
    }
  };

  const selectPlayer = (slot, player) => {
    const newIds = [...selectedIds];
    const newPlayers = [...selectedPlayers];
    newIds[slot] = player.id.toString();
    newPlayers[slot] = player;
    setSelectedIds(newIds);
    setSelectedPlayers(newPlayers);
    setActiveSlot(null);
    setSearchQuery('');
    setSearchResults([]);
  };

  const removePlayer = (slot) => {
    const newIds = [...selectedIds];
    const newPlayers = [...selectedPlayers];
    newIds[slot] = '';
    newPlayers[slot] = null;
    setSelectedIds(newIds);
    setSelectedPlayers(newPlayers);
  };

  const comparePlayers = async () => {
    const validIds = selectedIds.filter((id) => id).join(',');
    const count = selectedIds.filter((id) => id).length;

    if (count < 2 || count > 3) {
      setError('Seleziona 2 o 3 giocatori da confrontare');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await playersApi.compare(validIds, 500);
      setComparison(res.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchQuery) {
      const timer = setTimeout(() => searchPlayers(searchQuery), 300);
      return () => clearTimeout(timer);
    }

    setSearchResults([]);
  }, [searchQuery, roleFilter]);

  const selectedCount = selectedIds.filter((id) => id).length;

  return (



    <div className="min-h-full bg-[#0B0E14]">
      <style>{`
        .player-search-dropdown {
          scrollbar-width: thin;
          scrollbar-color: #38bdf8 #0f172a;
        }

        .player-search-dropdown::-webkit-scrollbar {
          width: 8px;
        }

        .player-search-dropdown::-webkit-scrollbar-track {
          background: #0f172a;
          border-radius: 9999px;
        }

        .player-search-dropdown::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 9999px;
          border: 2px solid #0f172a;
        }

        .player-search-dropdown::-webkit-scrollbar-thumb:hover {
          background: #38bdf8;
        }
      `}</style>
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-sky-400/15 bg-sky-400/[0.07] shadow-[0_0_30px_rgba(56,189,248,0.06)]">
            <Users className="h-6 w-6 text-sky-300" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-50 sm:text-3xl">
              Confronto Giocatori
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Confronta 2 o 3 giocatori side-by-side per analizzare statistiche e performance.
            </p>
          </div>
        </div>

        <main className="mt-5 space-y-5">
          <Card className="overflow-visible border border-slate-700/80 bg-gradient-to-br from-[#101b34] via-[#0F172A] to-[#0B1224] shadow-[0_18px_60px_rgba(0,0,0,0.18)]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4 sm:px-6 sm:py-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-blue-400/30 bg-blue-500/15 text-blue-300">
                    <span className="text-sm font-bold">1</span>
                  </div>
                  <div>
                    <CardTitle className="text-sm font-semibold text-slate-100">
                      Seleziona i giocatori
                    </CardTitle>
                    <CardDescription className="mt-1 text-xs text-slate-500">
                      Scegli 2 o 3 giocatori da confrontare
                    </CardDescription>
                  </div>
                </div>
                <Badge
                  variant={selectedCount >= 2 ? 'success' : 'secondary'}
                  className="w-fit"
                >
                  {selectedCount}/3 selezionati
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-5 p-5">
              <div>
                <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                  Filtra per ruolo
                </div>
                <div className="flex flex-wrap gap-2">
                  {['Tutti', 'P', 'D', 'C', 'A'].map((role) => (
                    <Button
                      key={role}
                      type="button"
                      variant={roleFilter === role ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setRoleFilter(role)}
                      className={
                        roleFilter === role
                          ? 'border-sky-300/30 bg-sky-400 text-slate-950 shadow-[0_0_22px_rgba(56,189,248,0.12)] hover:bg-sky-300'
                          : 'border-slate-700/80 bg-slate-950/20 text-slate-400 hover:border-slate-500 hover:bg-slate-900/50 hover:text-slate-100'
                      }
                    >
                      {role}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-3">
                {[0, 1, 2].map((slot) => (
                  <div
                    key={slot}
                    className={`relative rounded-xl border bg-slate-950/20 p-4 shadow-[0_12px_30px_rgba(0,0,0,0.12)] ${
                      slot === 0
                        ? 'border-sky-400/35'
                        : slot === 1
                          ? 'border-violet-400/30'
                          : 'border-amber-400/30'
                    }`}
                  >
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <label className="text-xs font-semibold text-slate-300">
                        Giocatore {slot + 1}
                      </label>
                      {slot === 2 && (
                        <span className="text-[10px] uppercase tracking-[0.08em] text-slate-600">
                          opzionale
                        </span>
                      )}
                    </div>

                    {selectedIds[slot] ? (
                      <div className={`flex min-h-[64px] items-center gap-3 rounded-lg border px-3 py-3 ${
                        slot === 0
                          ? 'border-sky-400/20 bg-sky-400/[0.05]'
                          : slot === 1
                            ? 'border-violet-400/20 bg-violet-400/[0.05]'
                            : 'border-amber-400/20 bg-amber-400/[0.05]'
                      }`}>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-semibold text-slate-100">
                            {selectedPlayers[slot]?.nome}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            {selectedPlayers[slot]?.squadra} · {selectedPlayers[slot]?.ruolo}
                          </div>
                        </div>

                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removePlayer(slot)}
                          className="shrink-0 text-slate-500 hover:bg-red-400/10 hover:text-red-300"
                          aria-label={`Rimuovi giocatore ${slot + 1}`}
                        >
                          <X className="h-4 w-4" aria-hidden="true" />
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center gap-3">
                          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border ${
                            slot === 0
                              ? 'border-sky-400/30 bg-sky-400/10 text-sky-300'
                              : slot === 1
                                ? 'border-violet-400/30 bg-violet-400/10 text-violet-300'
                                : 'border-amber-400/30 bg-amber-400/10 text-amber-300'
                          }`}>
                            <UserRound className="h-5 w-5" aria-hidden="true" />
                          </div>

                          <div className="relative min-w-0 flex-1">
                            <Input
                              type="text"
                              placeholder="Cerca giocatore..."
                              value={activeSlot === slot ? searchQuery : ''}
                              onFocus={() => setActiveSlot(slot)}
                              onChange={(e) => setSearchQuery(e.target.value)}
                              className={`h-11 w-full border-slate-700 bg-slate-950/50 text-sm placeholder:text-slate-500 ${
                                slot === 0
                                  ? 'focus-visible:border-sky-400/50 focus-visible:ring-sky-400/20'
                                  : slot === 1
                                    ? 'focus-visible:border-violet-400/50 focus-visible:ring-violet-400/20'
                                    : 'focus-visible:border-amber-400/50 focus-visible:ring-amber-400/20'
                              }`}
                              aria-label={`Cerca giocatore per slot ${slot + 1}`}
                            />

                            {activeSlot === slot && searchResults.length > 0 && (
                              <div
  className="player-search-dropdown absolute left-0 right-0 top-full z-[100] mt-2 max-h-72 overflow-y-auto overflow-x-hidden rounded-xl border border-slate-700/90 p-1.5 text-slate-100 shadow-[0_18px_45px_rgba(0,0,0,0.5)]"
  style={{ backgroundColor: '#0F172A', opacity: 1 }}
>
                                {searchResults.map((player) => (
                                  <button
                                    type="button"
                                    key={player.id}
                                    onClick={() => selectPlayer(slot, player)}
                                    className="flex w-full items-center justify-between gap-3 rounded-lg border border-transparent bg-transparent px-3 py-2.5 text-left text-slate-100 transition-colors hover:border-slate-700 hover:bg-slate-800/80 focus:outline-none"
                                  >
                                    <div className="min-w-0">
                                      <div className="truncate text-sm font-semibold text-slate-100">
                                        {player.nome}
                                      </div>
                                      <div className="mt-0.5 truncate text-xs text-slate-400">
                                        {player.squadra} · {player.ruolo}
                                      </div>
                                    </div>
                                    <Badge variant="secondary" className="shrink-0 bg-slate-800 text-slate-200">
                                      {player.overall || 'N/A'}
                                    </Badge>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        <p className="mt-1.5 pl-14 text-[11px] text-slate-500">
                          Digita nome o cognome
                        </p>
                      </div>
                    )}
                    {slot < 2 && (
                      <div className="pointer-events-none absolute -right-3 top-1/2 z-20 hidden -translate-y-1/2 lg:flex">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-600/90 bg-[#0B1224] text-[10px] font-semibold text-slate-300 shadow-xl">
                          VS
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-3 border-t border-slate-800/70 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-slate-500">
                  {selectedCount < 2
                    ? 'Seleziona almeno 2 giocatori per avviare il confronto.'
                    : 'Puoi confrontare fino a 3 giocatori.'}
                </div>

                <Button
                  type="button"
                  onClick={comparePlayers}
                  disabled={selectedCount < 2 || loading}
                  className="w-full sm:w-auto"
                >
                  <GitCompareArrows className="h-4 w-4" aria-hidden="true" />
                  {loading ? 'Confronto in corso...' : 'Confronta giocatori'}
                </Button>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {loading && (
            <LoadingState
              message="Caricamento confronto..."
              className="py-10"
            />
          )}

          {comparison && (
            <>
              <Card className="border border-slate-700/70 bg-gradient-to-br from-[#0E1830] via-[#0F172A] to-[#0C1426]">
                <CardHeader className="px-5 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-sm font-semibold text-slate-100">
                        Statistiche comparative
                      </CardTitle>
                      <CardDescription className="mt-1 text-xs text-slate-500">
                        Medie dei giocatori selezionati
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">
                      {comparison.comparison.count} giocatori
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <SummaryMetric label="FM media" value={comparison.comparison.avg_fm.toFixed(2)} accent />
                    <SummaryMetric label="MV media" value={comparison.comparison.avg_mv.toFixed(2)} />
                    <SummaryMetric label="Giocatori" value={comparison.comparison.count} />
                  </div>
                </CardContent>
              </Card>

              <div
                className="grid gap-4 lg:grid-cols-2 xl:gap-5"
                style={{
                  gridTemplateColumns:
                    comparison.players.length === 3
                      ? undefined
                      : `repeat(${comparison.players.length}, minmax(0, 1fr))`,
                }}
              >
                {comparison.players.map((player) => (
                  <Card
                    key={player.id}
                    className={`border border-slate-700/80 bg-gradient-to-br from-[#101b34] to-[#0F172A] shadow-[0_14px_40px_rgba(0,0,0,0.12)] ${
                      comparison.players.length === 3 ? 'xl:col-span-1' : ''
                    }`}
                  >
                    <CardHeader className="border-b border-slate-800/70 px-5 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-3">
                          <div className="h-12 w-12 shrink-0 overflow-hidden rounded-full border border-sky-400/20 bg-slate-900/70">
                            <PlayerAvatar playerId={player.id} size="medium" />
                          </div>
                          <div className="min-w-0">
                            <CardTitle className="truncate text-base font-semibold text-slate-100">
                              {player.nome}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              {player.squadra}
                            </CardDescription>
                          </div>
                        </div>
                        <Badge variant={getRoleVariant(player.ruolo)}>
                          {player.ruolo}
                        </Badge>
                      </div>
                    </CardHeader>

                    <CardContent className="p-4">
                      <div className="space-y-2">
                        <ComparisonStat
                          label="Overall"
                          value={player.overall || 'N/A'}
                          highlight
                          best={
                            player.overall ===
                            Math.max(...comparison.players.map((p) => p.overall || 0))
                          }
                        />
                        <ComparisonStat
                          label="Fantamedia"
                          value={player.fm_weighted?.toFixed(2) || '-'}
                          best={
                            player.fm_weighted ===
                            Math.max(...comparison.players.map((p) => p.fm_weighted || 0))
                          }
                        />
                        <ComparisonStat
                          label="Media voto"
                          value={player.mv_weighted?.toFixed(2) || '-'}
                          best={
                            player.mv_weighted ===
                            Math.max(...comparison.players.map((p) => p.mv_weighted || 0))
                          }
                        />
                        <ComparisonStat
                          label="Prezzo %"
                          value={
                            player.price_percentage
                              ? `${player.price_percentage.toFixed(2)}%`
                              : '-'
                          }
                          inverse
                          best={
                            player.price_percentage ===
                            Math.min(
                              ...comparison.players
                                .filter((p) => p.price_percentage)
                                .map((p) => p.price_percentage)
                            )
                          }
                        />
                        <ComparisonStat
                          label="Crediti"
                          value={player.price_credits?.toFixed(1) || '-'}
                          inverse
                          best={
                            player.price_credits ===
                            Math.min(
                              ...comparison.players
                                .filter((p) => p.price_credits)
                                .map((p) => p.price_credits)
                            )
                          }
                        />
                        <ComparisonStat
                          label="Stagioni"
                          value={player.seasons_count || '-'}
                        />

                        {player.ruolo && player.ruolo.startsWith('P') ? (
                          <>
                            <ComparisonStat
                              label="Partite (Pv)"
                              value={player.pv_weighted?.toFixed(0) || '-'}
                              best={
                                player.pv_weighted ===
                                Math.max(
                                  ...comparison.players.map((p) => p.pv_weighted || 0)
                                )
                              }
                            />
                            <ComparisonStat
                              label="Gol subiti (Gs)"
                              value={player.gs_weighted?.toFixed(1) || '-'}
                              inverse
                              best={
                                player.gs_weighted ===
                                Math.min(
                                  ...comparison.players
                                    .filter((p) => p.gs_weighted)
                                    .map((p) => p.gs_weighted)
                                )
                              }
                            />
                            <ComparisonStat
                              label="Rigori parati (Rp)"
                              value={player.rp_weighted?.toFixed(1) || '-'}
                              best={
                                player.rp_weighted ===
                                Math.max(
                                  ...comparison.players.map((p) => p.rp_weighted || 0)
                                )
                              }
                            />
                          </>
                        ) : (
                          <>
                            <ComparisonStat
                              label="Partite (Pv)"
                              value={player.pv_weighted?.toFixed(0) || '-'}
                              best={
                                player.pv_weighted ===
                                Math.max(
                                  ...comparison.players.map((p) => p.pv_weighted || 0)
                                )
                              }
                            />
                            <ComparisonStat
                              label="Gol (Gf)"
                              value={player.gf_weighted?.toFixed(1) || '-'}
                              best={
                                player.gf_weighted ===
                                Math.max(
                                  ...comparison.players.map((p) => p.gf_weighted || 0)
                                )
                              }
                            />
                            <ComparisonStat
                              label="Assist"
                              value={player.ass_weighted?.toFixed(1) || '-'}
                              best={
                                player.ass_weighted ===
                                Math.max(
                                  ...comparison.players.map((p) => p.ass_weighted || 0)
                                )
                              }
                            />
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}

        

          {selectedCount > 0 && selectedCount < 3 && (
            <Card className="border border-violet-400/15 bg-[#0F172A]">
              <CardHeader className="px-5 pb-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet-400/15 bg-violet-400/[0.06] text-violet-300">
                    <Lightbulb className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-semibold text-slate-100">
                      Giocatori suggeriti
                    </CardTitle>
                    <CardDescription className="mt-1 text-xs text-slate-500">
                      Basato su similarità con i giocatori selezionati
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {loadingRecommendations ? (
                  <div className="py-6 text-center text-sm text-slate-500">
                    Caricamento suggerimenti...
                  </div>
                ) : recommendations.length > 0 ? (
                  <div className="grid gap-2.5 lg:grid-cols-2">
                    {recommendations.map((rec) => (
                      <button
                        type="button"
                        key={rec.id}
                        onClick={() => {
                          const emptySlot = selectedIds.findIndex((id) => !id);
                          if (emptySlot !== -1) selectPlayer(emptySlot, rec);
                        }}
                        className="group flex w-full items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-950/20 p-3.5 text-left transition-colors hover:border-violet-400/25 hover:bg-violet-400/[0.035]"
                      >
                        <div className="h-10 w-10 shrink-0 overflow-hidden rounded-full border border-violet-400/20 bg-slate-900/70">
                          <PlayerAvatar playerId={rec.id} size="small" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-semibold text-slate-100">
                            {rec.nome}
                          </div>
                          <div className="mt-1 truncate text-xs text-slate-500">
                            {rec.squadra} · {rec.ruolo} · Overall {rec.overall || 'N/A'}
                          </div>
                        </div>

                        <div className="hidden shrink-0 text-right sm:block">
                          <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">FM</div>
                          <div className="mt-0.5 text-sm font-semibold text-sky-300">
                            {rec.fm_weighted?.toFixed(2) || '-'}
                          </div>
                        </div>

                        {rec.similarity_score !== null && (
                          <Badge variant="outline" className="hidden shrink-0 sm:inline-flex">
                            {rec.similarity_score}
                          </Badge>
                        )}

                        <ChevronRight
                          className="h-4 w-4 shrink-0 text-slate-700 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-400"
                          aria-hidden="true"
                        />
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-sm text-slate-500">
                    Nessun suggerimento disponibile
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card className="border border-slate-700/70 bg-gradient-to-br from-[#0E1830] via-[#0F172A] to-[#0C1426]">
            <CardHeader className="px-5 pb-4 sm:px-6">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-400/20 bg-blue-400/[0.07] text-blue-300">
                  <BarChart3 className="h-4 w-4" aria-hidden="true" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold text-slate-100">Cosa puoi confrontare</CardTitle>
                  <CardDescription className="mt-1 text-xs text-slate-500">
                    Un confronto rapido dei principali indicatori disponibili.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="px-5 pb-5 sm:px-6">
              <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  [BarChart3, 'Statistiche', 'Statistiche chiave dei giocatori'],
                  [TrendingUp, 'Performance', 'Performance e indicatori ponderati'],
                  [Shield, 'Ruoli & Titolarità', 'Ruolo, impiego e affidabilità'],
                  [Star, 'Qualità / Prezzo', 'Rapporto tra valore e costo'],
                ].map(([Icon, title, description], index) => (
                  <div key={title} className="rounded-xl border border-slate-800/80 bg-slate-950/20 p-3.5">
                    <div className={`mb-2 flex h-9 w-9 items-center justify-center rounded-lg border ${
                      index === 0
                        ? 'border-sky-400/20 bg-sky-400/10 text-sky-300'
                        : index === 1
                          ? 'border-violet-400/20 bg-violet-400/10 text-violet-300'
                          : index === 2
                            ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300'
                            : 'border-amber-400/20 bg-amber-400/10 text-amber-300'
                    }`}>
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div className="text-xs font-semibold text-slate-200">{title}</div>
                    <div className="mt-1 text-[11px] leading-relaxed text-slate-500">{description}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}

function SummaryMetric({ label, value, accent = false }) {
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 px-4 py-4">
      <div className="text-[10px] font-medium uppercase tracking-[0.1em] text-slate-500">
        {label}
      </div>
      <div className={`mt-1 text-2xl font-bold ${accent ? 'text-sky-300' : 'text-slate-100'}`}>
        {value}
      </div>
    </div>
  );
}

function ComparisonStat({ label, value, highlight = false, best = false }) {
  return (
    <div
      className={`flex items-center justify-between gap-4 rounded-lg border px-3.5 py-2.5 ${
        best
          ? 'border-emerald-400/15 bg-emerald-400/[0.035]'
          : 'border-slate-800/70 bg-slate-950/20'
      }`}
    >
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span>{label}</span>
        {best && <Trophy className="h-3 w-3 text-emerald-300" aria-hidden="true" />}
      </div>
      <div
        className={`text-sm font-semibold ${
          highlight ? 'text-sky-300' : best ? 'text-emerald-300' : 'text-slate-200'
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function getRoleVariant(role) {
  const variants = { P: 'warning', D: 'success', C: 'default', A: 'destructive' };
  return variants[role] || 'secondary';
}

export default Compare;