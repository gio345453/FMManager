import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Shield, Trophy, TrendingUp } from 'lucide-react';
import { teamsApi } from '../api/client';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { TeamLogo } from '../components/common/PlayerMedia';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

function getPositionTone(position, teamName, neopromosse) {
  if (neopromosse.includes(teamName)) return 'promoted';
  if (position <= 4) return 'champions';
  if (position === 5) return 'europa';
  if (position === 6) return 'conference';
  if (position >= 18) return 'relegation';
  return 'neutral';
}

function PositionBadge({ position, teamName, neopromosse }) {
  const tone = getPositionTone(position, teamName, neopromosse);

  const classes = {
    champions: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    europa: 'border-blue-400/20 bg-blue-400/10 text-blue-300',
    conference: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
    relegation: 'border-red-400/20 bg-red-400/10 text-red-300',
    promoted: 'border-lime-400/20 bg-lime-400/10 text-lime-300',
    neutral: 'border-slate-700 bg-slate-900/60 text-slate-300',
  };

  return (
    <div
      className={`flex h-9 w-9 items-center justify-center rounded-lg border text-sm font-bold ${classes[tone]}`}
      aria-label={`Posizione ${position}`}
    >
      {position}
    </div>
  );
}

function Teams() {
  const [teams, setTeams] = useState([]);
  const [neopromosse, setNeopromosse] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const [teamsRes, neopromosseRes] = await Promise.all([
        teamsApi.getAll(),
        teamsApi.getNeopromosse(),
      ]);
      setTeams(teamsRes.data);
      setNeopromosse(neopromosseRes.data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Caricamento squadre..." className="py-16" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Errore caricamento squadre"
        message={error}
        onRetry={loadTeams}
        className="py-16"
      />
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title="Squadre Serie A"
          description="Classifica e statistiche delle squadre"
          actions={
            <Button type="button" variant="outline" size="sm" onClick={loadTeams}>
              <TrendingUp className="h-4 w-4" />
              Aggiorna
            </Button>
          }
        />

        <main className="mt-5 space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-400/15 bg-sky-400/8 text-sky-300">
                    <Shield className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                      Squadre
                    </p>
                    <p className="mt-1 text-2xl font-bold text-slate-100">{teams.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-lime-400/15 bg-lime-400/8 text-lime-300">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                      Neopromosse
                    </p>
                    <p className="mt-1 text-2xl font-bold text-slate-100">
                      {neopromosse.length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-800/90 bg-[#0F172A] sm:col-span-2 xl:col-span-1">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-amber-400/15 bg-amber-400/8 text-amber-300">
                    <Trophy className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                      Vertice classifica
                    </p>
                    <div className="mt-1 flex items-center gap-2">
                      <TeamLogo teamName={teams[0]?.squadra} size={28} />
                      <p className="text-lg font-bold text-slate-100">
                        {teams[0]?.squadra || '—'}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="overflow-hidden border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-4 py-4 sm:px-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-sm font-semibold text-slate-100">
                    Classifica Serie A
                  </CardTitle>
                  <p className="mt-1 text-xs text-slate-500">
                    Posizione, punti e differenza reti
                  </p>
                </div>
                <Badge variant="secondary">{teams.length} squadre</Badge>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <ResponsiveTable
                caption="Classifica Serie A"
                mobileContent={
                  <div className="space-y-2 p-3">
                    {teams.map((team) => {
                      const diff = team.gol_fatti - team.gol_subiti;
                      return (
                        <button
                          key={team.squadra}
                          type="button"
                          onClick={() => navigate(`/teams/${team.squadra}`)}
                          className="group flex w-full items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-950/25 p-3 text-left transition-colors hover:border-slate-700 hover:bg-slate-900/50"
                        >
                          <PositionBadge
                            position={team.posizione}
                            teamName={team.squadra}
                            neopromosse={neopromosse}
                          />

                          <TeamLogo teamName={team.squadra} size={32} />
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-semibold text-slate-100">
                              {team.squadra}
                            </div>
                            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                              <span>{team.punti} pt</span>
                              <span>GF {team.gol_fatti}</span>
                              <span>GS {team.gol_subiti}</span>
                              <span className={diff >= 0 ? 'text-emerald-300' : 'text-red-300'}>
                                Diff {diff > 0 ? '+' : ''}{diff}
                              </span>
                            </div>
                          </div>

                          <ChevronRight className="h-4 w-4 shrink-0 text-slate-600 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-300" />
                        </button>
                      );
                    })}
                  </div>
                }
              >
                <thead>
                  <tr className="bg-slate-950/55">
                    <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Pos
                    </th>
                    <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Squadra
                    </th>
                    <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Punti
                    </th>
                    <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      GF
                    </th>
                    <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      GS
                    </th>
                    <th className="px-5 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Diff
                    </th>
                    <th className="px-5 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Azione
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {teams.map((team) => {
                    const diff = team.gol_fatti - team.gol_subiti;

                    return (
                      <tr
                        key={team.squadra}
                        onClick={() => navigate(`/teams/${team.squadra}`)}
                        className="cursor-pointer border-t border-slate-800/70 transition-colors hover:bg-slate-800/20"
                      >
                        <td className="px-5 py-3">
                          <div className="flex justify-center">
                            <PositionBadge
                              position={team.posizione}
                              teamName={team.squadra}
                              neopromosse={neopromosse}
                            />
                          </div>
                        </td>
                        <td className="px-5 py-3 text-sm font-medium text-slate-100">
                          <div className="flex items-center gap-2.5">
                            <TeamLogo teamName={team.squadra} size={28} />
                            <span>{team.squadra}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3 text-center text-sm font-semibold text-slate-200">
                          {team.punti}
                        </td>
                        <td className="px-5 py-3 text-center text-sm font-medium text-emerald-300">
                          {team.gol_fatti}
                        </td>
                        <td className="px-5 py-3 text-center text-sm font-medium text-red-300">
                          {team.gol_subiti}
                        </td>
                        <td className="px-5 py-3 text-center">
                          <Badge variant={diff >= 0 ? 'success' : 'destructive'}>
                            {diff > 0 ? '+' : ''}{diff}
                          </Badge>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="border-sky-400/25 bg-sky-400/[0.05] text-sky-300 hover:border-sky-400/45 hover:bg-sky-400/[0.10] hover:text-sky-200"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/teams/${team.squadra}`);
                            }}
                          >
                            Dettagli
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </ResponsiveTable>
            </CardContent>
          </Card>

          <Alert className="border-slate-800/90 bg-[#0F172A]">
            <Shield className="h-4 w-4 text-sky-300" />
            <AlertDescription>
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-400">
                <span><strong className="text-emerald-300">1–4</strong> Champions League</span>
                <span><strong className="text-blue-300">5</strong> Europa League</span>
                <span><strong className="text-amber-300">6</strong> Conference League</span>
                <span><strong className="text-red-300">18–20</strong> Retrocessione</span>
                <span><strong className="text-lime-300">●</strong> Neopromosse</span>
              </div>
            </AlertDescription>
          </Alert>
        </main>
      </div>
    </div>
  );
}

export default Teams;
