import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Calendar,
  Gavel,
  Play,
  RotateCcw,
  RotateCw,
  Search,
  ShieldCheck,
  TrendingUp,
  Upload,
} from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select } from '../components/ui/select';
import { auctionApi, playersApi } from '../api/client';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { PlayerAvatar, TeamLogo } from '../components/common/PlayerMedia';

const RECOMMENDATION_LABELS = {
  STRONG_BUY: 'Ottimo prezzo',
  BID: 'Prezzo corretto',
  VALUE_ONLY: 'Solo al prezzo giusto',
  PASS: 'Lascia andare',
  INELIGIBLE: 'Non acquistabile',
};

const PURPOSE_LABELS = {
  STARTER: 'Titolare',
  COVERAGE: 'Copertura',
  HANDCUFF: 'Copertura stessa squadra',
  NO_FIT: 'Non adatto alla rosa',
};

const ROLE_LABELS = {
  ALL: 'Tutti i ruoli',
  P: 'Portieri',
  D: 'Difensori',
  C: 'Centrocampisti',
  A: 'Attaccanti',
};

const ROLE_SHORT = {
  P: 'P',
  D: 'D',
  C: 'C',
  A: 'A',
};

export default function Asta() {
  const [state, setState] = useState(null);
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [leagueSettings, setLeagueSettings] = useState(null);
  const [playerDetails, setPlayerDetails] = useState(null);
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [playerSearch, setPlayerSearch] = useState('');
  const [playerRole, setPlayerRole] = useState('ALL');
  const [selectedPlayerId, setSelectedPlayerId] = useState('');

  const [setupTeamNames, setSetupTeamNames] = useState('');
  const [setupTeamIndex, setSetupTeamIndex] = useState('0');
  const [useLeagueTeams, setUseLeagueTeams] = useState(false);
  const [leagueCalendar, setLeagueCalendar] = useState(null);
  const [policy, setPolicy] = useState('call');

  const [bidTeam, setBidTeam] = useState('');
  const [myTeamId, setMyTeamId] = useState('');
  const [bidPrice, setBidPrice] = useState('1');

  const refresh = async () => {
    try {
      setLoading(true);
      const [stateRes, playerRes, teamRes, settingsRes, calendarRes] = await Promise.all([
        auctionApi.getState(),
        // Usa ESATTAMENTE la stessa sorgente della pagina Giocatori, così
        // FM/MV/PV/Gol/Assist/Tit%/Prezzo e ruolo arrivano già completi.
        playersApi.getAll({ sort: 'Overall', order: 'desc' }),
        auctionApi.getTeams(),
        fetch('/api/settings').then(async (res) => {
          if (!res.ok) throw new Error('Impossibile leggere le impostazioni della lega.');
          return res.json();
        }),
        auctionApi.getLeagueCalendar().catch(() => {
          try {
            const saved = localStorage.getItem('simula_stagione_calendar');
            return { data: saved ? JSON.parse(saved) : null };
          } catch {
            return { data: null };
          }
        }),
      ]);

      const nextState = stateRes.data;
      const assignedIds = new Set(Object.keys(nextState.assigned || {}).map(Number));
      const activeId = Number(nextState.current_auction?.player_id || 0);
      const nextPlayers = (playerRes.data || []).map((player) => ({
        ...player,
        assigned: assignedIds.has(Number(player.id)),
        current_auction: Number(player.id) === activeId,
      }));
      const nextTeams = teamRes.data || [];
      const nextCalendar = calendarRes?.data || null;

      setState(nextState);
      setPlayers(nextPlayers);
      setTeams(nextTeams);
      setLeagueSettings(settingsRes);
      setLeagueCalendar(nextCalendar);
      setError(null);

      if (!setupTeamNames.trim() && settingsRes?.participants) {
        setSetupTeamNames(
          Array.from({ length: settingsRes.participants }, (_, i) => `Squadra ${i + 1}`).join('\n'),
        );
      }

      const current = nextState.current_auction;
      if (current) {
        const nextMinimum = current.last_bidder
          ? Number(current.current_price) + 1
          : Number(current.current_price || 1);
        setBidPrice(String(Math.max(1, nextMinimum)));
      } else {
        setBidPrice('1');
      }

      setBidTeam((currentTeam) => currentTeam || nextTeams[0]?.id || '');
      setMyTeamId((currentTeam) => currentTeam || nextTeams[0]?.id || '');
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const current = state?.current_auction;
  const auctionStarted = Boolean(state?.phase && state.phase !== 'NOT_STARTED');
  const currentPlayer = current ? players.find((p) => p.id === current.player_id) : null;
  const winningTeam = current?.last_bidder
    ? teams.find((team) => team.id === current.last_bidder)
    : null;

  const phaseRole = String(state?.phase || '').startsWith('ROLE_')
    ? String(state.phase).replace('ROLE_', '')
    : null;
  const effectivePlayerRole = phaseRole || playerRole;

  const filteredPlayers = useMemo(() => {
    const query = playerSearch.trim().toLowerCase();
    return players
      .filter((player) => {
        if (player.assigned) return false;
        if (effectivePlayerRole !== 'ALL' && !String(player.ruolo || '').toUpperCase().startsWith(effectivePlayerRole)) {
          return false;
        }
        if (!query) return true;
        return (
          String(player.nome || '').toLowerCase().includes(query) ||
          String(player.squadra || '').toLowerCase().includes(query)
        );
      })
      .sort((a, b) => Number(b.overall || 0) - Number(a.overall || 0));
  }, [players, effectivePlayerRole, playerSearch]);

  const myTeam = myTeamId ? teams.find((team) => team.id === myTeamId) : null;
  const nextRoleSlots = phaseRole && myTeam
    ? Number(myTeam.slots_remaining?.[phaseRole] || 0)
    : null;
  const roleProgressLabel = phaseRole && nextRoleSlots != null
    ? `${phaseRole}: ${nextRoleSlots} per il prossimo ruolo`
    : null;

  const action = async (fn) => {
    try {
      await fn();
      await refresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  useEffect(() => {
    if (!currentPlayer?.id) {
      setPlayerDetails(null);
      return undefined;
    }

    let alive = true;
    setDetailsLoading(true);
    const budget = Number(state?.rules?.starting_credits || leagueSettings?.budget || 500);

    playersApi
      .getById(currentPlayer.id, budget)
      .then((res) => {
        if (alive) setPlayerDetails(res.data);
      })
      .catch(() => {
        if (alive) setPlayerDetails(null);
      })
      .finally(() => {
        if (alive) setDetailsLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [currentPlayer?.id, state?.rules?.starting_credits, leagueSettings?.budget]);

  const advisoryPlayerId = currentPlayer?.id || (selectedPlayerId ? Number(selectedPlayerId) : null);
  // L'Advisor valuta sempre la prossima offerta che l'utente può effettuare.
  // Questo rende percentuale, barra e decisione realmente reattive mentre il prezzo sale.
  const advisorPriceInput = Math.max(1, Number(bidPrice || current?.current_price || 1));

  useEffect(() => {
    // Il motore strategico dipende SOLO dalla mia squadra. Il bidder operativo
    // serve per l'assegnazione e NON entra mai nella chiave dell'Advisor.
    if (!advisoryPlayerId || !myTeamId || !auctionStarted) {
      setAdvice(null);
      return undefined;
    }

    let alive = true;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setAdviceLoading(true);

      auctionApi
        .advice(advisoryPlayerId, myTeamId, advisorPriceInput, controller.signal)
        .then((res) => {
          if (alive) setAdvice(res.data);
        })
        .catch((err) => {
          if (!alive || err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError') return;
          setAdvice({
            recommendation: 'ERROR',
            purpose: 'ERROR',
            reasons: [err.response?.data?.detail || err.message],
            risks: [],
            alternatives: [],
            idealMin: 0,
            idealMax: 0,
            maxBid: 0,
            legalMax: 0,
          });
        })
        .finally(() => {
          if (alive) setAdviceLoading(false);
        });
    }, 250);

    return () => {
      alive = false;
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [
    advisoryPlayerId,
    myTeamId,
    auctionStarted,
    advisorPriceInput,
  ]);

  const effectiveSetupTeamNames = useLeagueTeams && leagueCalendar?.teams?.length
    ? leagueCalendar.teams.join('\n')
    : setupTeamNames;

  const setupTeamOptions = effectiveSetupTeamNames
    .split(/\n|,/)
    .map((value) => value.trim())
    .filter(Boolean);

  const initialize = async () => {
    const names = setupTeamOptions;

    if (!names.length) {
      setError(useLeagueTeams ? 'Nessun calendario lega disponibile. Carica un calendario oppure inserisci manualmente le squadre.' : 'Inserisci almeno una squadra.');
      return false;
    }

    try {
      setError(null);
      const selectedIndex = Math.max(0, Math.min(Number(setupTeamIndex) || 0, names.length - 1));
      const selectedTeamId = `team_${selectedIndex + 1}`;

      await auctionApi.initialize({
        team_names: names,
        starting_credits: Number(leagueSettings?.budget || 500),
        composition: leagueSettings?.roster_composition,
        minimum_price: 1,
        bid_increment: 1,
        reserve_per_slot: 1,
        call_policy: policy,
      });
      setMyTeamId(selectedTeamId);
      setBidTeam((currentBidTeam) => currentBidTeam || selectedTeamId);
      await refresh();
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      return false;
    }
  };

  const startAuction = async () => {
    await action(auctionApi.start);
    setPlayerSearch('');
    setPlayerRole('ALL');
  };

  const saveAndStartAuction = async () => {
    const initialized = await initialize();
    if (!initialized) return;

    try {
      await action(auctionApi.start);
      setPlayerSearch('');
      setPlayerRole('ALL');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const handleUploadLeagueCalendar = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setError(null);
      const data = await auctionApi.uploadLeagueCalendar(file);
      setLeagueCalendar(data);
      localStorage.setItem('simula_stagione_calendar', JSON.stringify(data));
      localStorage.setItem('asta_league_calendar', JSON.stringify(data));
      setUseLeagueTeams(true);
      setSetupTeamIndex('0');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Errore upload calendario.');
    } finally {
      event.target.value = '';
    }
  };

  const handleDeleteLeagueCalendar = () => {
    localStorage.removeItem('asta_league_calendar');
    setLeagueCalendar(null);
    setUseLeagueTeams(false);
    setSetupTeamIndex('0');
  };

  const newAuction = async () => {
    const confirmed = window.confirm("Vuoi cancellare l'asta corrente e crearne una nuova?");
    if (!confirmed) return;

    try {
      setError(null);
      await auctionApi.reset();
      setState(null);
      setPlayers([]);
      setTeams([]);
      setPlayerDetails(null);
      setAdvice(null);
      setSelectedPlayerId('');
      setPlayerSearch('');
      setPlayerRole('ALL');
      setBidTeam('');
      setMyTeamId('');
      setBidPrice('1');
      await refresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const callPlayer = async (playerId) => {
    if (!playerId) return;
    setSelectedPlayerId(String(playerId));
    await action(() => auctionApi.open(Number(playerId)));
    setPlayerSearch('');
  };

  const placeQuickBid = async (extra) => {
    if (!bidTeam || !current) return;

    const currentPrice = Math.max(1, Number(current.current_price || 1));
    const hasBidder = Boolean(current.last_bidder);
    const minimumNextBid = hasBidder
      ? currentPrice + Math.max(1, Number(state?.rules?.bid_increment || 1))
      : currentPrice;
    const quickBid = Math.max(1, minimumNextBid + Number(extra || 0));

    setBidPrice(String(quickBid));
    await action(() => auctionApi.bid(bidTeam, quickBid));
  };

  const nextBid = Math.max(1, Number(bidPrice || 1));
  const currentAuctionPrice = Math.max(1, Number(current?.current_price || 1));
  const maxBid = Number(advice?.maxBid || 0);
  const gaugeWidth = maxBid > 0 ? Math.min(100, Math.max(0, (nextBid / maxBid) * 100)) : 0;
  const humanVerdict = advice ? humanizeVerdict(advice.recommendation) : 'Calcolo…';
  const actionHint = getActionHint(advice?.recommendation, nextBid, Number(advice?.maxBid || 0));
  const marginalPct = Number(advice?.summary?.marginalGainPercentage);
  const marginalDisplay = Number.isFinite(marginalPct) ? `${marginalPct >= 0 ? '+' : ''}${marginalPct.toFixed(1)}%` : '—';
  const minimumBidForGauge = Math.max(1, Number(state?.rules?.minimum_price || 1));
  const localHeadroomCredits = maxBid > 0 ? Math.max(0, maxBid - nextBid) : 0;
  const localPriceSpan = maxBid > minimumBidForGauge
    ? (maxBid - minimumBidForGauge)
    : 0;
  const localHeadroomPercentage = localPriceSpan > 0
    ? Math.min(100, Math.max(0, (localHeadroomCredits / localPriceSpan) * 100))
    : 0;
  const priceHeadroomCredits = Number.isFinite(Number(advice?.summary?.priceHeadroomCredits))
    ? Number(advice.summary.priceHeadroomCredits)
    : localHeadroomCredits;
  const priceHeadroomPercentage = localPriceSpan > 0
    ? localHeadroomPercentage
    : Number(advice?.summary?.priceHeadroomPercentage || 0);
  const marginalLevel = advice?.summary?.marginalGainLevel || 'NULLO';
  const dynamicHeadroom = localHeadroomPercentage;
  const marginalToneClass = {
    ECCEZIONALE: 'text-emerald-300',
    FORTE: 'text-cyan-300',
    MEDIO: 'text-amber-300',
    BASSO: 'text-orange-300',
    NULLO: 'text-red-300',
  }[marginalLevel] || 'text-slate-200';
  const priceGuidanceTitle = getPriceGuidanceTitle(nextBid, advice);
  const priceGuidanceText = getPriceGuidanceText(nextBid, advice);
  const priceGaugeWidth = Number(advice?.maxBid || 0) > 0 ? Math.min(100, Math.max(0, (nextBid / Number(advice.maxBid)) * 100)) : 0;
  const demandLabel = describeDemand(advice?.summary?.opponentDemand);
  const scarcityLabel = describeScarcity(advice?.summary?.validAlternativesCount ?? advice?.summary?.roleAlternativeCount ?? advice?.summary?.alternativesCount, advice?.summary?.roleSupply);
  const inflationLabel = describeInflation(advice?.summary?.marketInflation);
  const riskLabel = describeRisk(advice);

  const purpose = advice ? PURPOSE_LABELS[advice.purpose] || advice.purpose : '—';

  if (loading && !state) {
    return <LoadingState message="Caricamento asta..." className="py-16" />;
  }

  if (error && !state) {
    return <ErrorState title="Errore modalità Asta" message={error} onRetry={refresh} className="py-16" />;
  }

  // Prima schermata: configurazione. La schermata operativa compare solo dopo Avvia.
  if (!auctionStarted) {
    return (
      <div className="min-h-full bg-[#0B0E14] text-slate-100">
        <div className="mx-auto w-full max-w-[1100px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <PageHeader
            title="Configura asta"
            description="Imposta la lega prima di iniziare la gestione dell'asta."
            actions={
              <Button variant="outline" onClick={refresh} disabled={loading}>
                Aggiorna
              </Button>
            }
          />

          {error && (
            <div className="mb-5 rounded-xl border border-red-400/20 bg-red-400/[0.06] p-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <Card className="overflow-hidden border-cyan-400/15 bg-[#0F172A] shadow-2xl shadow-black/20">
            <div className="h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/50 to-transparent" />
            <CardHeader className="pb-4">
              <CardTitle className="text-xl text-slate-50">Configurazione iniziale</CardTitle>
              <p className="mt-1 text-sm text-slate-500">
                Budget, partecipanti e composizione vengono letti direttamente dalle Impostazioni.
                L'offerta base parte sempre da 1 credito e l'incremento standard è 1.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <label className="block text-sm font-medium text-slate-300">Squadre</label>
                    <p className="mt-1 text-xs text-slate-500">
                      Puoi usare i nomi inseriti manualmente oppure caricare qui il calendario personale della lega.
                    </p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={useLeagueTeams}
                    onClick={() => {
                      setUseLeagueTeams((value) => !value);
                      setSetupTeamIndex('0');
                    }}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold transition ${
                      useLeagueTeams
                        ? 'border-cyan-400/40 bg-cyan-400/[0.08] text-cyan-200'
                        : 'border-slate-700 bg-slate-950/70 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <span className={`h-2.5 w-2.5 rounded-full ${useLeagueTeams ? 'bg-cyan-300' : 'bg-slate-600'}`} />
                    {useLeagueTeams ? 'ON · Calendario lega' : 'OFF · Inserimento manuale'}
                  </button>
                </div>

                {useLeagueTeams ? (
                  <div className="mt-3 rounded-xl border border-cyan-400/15 bg-cyan-400/[0.035] p-4">
                    {leagueCalendar?.teams?.length ? (
                      <>
                        <div className="mb-3 text-xs text-slate-400">
                          Calendario disponibile: <span className="font-semibold text-slate-200">{leagueCalendar.teams.length} squadre</span> · {leagueCalendar.total_matchdays || 0} giornate
                        </div>
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                          {leagueCalendar.teams.map((team) => (
                            <div key={team} className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-200">
                              {team}
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="text-sm text-amber-200">
                        Nessun calendario lega disponibile. Caricalo qui sotto.
                      </div>
                    )}
                  </div>
                ) : (
                  <textarea
                    className="mt-3 min-h-36 w-full rounded-xl border border-slate-700 bg-slate-950/70 p-4 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-400/40"
                    value={setupTeamNames}
                    onChange={(event) => setSetupTeamNames(event.target.value)}
                    placeholder="Una squadra per riga"
                  />
                )}
              </div>

              <Card className="border-slate-800/90 bg-slate-950/30">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-sky-300" />
                    Calendario lega personale
                  </CardTitle>
                  <p className="text-xs text-slate-500">
                    Facoltativo per l'asta. Se lo carichi, l'Advisor può usarlo per analizzare rotazioni e calendario anche senza eseguire Simula Stagione.
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {leagueCalendar ? (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.04] p-5">
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.08] text-emerald-300">
                              <Calendar className="h-5 w-5" />
                            </div>
                            <div>
                              <div className="text-sm font-semibold text-slate-100">Calendario caricato</div>
                              <div className="mt-1 text-xs text-slate-500">
                                {leagueCalendar.teams?.length || 0} squadre · {leagueCalendar.total_matchdays || 0} giornate
                              </div>
                            </div>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            onClick={handleDeleteLeagueCalendar}
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
                            <div className="text-sm font-semibold text-slate-200">Carica un nuovo calendario</div>
                            <div className="mt-1 text-xs text-slate-500">Sostituirà il calendario attuale</div>
                          </div>
                        </div>
                        <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2.5 transition hover:border-sky-400/35 hover:bg-slate-950">
                          <span className="truncate text-sm text-slate-500">Seleziona nuovo file</span>
                          <span className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-sky-400/25 bg-sky-400/[0.06] px-3 py-1.5 text-xs font-semibold text-sky-300">
                            <Upload className="h-3.5 w-3.5" />
                            Scegli file
                          </span>
                          <input type="file" accept=".xlsx,.xls,.csv" onChange={handleUploadLeagueCalendar} className="sr-only" />
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
                          <div className="text-sm font-semibold text-slate-200">Seleziona calendario</div>
                          <div className="mt-1 text-xs text-slate-500">XLSX, XLS o CSV</div>
                        </div>
                      </div>
                      <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2.5 transition hover:border-sky-400/35 hover:bg-slate-950">
                        <span className="truncate text-sm text-slate-500">Nessun file selezionato</span>
                        <span className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-sky-400/25 bg-sky-400/[0.06] px-3 py-1.5 text-xs font-semibold text-sky-300">
                          <Upload className="h-3.5 w-3.5" />
                          Scegli file
                        </span>
                        <input type="file" accept=".xlsx,.xls,.csv" onChange={handleUploadLeagueCalendar} className="sr-only" />
                      </label>
                    </div>
                  )}
                </CardContent>
              </Card>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">La tua squadra</label>
                <Select
                  value={setupTeamIndex}
                  onChange={(event) => setSetupTeamIndex(event.target.value)}
                  disabled={!setupTeamOptions.length}
                  className="h-11 border-slate-700 bg-slate-950 text-slate-100 [&>option]:bg-slate-950 [&>option]:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {setupTeamOptions.map((name, index) => (
                    <option key={`${index}-${name}`} value={index}>
                      {name}
                    </option>
                  ))}
                </Select>
                <p className="mt-1.5 text-xs text-slate-500">L'Advisor calcola e ottimizza esclusivamente la rosa di questa squadra.</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <InfoField label="Budget per squadra" value={`${leagueSettings?.budget ?? '—'} crediti`} />
                <InfoField label="Partecipanti" value={leagueSettings?.participants ?? '—'} />
                <InfoField
                  label="Composizione"
                  value={
                    leagueSettings?.roster_composition
                      ? Object.entries(leagueSettings.roster_composition)
                          .map(([role, count]) => `${ROLE_SHORT[role] || role}: ${count}`)
                          .join(' · ')
                      : '—'
                  }
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-1">
                <InfoField label="Offerta base" value="1 credito" />
              </div>

              <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300">Modalità chiamata</label>
                  <Select
                    value={policy}
                    onChange={(event) => setPolicy(event.target.value)}
                    className="border-slate-700 bg-slate-950 text-slate-100 [&>option]:bg-slate-950 [&>option]:text-slate-100"
                  >
                    <option value="call">Chiamata libera</option>
                    <option value="call_by_role">Per ruolo</option>
                    <option value="random">Casuale</option>
                    <option value="random_by_role">Casuale per ruolo</option>
                    <option value="alphabetical">Alfabetica</option>
                    <option value="alphabetical_by_role">Alfabetica per ruolo</option>
                  </Select>
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <Button variant="outline" onClick={initialize}>
                    <ShieldCheck className="h-4 w-4" /> Salva configurazione
                  </Button>
                  <Button onClick={saveAndStartAuction} disabled={!setupTeamOptions.length || (useLeagueTeams && !leagueCalendar?.teams?.length)}>
                    <Play className="h-4 w-4" /> Salva e avvia
                  </Button>
                </div>
              </div>


            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14] text-slate-100">
      <div className="mx-auto w-full max-w-[1550px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
        <PageHeader
          title="Asta"
          description="Gestione dell'asta, rilanci e advisor dinamico"
          actions={
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={newAuction}
                className="border-red-400/30 bg-red-400/[0.05] text-red-200 hover:border-red-400/50 hover:bg-red-400/[0.09]"
              >
                <RotateCcw className="h-4 w-4" /> Nuova asta
              </Button>
              <Button variant="outline" onClick={() => setState((prev) => prev)}>
                <Badge variant="outline">{roleProgressLabel || state?.phase}</Badge>
              </Button>
              <Button variant="outline" onClick={() => action(auctionApi.undo)} disabled={!state?.history?.length}>
                <RotateCcw className="h-4 w-4" /> Undo
              </Button>
              <Button variant="outline" onClick={() => action(auctionApi.redo)} disabled={!state?.redo?.length}>
                <RotateCw className="h-4 w-4" /> Redo
              </Button>
            </div>
          }
        />

        {error && (
          <div className="mb-5 rounded-xl border border-red-400/20 bg-red-400/[0.06] p-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {/* Ricerca del giocatore da chiamare */}
        <Card className="mb-5 overflow-hidden border-violet-400/15 bg-[#0F172A]">
          <div className="h-0.5 bg-gradient-to-r from-violet-400/70 via-sky-400/50 to-transparent" />
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg text-slate-50">
              <Search className="h-4 w-4 text-cyan-300" /> Chiama giocatore
            </CardTitle>
            <p className="text-sm text-slate-500">Cerca il giocatore da mettere in asta e filtra per ruolo.</p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 lg:grid-cols-[1fr_210px]">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input
                  value={playerSearch}
                  onChange={(event) => setPlayerSearch(event.target.value)}
                  placeholder="Cerca giocatore o squadra..."
                  className="h-11 border-slate-700 bg-slate-950 pl-9 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400/40 focus:ring-cyan-400/20"
                />
              </div>
              <Select
                value={effectivePlayerRole}
                onChange={(event) => setPlayerRole(event.target.value)}
                disabled={Boolean(phaseRole)}
                className="h-11 border-slate-700 bg-slate-950 text-slate-100 [&>option]:bg-slate-950 [&>option]:text-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {Object.entries(ROLE_LABELS).map(([role, label]) => (
                  <option key={role} value={role}>{label}</option>
                ))}
              </Select>
            </div>

            <div className="mt-3 max-h-[375px] overflow-y-auto overflow-x-auto rounded-2xl border border-slate-800/80 bg-[#0F172A]/85 overscroll-contain" style={{ scrollbarGutter: 'stable' }}>
              <ResponsiveTable
                caption="Elenco giocatori disponibili per la chiamata"
                mobileContent={
                  <div className="space-y-3 p-3">
                    {filteredPlayers.map((player) => (
                      <div
                        key={player.id}
                        className="block w-full rounded-2xl border border-slate-800 bg-[#0F172A]/85 p-4 text-left transition-all hover:border-sky-400/20 hover:bg-slate-900/80"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex min-w-0 items-center gap-3">
                            <PlayerAvatar playerId={player.id} size="medium" />
                            <div className="min-w-0">
                              <div className="truncate text-[15px] font-semibold text-slate-100">{player.nome}</div>
                              <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                                <TeamLogo teamName={player.squadra} size={20} />
                                <span>{player.squadra}</span>
                              </div>
                            </div>
                          </div>
                          <Button size="sm" onClick={() => callPlayer(player.id)} className="shrink-0">
                            Chiama
                          </Button>
                        </div>

                        <div className="mt-4 grid grid-cols-4 gap-2 border-t border-slate-800/70 pt-3">
                          <div>
                            <div className="text-[10px] uppercase tracking-wider text-slate-600">OVR</div>
                            <div className="mt-1 text-lg font-bold text-sky-400">{player.overall || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-[10px] uppercase tracking-wider text-slate-600">FM</div>
                            <div className="mt-1 text-sm font-semibold text-slate-200">{player.fm_weighted?.toFixed(2) || '-'}</div>
                          </div>
                          <div>
                            <div className="text-[10px] uppercase tracking-wider text-slate-600">Prezzo</div>
                            <div className="mt-1 text-sm font-semibold text-amber-400">{player.price_percentage?.toFixed(1) || '-'}%</div>
                          </div>
                          <div className="flex items-end justify-end pb-0.5">
                            <Badge variant="secondary">{player.ruolo || '-'}</Badge>
                          </div>
                        </div>

                        <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                          <span>MV {player.mv_weighted?.toFixed(2) || '-'}</span>
                          <span>PV {player.pv_weighted?.toFixed(1) || '-'}</span>
                          <span>Gol {player.gf_weighted?.toFixed(1) || '-'}</span>
                          <span>Assist {player.ass_weighted?.toFixed(1) || '-'}</span>
                        </div>
                      </div>
                    ))}
                    {!filteredPlayers.length && (
                      <div className="px-4 py-8 text-center text-sm text-slate-400">Nessun giocatore disponibile.</div>
                    )}
                  </div>
                }
              >
                <thead>
                  <tr>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">OVR</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Nome</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Squadra</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Ruolo</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">FM</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">MV</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">PV</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Gol</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Assist</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Tit%</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Prezzo %</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Crediti</th>
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Azione</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlayers.map((player) => (
                    <tr key={player.id} className="border-b border-slate-800/60 transition-colors hover:bg-slate-900/70">
                      <td className="px-3 py-3.5 text-base font-bold text-sky-400">{player.overall || 'N/A'}</td>
                      <td className="px-3 py-3.5">
                        <div className="flex items-center gap-3">
                          <PlayerAvatar playerId={player.id} size="small" />
                          <div className="min-w-0">
                            <div className="truncate font-semibold text-slate-100">{player.nome}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3.5">
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                          <TeamLogo teamName={player.squadra} size={24} />
                          <span>{player.squadra}</span>
                        </div>
                      </td>
                      <td className="px-3 py-3.5 text-sm font-medium text-slate-200">{player.ruolo || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-slate-100">{player.fm_weighted?.toFixed(2) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.mv_weighted?.toFixed(2) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.pv_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.gf_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.ass_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.titolarita != null ? `${Number(player.titolarita).toFixed(0)}%` : '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_percentage != null ? `${Number(player.price_percentage).toFixed(1)}%` : '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_credits != null ? Number(player.price_credits).toFixed(0) : '-'}</td>
                      <td className="px-3 py-3.5 text-right">
                        <Button size="sm" onClick={() => callPlayer(player.id)}>Chiama</Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </ResponsiveTable>
            </div>
            {roleProgressLabel && (
              <div className="mt-2 text-xs text-slate-500">{roleProgressLabel}</div>
            )}
          </CardContent>
        </Card>

        <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
          <Card className="overflow-hidden border-cyan-400/15 bg-[#0F172A] shadow-xl shadow-black/10">
            <div className="h-0.5 bg-gradient-to-r from-sky-400/80 via-cyan-400/30 to-transparent" />
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-lg text-slate-50">Giocatore in asta</CardTitle>
                  {currentPlayer && (
                    <div className="mt-1 text-xs text-slate-500">
                      {currentPlayer.ruolo} · {currentPlayer.squadra}
                    </div>
                  )}
                </div>
                <Badge variant="outline" className="border-cyan-400/20 bg-cyan-400/[0.05] text-cyan-300">
                  {state?.phase}
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              {currentPlayer ? (
                <div className="space-y-5">
                  <div className="rounded-2xl border border-slate-700/80 bg-slate-950/65 p-5">
                    <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
                      <div className="min-w-0">
                        <div className="mb-2 flex items-center gap-2">
                          <Badge className="border border-emerald-400/15 bg-emerald-400/[0.08] text-emerald-300">
                            {ROLE_LABELS[currentPlayer.ruolo] || currentPlayer.ruolo}
                          </Badge>
                          {currentPlayer.squadra && <span className="text-xs text-slate-500">{currentPlayer.squadra}</span>}
                        </div>
                        <div className="truncate text-3xl font-semibold tracking-tight text-slate-50">{currentPlayer.nome}</div>
                        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                          <span className="text-slate-500">Prezzo attuale</span>
                          <span className="rounded-lg border border-cyan-400/20 bg-cyan-400/[0.07] px-3 py-1.5 text-lg font-bold text-cyan-300">
                            {currentAuctionPrice} cr
                          </span>
                          {winningTeam && (
                            <span className="text-slate-500">
                              Ultimo offerente: <strong className="text-slate-300">{winningTeam.name}</strong>
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:min-w-[520px]">
                        <PlayerStat label="OVERALL" value={playerDetails?.overall ?? currentPlayer.overall ?? '—'} accent />
                        <PlayerStat label="FM" value={formatStat(playerDetails?.fm_weighted, 2)} />
                        <PlayerStat label="MV" value={formatStat(playerDetails?.mv_weighted, 2)} />
                        <PlayerStat label="TITOLARITÀ" value={formatPercent(playerDetails?.titolarita)} />
                      </div>
                    </div>
                    {detailsLoading && (
                      <div className="mt-3 text-xs text-slate-600">Aggiornamento statistiche giocatore...</div>
                    )}
                  </div>

                  <div className="grid gap-4 lg:grid-cols-[1fr_1.15fr]">
                    <div className="rounded-xl border border-slate-800 bg-slate-950/45 p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Offerta</div>
                          <div className="mt-1 text-2xl font-bold text-slate-50">{nextBid} cr</div>
                        </div>
                        <div className="text-right text-xs text-slate-500">
                          <div>Base</div>
                          <div className="font-semibold text-slate-300">1 cr</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <Button
                          variant="outline"
                          className="h-11 border-cyan-400/20 bg-cyan-400/[0.04] text-cyan-300 hover:bg-cyan-400/[0.08]"
                          onClick={() => placeQuickBid(1)}
                        >
                          +1
                        </Button>
                        <Button
                          variant="outline"
                          className="h-11 border-violet-400/20 bg-violet-400/[0.04] text-violet-300 hover:bg-violet-400/[0.08]"
                          onClick={() => placeQuickBid(5)}
                        >
                          +5
                        </Button>
                      </div>

                      <div className="mt-3 flex items-end gap-2">
                        <div className="min-w-0 flex-1">
                          <label className="mb-1.5 block text-xs font-medium text-slate-500">Nuova offerta</label>
                          <Input
                            type="number"
                            min="1"
                            step="1"
                            value={bidPrice}
                            onChange={(event) => setBidPrice(event.target.value)}
                            className="h-11 border-slate-700 bg-slate-950 text-slate-100"
                          />
                        </div>
                        <Button
                          className="h-11 min-w-[120px]"
                          disabled={!bidTeam}
                          onClick={() => action(() => auctionApi.bid(bidTeam, Number(bidPrice)))}
                        >
                          <Gavel className="h-4 w-4" /> Rilancia
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-950/45 p-4">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Assegnazione giocatore</div>
                          <div className="mt-1 text-sm text-slate-400">Solo per assegnare il giocatore. Non modifica i calcoli dell'Advisor.</div>
                        </div>
                        {bidTeam && (
                          <Badge variant="outline" className="border-slate-700 bg-slate-900/70 text-slate-300">
                            {teams.find((team) => team.id === bidTeam)?.name || '—'}
                          </Badge>
                        )}
                      </div>

                      <Select
                        value={bidTeam}
                        onChange={(event) => setBidTeam(event.target.value)}
                        className="h-11 border-slate-700 bg-slate-950 text-slate-100 [&>option]:bg-slate-950 [&>option]:text-slate-100"
                      >
                        {teams.map((team) => (
                          <option key={team.id} value={team.id}>{team.name}</option>
                        ))}
                      </Select>

                      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-400/15 bg-amber-400/[0.03] p-3">
                        <div>
                          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Assegnazione</div>
                          <div className="mt-1 text-sm text-slate-300">
                            {winningTeam ? `${winningTeam.name} · ${currentAuctionPrice} crediti` : 'Nessun offerente'}
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          disabled={!winningTeam}
                          onClick={() => action(auctionApi.assign)}
                          className="border-amber-400/20 bg-amber-400/[0.04] text-amber-200 hover:bg-amber-400/[0.08]"
                        >
                          Assegna a {winningTeam?.name || '—'}
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-cyan-400/15 bg-cyan-400/[0.025] p-4">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-cyan-300" />
                        <span className="text-sm font-semibold text-slate-100">Advisor asta</span>
                      </div>
                      {adviceLoading && <span className="text-xs text-slate-500">calcolo...</span>}
                    </div>

                    {advice && (
                      advice.recommendation === 'ERROR' ? (
                        <div className="rounded-2xl border border-red-400/20 bg-red-400/[0.04] p-4">
                          <div className="text-base font-semibold text-red-200">Advisor non disponibile</div>
                          <div className="mt-1 text-sm leading-6 text-slate-400">{advice.reasons?.[0] || 'Il motore non ha restituito una valutazione.'}</div>
                        </div>
                      ) : (
                        <>
                          <div className="grid gap-3 lg:grid-cols-[1.35fr_0.8fr_0.8fr]">
                            <div className="rounded-2xl border border-cyan-400/20 bg-slate-950/55 p-5">
                              <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Decisione</div>
                              <div className="mt-2 flex flex-wrap items-end gap-3">
                                <div className="text-3xl font-black tracking-tight text-slate-50">{humanVerdict}</div>
                                <div className="pb-1 text-sm font-medium text-slate-400">{priceGuidanceTitle}</div>
                              </div>
                              <div className="mt-2 text-sm leading-6 text-slate-300">{actionHint}</div>
                              <div className="mt-4 flex flex-wrap items-center gap-3">
                                <span className="rounded-lg border border-cyan-400/15 bg-cyan-400/[0.06] px-3 py-2 text-sm font-semibold text-cyan-200">Prezzo attuale: {currentAuctionPrice} cr</span>
                                <span className={`rounded-lg border px-3 py-2 text-sm font-semibold ${nextBid > Number(advice.maxBid || 0) ? 'border-red-400/20 bg-red-400/[0.05] text-red-200' : 'border-slate-700 bg-slate-900/60 text-slate-200'}`}>Prossima: {nextBid} cr</span>
                              </div>
                            </div>

                            <div className="rounded-2xl border border-slate-800 bg-slate-950/45 p-5">
                              <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Tuo limite</div>
                              <div className="mt-2 text-3xl font-black text-red-300">{advice.maxBid ?? 0} cr</div>
                              <div className="mt-2 text-sm leading-5 text-slate-400">Oltre questo prezzo il piano alternativo diventa migliore.</div>
                            </div>

                            <div className="rounded-2xl border border-slate-800 bg-slate-950/45 p-5">
                              <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Fascia ideale</div>
                              <div className="mt-2 text-3xl font-black text-emerald-300">{advice.idealMin ?? 0}–{advice.idealMax ?? 0} cr</div>
                              <div className="mt-2 text-sm leading-5 text-slate-400">Qui il rapporto tra valore e prezzo è più favorevole.</div>
                            </div>
                          </div>

                          <div className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/45 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Quanto margine hai a {nextBid} cr?</div>
                                <div className="mt-1 flex flex-wrap items-baseline gap-2">
                                  <span className="text-xl font-black text-cyan-300">
                                    {Number.isFinite(priceHeadroomPercentage) ? `${priceHeadroomPercentage.toFixed(0)}%` : '—'}
                                  </span>
                                  <span className="text-sm font-semibold text-slate-300">del margine di prezzo che ti resta</span>
                                </div>
                              </div>
                              <div className="text-right text-xs text-slate-500">Si aggiorna a ogni rilancio</div>
                            </div>
                            <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-800">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-red-400 transition-all duration-300"
                                style={{ width: `${dynamicHeadroom}%` }}
                              />
                            </div>
                            <div className="mt-2 flex justify-between text-[11px] text-slate-500">
                              <span>Limite raggiunto</span>
                              <span>{Number.isFinite(priceHeadroomPercentage) ? `${priceHeadroomPercentage.toFixed(0)}% di margine` : '—'}</span>
                              <span>Massimo margine</span>
                            </div>
                            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                              <span>Ti restano <strong className="text-cyan-300">{Number.isFinite(priceHeadroomCredits) ? `${priceHeadroomCredits.toFixed(0)} cr` : '—'}</strong> prima del tuo limite.</span>
                              <span>Incremento della rosa rispetto all'alternativa senza questo giocatore: <strong className={marginalToneClass}>{marginalDisplay}</strong></span>
                            </div>
                          </div>
                          <div className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/45 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Cosa succede se il prezzo sale?</div>
                                <div className="mt-1 text-sm font-semibold text-slate-200">{priceGuidanceText}</div>
                              </div>
                              {adviceLoading && <span className="text-xs font-semibold text-cyan-300">Aggiornamento…</span>}
                            </div>
                            <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-800">
                              <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-red-400 transition-all duration-300" style={{ width: `${priceGaugeWidth}%` }} />
                            </div>
                            <div className="mt-2 grid grid-cols-3 text-[11px]">
                              <div className="text-left text-slate-500">Ideale <strong className="text-emerald-300">{advice.idealMin ?? 0}–{advice.idealMax ?? 0}</strong></div>
                              <div className="text-center text-slate-500">Mercato <strong className="text-cyan-300">{advice.summary?.estimatedMarketPrice ?? '—'}</strong></div>
                              <div className="text-right text-slate-500">STOP <strong className="text-red-300">{advice.maxBid ?? 0}</strong></div>
                            </div>
                          </div>

                          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                            <SimpleAdviceCard label="Valore teorico" value={`${advice.summary?.sourcePriceCredits ?? '—'} cr`} help="Stima del modello prima del mercato." />
                            <SimpleAdviceCard label="Mercato atteso" value={`${advice.summary?.estimatedMarketPrice ?? '—'} cr`} help={inflationLabel} />
                            <SimpleAdviceCard label="Categoria" value={advice.summary?.tier || '—'} help="Fascia del giocatore nel suo ruolo." />
                            <SimpleAdviceCard label="Alternative valide" value={scarcityLabel} help={`${advice.summary?.roleSupply ?? '—'} giocatori del ruolo ancora disponibili`} />
                          </div>

                          {Array.isArray(advice.alternatives) && advice.alternatives.length > 0 && (
                            <div className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/30 p-4">
                              <div className="flex items-center justify-between gap-3">
                                <div>
                                  <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Migliori alternative valide</div>
                                  <div className="mt-1 text-xs text-slate-500">Per i portieri: prima handcuff della stessa squadra, poi migliori abbinamenti di rotazione.</div>
                                </div>
                                <span className="text-xs font-semibold text-cyan-300">{advice.summary?.validAlternativesCount ?? advice.alternatives.length} valide</span>
                              </div>
                              <div className="mt-3 space-y-2">
                                {advice.alternatives.slice(0, 5).map((alternative, index) => (
                                  <div key={alternative.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-900/40 px-3 py-2.5">
                                    <div className="flex min-w-0 items-center gap-3">
                                      <span className="w-5 text-center text-xs font-bold text-slate-600">{index + 1}</span>
                                      <div className="min-w-0">
                                        <div className="truncate text-sm font-semibold text-slate-200">{alternative.name}</div>
                                        <div className="mt-0.5 text-[11px] text-slate-500">
                                          {alternative.type === 'SAME_TEAM_HANDCUFF' ? 'Handcuff stessa squadra' : alternative.type === 'ROTATION_PAIR' ? 'Rotazione calendario' : `${alternative.role} · ${alternative.tier || '—'}`}
                                          {alternative.roleRank ? ` · Rank ${alternative.roleRank}` : ''}
                                        </div>
                                      </div>
                                    </div>
                                    <div className="shrink-0 text-right">
                                      <div className="text-sm font-bold text-cyan-300">{alternative.estimatedCost ?? '—'} cr</div>
                                      <div className="text-[10px] text-slate-600">costo stimato</div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          <details className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/30 p-4">
                            <summary className="cursor-pointer text-sm font-semibold text-slate-200">Perché il modello dice questo</summary>
                            <div className="mt-4 grid gap-4 lg:grid-cols-2">
                              <AdviceList icon={CheckCircle2} title="Perché" items={advice.reasons} />
                              <AdviceList icon={AlertTriangle} title="Attenzione" items={advice.risks} empty="Nessun rischio rilevante." />
                            </div>
                            <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                              <TechnicalAdvice label="Valore assoluto" value={formatStat(advice.summary?.absoluteValue)} />
                              <TechnicalAdvice label="Valore marginale" value={formatStat(advice.summary?.marginalValue)} />
                              <TechnicalAdvice label="Confidenza" value={advice.confidence != null ? `${Math.round(advice.confidence * 100)}%` : '—'} />
                              <TechnicalAdvice label="Primo prezzo non conveniente" value={advice.summary?.firstBadPrice ? `${advice.summary.firstBadPrice} cr` : '—'} />
                            </div>
                          </details>
                        </>
                      )
                    )}
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/30 p-10 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-slate-700 bg-slate-900 text-slate-500">
                    <Gavel className="h-5 w-5" />
                  </div>
                  <div className="mt-3 text-sm font-semibold text-slate-300">Nessun giocatore in asta</div>
                  <div className="mt-1 text-xs text-slate-600">Usa la ricerca sopra per chiamare il prossimo giocatore.</div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="overflow-hidden border-emerald-400/15 bg-[#0F172A] shadow-xl shadow-black/10">
            <div className="h-0.5 bg-gradient-to-r from-emerald-400/70 via-cyan-400/40 to-transparent" />
            <CardHeader className="pb-4">
              <CardTitle className="text-lg text-slate-50">Squadre</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {teams.map((team) => (
                  <div key={team.id} className="rounded-xl border border-slate-800 bg-slate-950/45 p-3.5">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-slate-100">{team.name}</span>
                      <span className="text-sm font-semibold text-emerald-300">{team.credits} cr</span>
                    </div>
                    <div className="mt-2 grid grid-cols-4 gap-2 text-xs text-slate-500">
                      {Object.entries(team.slots_remaining || {}).map(([role, slots]) => (
                        <span key={role}>{role}: {slots}</span>
                      ))}
                    </div>
                    <div className="mt-2 text-[11px] text-slate-600">Max bid legale: {team.legal_max_bid} cr</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-300">{label}</label>
      <Input
        type="number"
        min="0"
        step="1"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 border-slate-700 bg-slate-950/70 text-slate-100"
      />
    </div>
  );
}

function InfoField({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/45 p-3.5">
      <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-600">{label}</div>
      <div className="mt-1.5 text-sm font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function PlayerStat({ label, value, accent = false }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/65 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-600">{label}</div>
      <div className={`mt-1 text-xl font-bold ${accent ? 'text-cyan-300' : 'text-slate-100'}`}>{value}</div>
    </div>
  );
}


function humanizeVerdict(recommendation) {
  const labels = {
    STRONG_BUY: 'COMPRALO',
    BID: 'RILANCIA',
    VALUE_ONLY: 'SOLO AL GIUSTO PREZZO',
    PASS: 'LASCIALO',
    INELIGIBLE: 'NON DISPONIBILE',
  };
  return labels[recommendation] || 'VALUTAZIONE';
}

function getActionHint(recommendation, nextBid, maxBid) {
  if (recommendation === 'STRONG_BUY') return `La prossima offerta è ${nextBid} cr: sei ancora in zona conveniente.`;
  if (recommendation === 'BID') return `Rilancia solo finché resti sotto ${maxBid} cr.`;
  if (recommendation === 'VALUE_ONLY') return `Aspetta il prezzo giusto: non inseguire il giocatore oltre il limite.`;
  if (recommendation === 'PASS') return 'La migliore alternativa per la tua rosa è più conveniente.';
  return 'Controlla i dettagli prima di continuare.';
}

function readableStatus(status) {
  const labels = {
    AVAILABLE: 'Disponibile', STARTER: 'Titolare', DOUBTFUL: 'In dubbio', ROTATION: 'Rotazione',
    BENCH: 'Panchina', INJURED: 'Infortunato', SUSPENDED: 'Squalificato',
  };
  return labels[String(status || '').toUpperCase()] || status || 'Non disponibile';
}

function getMarginalSentence(advice) {
  const pct = Number(advice?.summary?.marginalGainPercentage);
  if (!Number.isFinite(pct)) return 'Il modello non ha ancora una stima leggibile del vantaggio.';
  if (pct <= 0) return 'Prenderlo non migliora la tua rosa rispetto alla migliore alternativa.';
  return `A questo prezzo la tua rosa guadagna circa il ${pct.toFixed(1)}% rispetto alla migliore alternativa disponibile.`;
}

function getPriceGuidanceTitle(nextBid, advice) {
  const max = Number(advice?.maxBid || 0);
  if (max <= 0) return 'Non conviene entrare';
  if (nextBid > max) return 'Hai già superato il tuo limite';
  if (nextBid <= Number(advice?.idealMax || 0)) return 'Zona conveniente';
  return 'Zona di attenzione';
}

function getPriceGuidanceText(nextBid, advice) {
  const max = Number(advice?.maxBid || 0);
  const ideal = Number(advice?.idealMax || 0);
  if (max <= 0) return 'Lascia andare e conserva i crediti per alternative migliori.';
  if (nextBid > max) return `STOP: ${max} cr è il limite assoluto. Al prossimo rilancio sei fuori strategia.`;
  if (nextBid <= ideal) return `Puoi continuare: ${ideal} cr è il tetto della fascia ideale.`;
  return `Puoi ancora valutare il rilancio, ma sei oltre la fascia ideale. Il limite resta ${max} cr.`;
}

function describeDemand(opponentDemand) {
  const value = Number(opponentDemand);
  return Number.isFinite(value) ? `${Math.max(0, Math.round(value))} squadre interessate` : 'Non stimata';
}

function describeScarcity(validAlternatives, roleSupply) {
  const valid = Number(validAlternatives);
  const supply = Number(roleSupply);
  if (Number.isFinite(valid)) return `${Math.max(0, Math.round(valid))} alternative valide`;
  if (Number.isFinite(supply)) return '— alternative valide';
  return 'Non disponibile';
}

function describeInflation(value) {
  const x = Number(value);
  if (!Number.isFinite(x)) return 'Non disponibile';
  const pct = (x - 1) * 100;
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}% inflazione osservata nel mercato`;
}

function describeRisk(advice) {
  const statusRisk = Number(advice?.summary?.statusRisk);
  if (!Number.isFinite(statusRisk)) return 'Non disponibile';
  return `${(statusRisk * 100).toFixed(0)}% rischio status`;
}

function SimpleAdviceCard({ label, value, help }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/35 p-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">{label}</div>
      <div className="mt-1 text-base font-bold text-slate-100">{value}</div>
      <div className="mt-1 text-xs leading-5 text-slate-500">{help}</div>
    </div>
  );
}

function TechnicalAdvice({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800/80 bg-slate-900/40 p-2">
      <div className="text-[10px] uppercase tracking-[0.08em] text-slate-600">{label}</div>
      <div className="mt-1 font-semibold text-slate-300">{value}</div>
    </div>
  );
}

function AdviceStat({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/35 p-2.5">
      <div className="text-[10px] uppercase tracking-wider text-slate-600">{label}</div>
      <div className="mt-1 text-sm font-bold text-slate-100">{value}</div>
    </div>
  );
}

function AdviceList({ icon: Icon, title, items, empty }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <Icon className="h-4 w-4 text-cyan-300" />
        {title}
      </div>
      <div className="space-y-1 text-xs text-slate-400">
        {items?.length
          ? items.slice(0, 5).map((item) => <div key={item}>• {item}</div>)
          : <div>{empty || '—'}</div>}
      </div>
    </div>
  );
}

function formatStat(value, decimals = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(decimals) : '—';
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  return `${Math.round(number)}%`;
}
