import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CalendarDays, FileJson, Library, Sparkles, Upload, Users } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Select } from '../components/ui/select';
import { lineupApi } from '../api/client';

const DEFAULT_FORMATIONS = ['3-4-3', '3-5-2', '4-3-3', '4-4-2', '5-3-2'];
const ROLE_LABELS = { P: 'Portieri', D: 'Difensori', C: 'Centrocampisti', A: 'Attaccanti' };
const ROLE_STYLES = {
  P: 'border-amber-400/25 bg-amber-400/10 text-amber-200',
  D: 'border-sky-400/25 bg-sky-400/10 text-sky-200',
  C: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  A: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
};

const localDate = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
};

const FORMATION_POSITIONS = {
  '3-4-3': {
    P: [[50, 92]],
    D: [[20, 69], [50, 75], [80, 69]],
    C: [[14, 48], [38, 55], [62, 55], [86, 48]],
    A: [[18, 21], [50, 14], [82, 21]],
  },
  '3-5-2': {
    P: [[50, 92]],
    D: [[20, 69], [50, 75], [80, 69]],
    C: [[10, 48], [30, 55], [50, 44], [70, 55], [90, 48]],
    A: [[37, 20], [63, 20]],
  },
  '4-3-3': {
    P: [[50, 92]],
    D: [[12, 69], [36, 75], [64, 75], [88, 69]],
    C: [[24, 48], [50, 42], [76, 48]],
    A: [[18, 21], [50, 14], [82, 21]],
  },
  '4-4-2': {
    P: [[50, 92]],
    D: [[12, 69], [36, 75], [64, 75], [88, 69]],
    C: [[13, 48], [37, 55], [63, 55], [87, 48]],
    A: [[37, 20], [63, 20]],
  },
  '5-3-2': {
    P: [[50, 88]],
    D: [[11, 68], [30, 72], [50, 75], [70, 72], [89, 68]],
    C: [[24, 48], [50, 41], [76, 48]],
    A: [[37, 19], [63, 19]],
  },
  '5-4-1': {
    P: [[50, 88]],
    D: [[9, 66], [29, 71], [50, 74], [71, 71], [91, 66]],
    C: [[12, 47], [37, 54], [63, 54], [88, 47]],
    A: [[50, 19]],
  },
};

const ROLE_PILL = {
  P: 'border-amber-200/35 bg-amber-300/15 text-amber-100',
  D: 'border-sky-200/35 bg-sky-300/15 text-sky-100',
  C: 'border-emerald-200/35 bg-emerald-300/15 text-emerald-100',
  A: 'border-rose-200/35 bg-rose-300/15 text-rose-100',
};

function PitchPlayer({ player, position }) {
  const [left, top] = position;
  const fixture = player.opponent
    ? `${player.squadra} · ${player.opponent}`
    : 'Partita non disponibile';

  const roleClass = ROLE_PILL[player.ruolo] || 'border-white/20 bg-white/10 text-white';
  const tit = Math.max(0, Math.min(100, Number(player.titolarita) || 0));
  const titBarClass =
    tit >= 75 ? 'bg-emerald-400' :
    tit >= 50 ? 'bg-lime-300' :
    tit >= 25 ? 'bg-amber-400' :
    'bg-red-500';

  return (
    <div
      className="absolute z-20 -translate-x-1/2 -translate-y-1/2"
      style={{ left: `${left}%`, top: `${top}%` }}
    >
      <article className="w-[116px] rounded-xl border border-slate-800/90 bg-[#07111F] p-2 shadow-[0_10px_24px_rgba(0,0,0,0.34)] sm:w-[128px]">
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0">
            <Badge className={`border ${roleClass} px-1.5 py-0.5 text-[8px]`}>{player.ruolo}</Badge>
            <p className="mt-1 truncate text-[10px] font-bold text-slate-100" title={player.nome}>
              {player.nome}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="text-[7px] font-semibold uppercase tracking-[0.11em] text-slate-500">Score</p>
            <p className="text-[15px] font-black leading-none text-cyan-300">{player.expected_score.toFixed(2)}</p>
          </div>
        </div>

        <div className="mt-1 flex items-center gap-1 text-[7px] text-slate-300">
          <span className="min-w-0 flex-1 truncate" title={fixture}>{fixture}</span>
          <span className="shrink-0 font-semibold text-slate-400">
            Difficoltà {player.difficulty_score.toFixed(1)}
          </span>
        </div>

        <div className="mt-1.5">
          <div className="mb-1 flex items-center justify-between text-[7px] uppercase tracking-wide">
            <span className="text-slate-500">Titolarità</span>
            <span className="font-bold text-slate-100">{tit.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
            <div className={`h-full rounded-full ${titBarClass}`} style={{ width: `${tit}%` }} />
          </div>
        </div>
      </article>
    </div>
  );
}

function FormationPitch({ formation, starters, expectedScore }) {
  const positions = FORMATION_POSITIONS[formation] || FORMATION_POSITIONS['4-3-3'];

  return (
    <div className="mx-auto w-full max-w-[1300px] px-0 sm:px-3">
      <div className="relative aspect-[1.45] min-h-[440px] max-h-[500px] overflow-hidden rounded-[28px] border border-emerald-100/15 bg-gradient-to-b from-emerald-700 via-emerald-600 to-emerald-700 shadow-[0_24px_70px_rgba(0,0,0,0.34)] sm:min-h-[470px]">
        {/* Profondità visiva del campo */}
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.045),transparent_38%,rgba(0,0,0,0.16))]" />
        <div className="pointer-events-none absolute inset-0 opacity-[0.10] [background-image:repeating-linear-gradient(to_bottom,transparent_0%,transparent_11%,rgba(255,255,255,0.18)_11.2%,transparent_12.2%)]" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[30%] bg-gradient-to-t from-black/20 to-transparent" />

        {/* texture leggera */}
        <div className="absolute inset-0 opacity-[0.08] [background-image:repeating-linear-gradient(90deg,transparent,transparent_48px,rgba(255,255,255,0.08)_48px,rgba(255,255,255,0.08)_96px)]" />

        {/* linee del campo */}
        <div className="absolute inset-[8%] rounded-[12px] border border-white/30" />
        <div className="absolute left-[8%] right-[8%] top-1/2 border-t border-white/30" />

        {/* cerchio centrale */}
        <div className="absolute left-1/2 top-1/2 h-[20%] aspect-square -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/30" />
        <div className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/70" />

        {/* area alta */}
        <div className="absolute left-1/2 top-[8%] h-[17%] w-[48%] -translate-x-1/2 border-x border-b border-white/30" />
        <div className="absolute left-1/2 top-[8%] h-[8%] w-[22%] -translate-x-1/2 border-x border-b border-white/30" />
        <div className="absolute left-1/2 top-[23%] h-[5%] w-[14%] -translate-x-1/2 rounded-b-full border-b border-white/30" />

        {/* area bassa */}
        <div className="absolute bottom-[8%] left-1/2 h-[17%] w-[48%] -translate-x-1/2 border-x border-t border-white/30" />
        <div className="absolute bottom-[8%] left-1/2 h-[8%] w-[22%] -translate-x-1/2 border-x border-t border-white/30" />
        <div className="absolute bottom-[23%] left-1/2 h-[5%] w-[14%] -translate-x-1/2 rounded-t-full border-t border-white/30" />

        {/* centrocampo / linea laterale */}
        <div className="absolute inset-y-[8%] left-1/2 border-l border-white/20" />

        {/* header campo */}
        <div className="absolute left-4 top-4 z-20 rounded-full border border-white/15 bg-slate-950/35 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-white/80 backdrop-blur">
          {formation}
        </div>
        <div className="absolute right-4 top-4 z-20 rounded-full border border-white/15 bg-slate-950/35 px-3 py-1.5 text-[10px] font-semibold text-white/80 backdrop-blur">
          Score XI {Number(expectedScore || 0).toFixed(2)}
        </div>

        {Object.entries(positions).flatMap(([role, rolePositions]) =>
          starters
            .filter((player) => player.ruolo === role)
            .map((player, index) => (
              <PitchPlayer
                key={player.id}
                player={player}
                position={rolePositions[index] || rolePositions[rolePositions.length - 1]}
              />
            ))
        )}
      </div>
    </div>
  );
}

function PlayerCard({ player }) {
  const fixture = player.opponent
    ? `${player.squadra} - ${player.opponent}`
    : 'Partita non disponibile';

  return (
    <article className="rounded-xl border border-slate-800/90 bg-slate-950/30 p-3.5 shadow-inner shadow-black/10">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Badge className={ROLE_STYLES[player.ruolo]}>{player.ruolo}</Badge>
            <h3 className="truncate text-sm font-semibold text-slate-100">{player.nome}</h3>
          </div>
          <p className="mt-1 text-xs text-slate-400">{fixture}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-lg font-bold text-cyan-300">{player.expected_score.toFixed(2)}</p>
          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">score atteso</p>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5"><p className="text-xs font-semibold text-slate-200">{player.titolarita.toFixed(0)}%</p><p className="mt-0.5 text-[9px] uppercase tracking-wide text-slate-500">Titol.</p></div>
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5"><p className="text-xs font-semibold text-slate-200">{player.difficulty_score.toFixed(1)}</p><p className="mt-0.5 text-[9px] uppercase tracking-wide text-slate-500">Difficoltà</p></div>
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5"><p className="text-xs font-semibold text-slate-200">{player.projected_mv.toFixed(2)}</p><p className="mt-0.5 text-[9px] uppercase tracking-wide text-slate-500">MV proj.</p></div>
      </div>
    </article>
  );
}

export default function SchieraFormazione() {
  const [savedRosas, setSavedRosas] = useState([]);
  const [roster, setRoster] = useState(null);
  const [selectedRosaName, setSelectedRosaName] = useState('');
  const [formations, setFormations] = useState(DEFAULT_FORMATIONS);
  const [formation, setFormation] = useState('auto');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const saved = JSON.parse(localStorage.getItem('completa_rosa_library') || '[]');
        setSavedRosas(Array.isArray(saved) ? saved : []);
        const session = JSON.parse(sessionStorage.getItem('schiera_formazione_session') || '{}');
        const response = await lineupApi.getFormations();
        const remoteFormations = Array.isArray(response.data?.formations) ? response.data.formations : [];
        if (remoteFormations.length) setFormations(remoteFormations);
        const allowed = new Set(['auto', ...(remoteFormations.length ? remoteFormations : DEFAULT_FORMATIONS)]);
        if (session.formation && allowed.has(session.formation)) setFormation(session.formation);
        if (session.roster) setRoster(session.roster);
        if (session.selectedRosaName) setSelectedRosaName(session.selectedRosaName);
      } catch (storageError) {
        console.error('Errore inizializzazione schiera formazione:', storageError);
      }
    };
    load();
  }, []);

  useEffect(() => {
    try {
      sessionStorage.setItem('schiera_formazione_session', JSON.stringify({ roster, selectedRosaName, formation }));
    } catch (storageError) {
      console.error('Errore salvataggio sessione:', storageError);
    }
  }, [roster, selectedRosaName, formation]);

  const playerCount = useMemo(() => roster?.roster?.filter((slot) => slot?.player)?.length || 0, [roster]);

  const chooseSavedRosa = (name) => {
    const saved = savedRosas.find((rosa) => rosa.name === name);
    setRoster(saved || null);
    setSelectedRosaName(saved?.name || '');
    setResult(null);
    setError(null);
  };

  const importRosa = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ({ target }) => {
      try {
        const parsed = JSON.parse(target.result);
        if (!Array.isArray(parsed?.roster)) throw new Error('Formato non supportato');
        setRoster(parsed);
        setSelectedRosaName(parsed.name || file.name.replace(/\.json$/i, ''));
        setResult(null);
        setError(null);
      } catch {
        setError('Il file non contiene una rosa valida. Serve un JSON con l’array roster.');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const recommend = async () => {
    if (!roster) {
      setError('Scegli o carica una rosa prima di elaborare la formazione.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await lineupApi.recommend({
        local_date: localDate(),
        formation,
        roster,
      });
      setResult(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Non è stato possibile elaborare la formazione.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message="Sto valutando la formazione della prossima giornata..." className="min-h-[60vh]" />;

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <PageHeader
        eyebrow="Rosa · giornata corrente"
        title="Schiera formazione"
        description="Una proposta per la sola prossima giornata disponibile nel calendario, calcolata con la data locale di questa macchina."
      />
      <main className="mx-auto w-full max-w-[1480px] space-y-5 px-4 py-5 sm:px-6 lg:px-8">
        <section className="relative overflow-hidden rounded-2xl border border-slate-800/90 bg-[#0F172A] p-4 shadow-[0_10px_30px_rgba(0,0,0,0.16)] sm:p-5">
          <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px_auto] lg:items-end">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Fonte rosa</p>
              <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                <Select value={selectedRosaName} onChange={(event) => chooseSavedRosa(event.target.value)} className="border-slate-700 bg-slate-950/60">
                  <option value="">Scegli una rosa salvata</option>
                  {savedRosas.map((rosa, index) => <option value={rosa.name} key={`${rosa.name}-${index}`}>{rosa.name} · {rosa.roster?.filter((slot) => slot.player).length || 0} giocatori</option>)}
                </Select>
                <Button type="button" variant="outline" onClick={() => document.getElementById('lineup-import').click()}><Upload className="h-4 w-4" /> Carica JSON</Button>
                <input id="lineup-import" type="file" accept=".json,application/json" onChange={importRosa} className="hidden" />
              </div>
              <p className="mt-2 text-xs text-slate-500">{roster ? `${selectedRosaName || 'Rosa importata'} · ${playerCount} giocatori disponibili` : 'Importa un export di Rosa oppure seleziona una rosa dalla libreria.'}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Modulo</p>
              <Select value={formation} onChange={(event) => setFormation(event.target.value)} className="mt-2 border-slate-700 bg-slate-950/60">
                {['auto', ...formations].map((value) => <option value={value} key={value}>{value === 'auto' ? 'Automatico (miglior punteggio)' : value}</option>)}
              </Select>
            </div>
            <Button type="button" onClick={recommend} disabled={!roster} className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"><Sparkles className="h-4 w-4" /> Consiglia formazione</Button>
          </div>
        </section>

        {error && <ErrorState title="Formazione non disponibile" message={error} onRetry={recommend} />}

        {!result && !error && (
          <EmptyState icon={Users} title="Scegli la rosa da schierare" description="Seleziona una rosa salvata o importa il suo JSON, quindi genera l’undici suggerito per la prossima giornata." />
        )}

        {result && (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ['Giornata', result.matchday, CalendarDays, 'text-sky-300 bg-sky-400/10 border-sky-400/15'],
                ['Score XI', result.lineup_summary.expected_score.toFixed(2), Sparkles, 'text-violet-300 bg-violet-400/10 border-violet-400/15'],
                ['Modificatore', `+${result.lineup_summary.expected_defense_modifier}`, Users, 'text-emerald-300 bg-emerald-400/10 border-emerald-400/15'],
                ['Copertura fixture', `${result.lineup_summary.coverage.players_with_fixture}/${playerCount}`, FileJson, 'text-amber-300 bg-amber-400/10 border-amber-400/15'],
              ].map(([label, value, Icon, style]) => <Card key={label} className="border-slate-800/90 bg-[#0F172A]"><CardContent className="flex items-start justify-between p-4"><div><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-100">{value}</p></div><div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${style}`}><Icon className="h-5 w-5" /></div></CardContent></Card>)}
            </section>
            <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A] p-4 shadow-[0_10px_30px_rgba(0,0,0,0.16)] sm:p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Formazione consigliata</p>
                  <h2 className="mt-1 text-lg font-semibold text-slate-100">{result.formation} · Giornata {result.matchday}</h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Fixture dal {new Date(`${result.date_range.from}T12:00:00`).toLocaleDateString()} al {new Date(`${result.date_range.to}T12:00:00`).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant="outline" className="w-fit border-cyan-400/25 bg-cyan-400/10 text-cyan-200">
                  Data locale: {localDate()}
                </Badge>
              </div>

              <div className="mt-5">
                <FormationPitch
                  formation={result.formation}
                  starters={result.selection.starters}
                  expectedScore={result.lineup_summary.expected_score}
                />
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800/90 bg-[#0F172A] p-4 sm:p-5">
              <div className="mb-4 flex items-center gap-2"><Library className="h-4 w-4 text-violet-300" /><h2 className="text-sm font-semibold text-slate-100">Panchina ordinata</h2></div>
              {result.selection.bench.length ? <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{result.selection.bench.map((player) => <PlayerCard key={player.id} player={player} />)}</div> : <p className="text-sm text-slate-500">Nessuna alternativa disponibile nella rosa caricata.</p>}
            </section>

            {result.warnings.length > 0 && <Alert className="border-amber-400/25 bg-amber-400/[0.06]"><AlertCircle className="h-4 w-4 text-amber-300" /><AlertDescription className="text-amber-100"><p className="font-semibold">Qualità dati da verificare</p><ul className="mt-2 space-y-1 text-xs text-amber-100/80">{result.warnings.map((warning) => <li key={warning}>• {warning}</li>)}</ul></AlertDescription></Alert>}
          </>
        )}
      </main>
    </div>
  );
}
