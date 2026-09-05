import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Search, Target, ChevronRight } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Separator } from '../components/ui/separator';
import { teamLogoUrl } from '../utils/playerMedia';

function ShooterRow({ rank, name, primary, icon: Icon, onClick }) {
  if (!name) return null;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group flex w-full items-center gap-3 rounded-xl border px-3.5 py-3 text-left transition-all ${
        primary
          ? 'border-sky-400/20 bg-sky-400/[0.055] hover:border-sky-400/35 hover:bg-sky-400/[0.085]'
          : 'border-slate-800/80 bg-slate-950/20 hover:border-slate-700 hover:bg-slate-900/40'
      }`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-xs font-bold ${
          primary
            ? 'border-amber-300/25 bg-amber-400/10 text-amber-300'
            : 'border-slate-700 bg-slate-900/70 text-slate-400'
        }`}
      >
        {Icon ? <Icon className="h-3.5 w-3.5" aria-hidden="true" /> : rank}
      </div>

      <div className="min-w-0 flex-1 truncate text-sm font-medium text-slate-100 group-hover:text-white">
        {name}
      </div>

      <ChevronRight
        className="h-4 w-4 shrink-0 text-slate-700 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-400"
        aria-hidden="true"
      />
    </button>
  );
}

function Tiratori() {
  const [tiratori, setTiratori] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTeam, setSearchTeam] = useState('');
  const navigate = useNavigate();
  const { players } = useAppContext();

  useEffect(() => {
    loadTiratori();
  }, []);

  const loadTiratori = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/tiratori');
      if (!response.ok) throw new Error('Errore nel caricamento tiratori');
      const data = await response.json();
      setTiratori(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handlePlayerClick = (playerName) => {
    if (!playerName || !players.length) return;

    const player = players.find(
      (p) =>
        p.nome === playerName ||
        p.nome === playerName + ' *' ||
        p.nome.replace(' *', '') === playerName
    );

    if (player) {
      navigate(`/players/${player.id}`);
    }
  };

  const filteredTiratori = tiratori.filter((team) =>
    team.squadra.toLowerCase().includes(searchTeam.toLowerCase())
  );

  if (loading) {
    return <LoadingState message="Caricamento tiratori..." className="py-16" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Errore caricamento tiratori"
        message={error}
        onRetry={loadTiratori}
        className="py-16"
      />
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title="Rigoristi e Tiratori"
          description="Gerarchie rigori e calci piazzati per squadra"
        />

        <main className="mt-5 space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-400/15 bg-sky-400/[0.07] text-sky-300">
                    <Target className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                      Squadre
                    </div>
                    <div className="mt-1 text-2xl font-bold text-slate-100">
                      {filteredTiratori.length}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>


          </div>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardContent className="p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-sm font-semibold text-slate-100">Cerca squadra</div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    Filtra rapidamente le gerarchie dei calci piazzati
                  </div>
                </div>
                <div className="relative w-full sm:max-w-sm">
                  <Search
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600"
                    aria-hidden="true"
                  />
                  <Input
                    type="text"
                    placeholder="Cerca squadra..."
                    value={searchTeam}
                    onChange={(e) => setSearchTeam(e.target.value)}
                    className="pl-9"
                    aria-label="Cerca squadra"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {filteredTiratori.length > 0 ? (
            <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
              {filteredTiratori.map((team, idx) => (
                <Card
                  key={idx}
                  className="relative overflow-hidden border border-slate-700/70 bg-[#0F172A] shadow-[0_10px_30px_rgba(0,0,0,0.20)] transition-all hover:-translate-y-0.5 hover:border-slate-600 hover:shadow-[0_14px_36px_rgba(0,0,0,0.26)]"
                >
                  <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
                  <CardHeader className="border-b border-slate-700/80 bg-slate-950/20 px-5 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/[0.06] overflow-hidden">
                          <img
                            src={teamLogoUrl(team.squadra)}
                            alt={team.squadra}
                            className="h-full w-full object-contain p-1"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        </div>
                        <CardTitle className="truncate text-base font-semibold text-slate-100">
                          {team.squadra}
                        </CardTitle>
                      </div>
                      <Badge variant="secondary">Serie A</Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-5 p-5">
                    <section>
                      <div className="mb-2.5 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-amber-400/15 bg-amber-400/[0.06] text-amber-300">
                            <Award className="h-3.5 w-3.5" aria-hidden="true" />
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-slate-100">Rigori</div>
                            <div className="text-[11px] text-slate-500">Gerarchia calciatori</div>
                          </div>
                        </div>
                        <Badge className="border-amber-300/15 bg-amber-400/[0.08] text-amber-300">
                          RIG
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <ShooterRow
                          rank="1°"
                          icon={Award}
                          primary
                          name={team.rigoristi['1_rigorista']}
                          onClick={() =>
                            handlePlayerClick(team.rigoristi['1_rigorista'])
                          }
                        />
                        <ShooterRow
                          rank="2°"
                          name={team.rigoristi['2_rigorista']}
                          onClick={() =>
                            handlePlayerClick(team.rigoristi['2_rigorista'])
                          }
                        />
                        <ShooterRow
                          rank="3°"
                          name={team.rigoristi['3_rigorista']}
                          onClick={() =>
                            handlePlayerClick(team.rigoristi['3_rigorista'])
                          }
                        />
                      </div>
                    </section>

                    <Separator className="border-slate-800/70" />

                    <section>
                      <div className="mb-2.5 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-violet-400/15 bg-violet-400/[0.06] text-violet-300">
                            <Target className="h-3.5 w-3.5" aria-hidden="true" />
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-slate-100">
                              Calci piazzati
                            </div>
                            <div className="text-[11px] text-slate-500">Piazzati e angoli</div>
                          </div>
                        </div>
                        <Badge className="border-violet-300/15 bg-violet-400/[0.08] text-violet-300">
                          CPA
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <ShooterRow
                          rank="1°"
                          icon={Target}
                          primary
                          name={team.piazzati_e_angoli['1_tiratore']}
                          onClick={() =>
                            handlePlayerClick(team.piazzati_e_angoli['1_tiratore'])
                          }
                        />
                        <ShooterRow
                          rank="2°"
                          name={team.piazzati_e_angoli['2_tiratore']}
                          onClick={() =>
                            handlePlayerClick(team.piazzati_e_angoli['2_tiratore'])
                          }
                        />
                        <ShooterRow
                          rank="3°"
                          name={team.piazzati_e_angoli['3_tiratore']}
                          onClick={() =>
                            handlePlayerClick(team.piazzati_e_angoli['3_tiratore'])
                          }
                        />
                      </div>
                    </section>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Target}
              title="Nessuna squadra trovata"
              description="Prova a modificare il termine di ricerca"
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default Tiratori;
