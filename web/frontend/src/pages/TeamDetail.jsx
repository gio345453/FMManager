import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  ChevronRight,
  Home,
  Plane,
  Shield,
  Star,
  Target,
  TrendingUp,
  Users,
  X,
} from 'lucide-react';
import { teamsApi } from '../api/client';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import KpiCard from '../components/common/KpiCard';
import { TeamLogo } from '../components/common/PlayerMedia';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Separator } from '../components/ui/separator';

function getRoleName(role) {
  const names = { P: 'Portieri', D: 'Difensori', C: 'Centrocampisti', A: 'Attaccanti' };
  return names[role] || role;
}

function getRoleVariant(role) {
  const variants = { P: 'warning', D: 'success', C: 'default', A: 'destructive' };
  return variants[role] || 'secondary';
}

function SectionHeading({ icon: Icon, title, description }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/[0.07] text-sky-300">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-sm font-semibold tracking-tight text-slate-100">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
      </div>
    </div>
  );
}

function TeamDetail() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCalendario, setShowCalendario] = useState(false);
  const [calendario, setCalendario] = useState([]);

  useEffect(() => {
    loadTeam();
  }, [name]);

  const loadTeam = async () => {
    try {
      setLoading(true);
      setError(null);
      const teamRes = await teamsApi.getDashboard(name, true);
      setTeam(teamRes.data);
      setPlayers(teamRes.data.roster || []);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const loadCalendario = async () => {
    try {
      const response = await fetch('/api/calendario');
      if (!response.ok) throw new Error('Calendario non disponibile');

      const data = await response.json();
      const teamMatches = data.matches.filter(
        (m) => m.home_team === name || m.away_team === name
      );

      setCalendario(teamMatches);
      setShowCalendario(true);
    } catch (err) {
      alert('Errore caricamento calendario: ' + err.message);
    }
  };

  if (loading) {
    return <LoadingState message="Caricamento squadra..." className="py-16" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Errore caricamento squadra"
        message={error}
        onRetry={loadTeam}
        className="py-16"
      />
    );
  }

  if (!team) {
    return (
      <ErrorState
        title="Squadra non trovata"
        message="La squadra richiesta non esiste nel database."
        onRetry={() => navigate('/teams')}
        retryLabel="Torna alle squadre"
        className="py-16"
      />
    );
  }

  const diff = team.classifica.differenza_reti;
  const diffTone = diff >= 0 ? 'success' : 'danger';

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title={team.squadra}
          description="Dashboard completa squadra Serie A 2025-26"
          actions={
            <div className="flex flex-wrap items-center justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="border-sky-400/20 bg-sky-400/[0.04] text-sky-300 hover:border-sky-400/40 hover:bg-sky-400/[0.10] hover:text-sky-200"
                onClick={loadCalendario}
              >
                <Calendar className="h-4 w-4" aria-hidden="true" />
                <span>Calendario</span>
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="border-sky-400/25 bg-sky-400/[0.05] text-sky-300 hover:border-sky-400/45 hover:bg-sky-400/[0.10] hover:text-sky-200"
                onClick={() => navigate('/teams')}
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                <span>Torna alle squadre</span>
              </Button>
            </div>
          }
        />

        <main className="mt-5 space-y-5">
          <section>
            <div className="mb-3">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/[0.07]">
                  <TeamLogo teamName={team.squadra} size={22} />
                </div>
                <div>
                  <h2 className="text-sm font-semibold tracking-tight text-slate-100">Rendimento squadra</h2>
                  <p className="mt-0.5 text-xs text-slate-500">Indicatori principali della classifica</p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <KpiCard
                label="Posizione"
                value={`${team.classifica.posizione}°`}
                icon={() => <TeamLogo teamName={team.squadra} size={20} />}
                tone="primary"
              />
              <KpiCard
                label="Punti"
                value={team.classifica.punti}
                icon={TrendingUp}
              />
              <KpiCard
                label="Gol fatti"
                value={team.classifica.gol_fatti}
                icon={Target}
                tone="success"
              />
              <KpiCard
                label="Gol subiti"
                value={team.classifica.gol_subiti}
                icon={Shield}
                tone="danger"
              />
              <KpiCard
                label="Differenza reti"
                value={`${diff > 0 ? '+' : ''}${diff}`}
                tone={diffTone}
              />
            </div>
          </section>

          <Separator className="border-slate-800/60" />

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="px-5 pb-4">
              <SectionHeading
                icon={Star}
                title="Giocatori chiave"
                description="I protagonisti della squadra"
              />
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 lg:grid-cols-3">
                {team.giocatori_chiave.fm && (
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4 transition-colors hover:border-slate-700/90">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/[0.07]">
                        <Star className="h-4 w-4 text-sky-300" aria-hidden="true" />
                      </div>
                      <Badge variant="secondary">{team.giocatori_chiave.fm.ruolo}</Badge>
                    </div>

                    <div className="mt-4 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                      Migliore Fantamedia
                    </div>
                    <div className="mt-1 truncate text-lg font-semibold text-slate-100">
                      {team.giocatori_chiave.fm.nome}
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">FM</div>
                        <div className="mt-1 text-xl font-bold text-sky-300">
                          {team.giocatori_chiave.fm.fm?.toFixed(2) || '-'}
                        </div>
                      </div>
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">Presenze</div>
                        <div className="mt-1 text-xl font-bold text-slate-100">
                          {team.giocatori_chiave.fm.pv || '-'}
                        </div>
                      </div>
                    </div>

                    {team.giocatori_chiave.fm.id && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full border-slate-700 bg-slate-900/40 text-slate-300 hover:border-sky-400/30 hover:bg-sky-400/[0.06] hover:text-sky-200"
                        onClick={() => navigate(`/players/${team.giocatori_chiave.fm.id}`)}
                      >
                        Vedi dettagli
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                )}

                {team.giocatori_chiave.gol && (
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4 transition-colors hover:border-slate-700/90">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-400/15 bg-emerald-400/[0.07]">
                        <Target className="h-4 w-4 text-emerald-300" aria-hidden="true" />
                      </div>
                      <Badge variant="secondary">{team.giocatori_chiave.gol.ruolo}</Badge>
                    </div>

                    <div className="mt-4 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                      Capocannoniere
                    </div>
                    <div className="mt-1 truncate text-lg font-semibold text-slate-100">
                      {team.giocatori_chiave.gol.nome}
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">Gol</div>
                        <div className="mt-1 text-xl font-bold text-emerald-300">
                          {team.giocatori_chiave.gol.gol || '-'}
                        </div>
                      </div>
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">Presenze</div>
                        <div className="mt-1 text-xl font-bold text-slate-100">
                          {team.giocatori_chiave.gol.pv || '-'}
                        </div>
                      </div>
                    </div>

                    {team.giocatori_chiave.gol.id && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full border-slate-700 bg-slate-900/40 text-slate-300 hover:border-emerald-400/30 hover:bg-emerald-400/[0.06] hover:text-emerald-200"
                        onClick={() => navigate(`/players/${team.giocatori_chiave.gol.id}`)}
                      >
                        Vedi dettagli
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                )}

                {team.giocatori_chiave.assist && (
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4 transition-colors hover:border-slate-700/90">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet-400/15 bg-violet-400/[0.07]">
                        <TrendingUp className="h-4 w-4 text-violet-300" aria-hidden="true" />
                      </div>
                      <Badge variant="secondary">{team.giocatori_chiave.assist.ruolo}</Badge>
                    </div>

                    <div className="mt-4 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                      Top Assist
                    </div>
                    <div className="mt-1 truncate text-lg font-semibold text-slate-100">
                      {team.giocatori_chiave.assist.nome}
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">Assist</div>
                        <div className="mt-1 text-xl font-bold text-violet-300">
                          {team.giocatori_chiave.assist.assist || '-'}
                        </div>
                      </div>
                      <div className="rounded-lg border border-slate-800/70 bg-slate-950/30 p-3">
                        <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">Presenze</div>
                        <div className="mt-1 text-xl font-bold text-slate-100">
                          {team.giocatori_chiave.assist.pv || '-'}
                        </div>
                      </div>
                    </div>

                    {team.giocatori_chiave.assist.id && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full border-slate-700 bg-slate-900/40 text-slate-300 hover:border-violet-400/30 hover:bg-violet-400/[0.06] hover:text-violet-200"
                        onClick={() => navigate(`/players/${team.giocatori_chiave.assist.id}`)}
                      >
                        Vedi dettagli
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {team.reparti?.dettaglio && (
            <>
              <Separator className="border-slate-800/60" />

              <Card className="border-slate-800/90 bg-[#0F172A]">
                <CardHeader className="px-5 pb-4">
                  <SectionHeading
                    icon={Users}
                    title="Analisi reparti"
                    description="Performance media per ruolo"
                  />
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    {Object.entries(team.reparti.dettaglio).map(([role, data]) => (
                      <div
                        key={role}
                        className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <Badge variant={getRoleVariant(role)}>
                            {getRoleName(role)}
                          </Badge>
                          <span className="text-xs text-slate-600">
                            {data.giocatori} giocatori
                          </span>
                        </div>

                        <div className="mt-4">
                          <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">FM media</div>
                          <div className="mt-1 text-xl font-semibold text-sky-300">
                            {data.fm_media?.toFixed(2) || '-'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          <Separator className="border-slate-800/60" />

          <Card className="overflow-hidden border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="px-5 pb-4">
              <SectionHeading
                icon={Users}
                title="Rosa completa"
                description={`${players.length} giocatori · clicca una riga per aprire il dettaglio`}
              />
            </CardHeader>

            <CardContent className="p-0">
              {players.length > 0 ? (
                <>
                  <div className="block md:hidden space-y-2 p-3">
                    {players.map((player) => (
                      <button
                        type="button"
                        key={player.id}
                        onClick={() => navigate(`/players/${player.id}`)}
                        className="flex w-full items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-950/25 p-3 text-left transition-colors hover:border-slate-700 hover:bg-slate-900/45"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-semibold text-slate-100">{player.nome}</div>
                          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                            <Badge variant={getRoleVariant(player.ruolo)}>{player.ruolo}</Badge>
                            <span>FM {player.fm?.toFixed(2) || '-'}</span>
                            <span>MV {player.mv?.toFixed(2) || '-'}</span>
                          </div>
                        </div>
                        <div className="grid shrink-0 grid-cols-2 gap-x-4 gap-y-1 text-right text-xs">
                          <span className="text-slate-500">Pv {player.pv || '-'}</span>
                          <span className="text-emerald-300">Gol {player.gf || '-'}</span>
                          <span className="text-slate-500">Ass {player.ass || '-'}</span>
                        </div>
                        <ChevronRight className="h-4 w-4 shrink-0 text-slate-600" />
                      </button>
                    ))}
                  </div>

                  <div className="hidden md:block">
                    <ResponsiveTable caption="Rosa completa squadra">
                      <thead>
                        <tr className="bg-slate-950/55">
                          <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Nome</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Ruolo</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">FM</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">MV</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Pv</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Gol</th>
                          <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Assist</th>
                        </tr>
                      </thead>
                      <tbody>
                        {players.map((player) => (
                          <tr
                            key={player.id}
                            className="cursor-pointer border-t border-slate-800/70 transition-colors hover:bg-slate-800/20"
                            onClick={() => navigate(`/players/${player.id}`)}
                          >
                            <td className="px-5 py-3 text-sm font-medium text-slate-100">{player.nome}</td>
                            <td className="px-5 py-3 text-center">
                              <Badge variant={getRoleVariant(player.ruolo)}>{player.ruolo}</Badge>
                            </td>
                            <td className="px-5 py-3 text-center text-sm text-sky-300">{player.fm?.toFixed(2) || '-'}</td>
                            <td className="px-5 py-3 text-center text-sm text-slate-300">{player.mv?.toFixed(2) || '-'}</td>
                            <td className="px-5 py-3 text-center text-sm text-slate-300">{player.pv || '-'}</td>
                            <td className="px-5 py-3 text-center text-sm text-emerald-300">{player.gf || '-'}</td>
                            <td className="px-5 py-3 text-center text-sm text-violet-300">{player.ass || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </ResponsiveTable>
                  </div>
                </>
              ) : (
                <div className="px-5 py-10 text-center text-sm text-slate-500">
                  Nessun giocatore trovato per questa squadra
                </div>
              )}
            </CardContent>
          </Card>
        </main>
      </div>

      {showCalendario && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-3 backdrop-blur-sm sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="calendario-title"
          onClick={() => setShowCalendario(false)}
        >
          <div
            className="max-h-[92vh] w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-800/90 bg-[#0F172A] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b border-slate-800/80 px-5 py-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-sky-300">
                  <Calendar className="h-4 w-4" />
                  <span className="text-[11px] font-semibold uppercase tracking-[0.1em]">
                    Calendario
                  </span>
                </div>
                <h2 id="calendario-title" className="mt-1 truncate text-base font-semibold text-slate-100">
                  {name} · Stagione 2024-25
                </h2>
                <p className="mt-1 text-xs text-slate-500">{calendario.length} partite totali</p>
              </div>

              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Chiudi calendario"
                onClick={() => setShowCalendario(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="max-h-[calc(92vh-145px)] overflow-auto p-3 sm:p-5">
              <ResponsiveTable caption="Calendario completo stagione">
                <thead>
                  <tr className="bg-slate-950/55">
                    <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">G</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Data</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Casa</th>
                    <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Risultato</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Trasferta</th>
                  </tr>
                </thead>
                <tbody>
                  {calendario.map((match, idx) => {
                    const isHome = match.home_team === name;
                    let resultTone = 'text-slate-500';

                    if (match.played) {
                      const won =
                        (isHome && match.home_goals > match.away_goals) ||
                        (!isHome && match.away_goals > match.home_goals);
                      const draw = match.home_goals === match.away_goals;
                      resultTone = won
                        ? 'text-emerald-300'
                        : draw
                          ? 'text-amber-300'
                          : 'text-red-300';
                    }

                    return (
                      <tr key={idx} className="border-t border-slate-800/70 hover:bg-slate-800/20">
                        <td className="px-4 py-3 text-center text-sm text-slate-500">{match.matchday}</td>
                        <td className="px-4 py-3 text-sm text-slate-500">{match.date || '-'}</td>
                        <td className={`px-4 py-3 text-sm ${isHome ? 'font-medium text-sky-200' : 'text-slate-300'}`}>
                          {match.home_team}
                          {isHome && <Home className="ml-1 inline-block h-3.5 w-3.5" aria-hidden="true" />}
                        </td>
                        <td className={`px-4 py-3 text-center text-sm font-semibold ${resultTone}`}>
                          {match.played ? `${match.home_goals} - ${match.away_goals}` : 'vs'}
                        </td>
                        <td className={`px-4 py-3 text-sm ${!isHome ? 'font-medium text-sky-200' : 'text-slate-300'}`}>
                          {match.away_team}
                          {!isHome && <Plane className="ml-1 inline-block h-3.5 w-3.5" aria-hidden="true" />}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </ResponsiveTable>
            </div>

            <div className="flex justify-end border-t border-slate-800/80 px-5 py-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowCalendario(false)}
              >
                Chiudi
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TeamDetail;
