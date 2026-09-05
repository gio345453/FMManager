import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Activity,
  Calendar,
  Edit3,
  FileText,
  Home,
  Plane,
  Save,
  Shield,
  Star,
  TrendingUp,
  X,
  Trophy,
  WalletCards,
  Target,
  Swords,
} from 'lucide-react';

import { playersApi } from '../api/client';
import { formatTitolarita } from '../utils/formatters';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import KpiCard from '../components/common/KpiCard';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Separator } from '../components/ui/separator';
import { PlayerAvatar, TeamLogo } from '../components/common/PlayerMedia';
import { useAppContext } from '../context/AppContext';

const ROLE_VARIANTS = {
  P: 'warning',
  D: 'success',
  C: 'default',
  A: 'destructive',
};

// Ruoli speciali con colori custom
const SPECIAL_ROLE_COLORS = {
  'C (T)': 'bg-purple-500/10 text-purple-300 border-purple-400/20',
  'D (E)': 'bg-green-500/10 text-green-300 border-green-400/20',
};

function RoleBadge({ role }) {
  const value = role?.trim() || '-';

  // Check se è un ruolo speciale con colore custom
  const specialColor = SPECIAL_ROLE_COLORS[value];

  if (specialColor) {
    return (
      <Badge className={`${specialColor} font-medium`}>
        {value}
      </Badge>
    );
  }

  return <Badge variant={ROLE_VARIANTS[value] || 'secondary'}>{value}</Badge>;
}

function StatItem({ label, value, accent = false }) {
  const displayValue =
    value !== undefined && value !== null && value !== 'NaN' ? value : '-';

  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/30 px-4 py-3 transition-colors hover:border-slate-700/90">
      <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
        {label}
      </div>
      <div
        className={`mt-1 text-lg font-semibold ${
          accent ? 'text-sky-300' : 'text-slate-100'
        }`}
      >
        {displayValue}
      </div>
    </div>
  );
}

function SectionTitle({ icon: Icon, title, description }) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/8 text-sky-300">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-sm font-semibold tracking-tight text-slate-100">{title}</h2>
        {description && (
          <p className="mt-0.5 text-xs text-slate-500">{description}</p>
        )}
      </div>
    </div>
  );
}

function PlayerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { settings } = useAppContext();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState({ note: '', tags: [] });

  useEffect(() => {
    loadPlayer();
  }, [id]);

  const loadPlayer = async () => {
    try {
      setLoading(true);
      setError(null);
      const budget = settings?.budget || 500;
      const res = await playersApi.getById(id, budget);
      setPlayer(res.data);
      setNotes({ note: res.data.note || '', tags: res.data.tags || [] });
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const toggleFavorite = async () => {
    try {
      await playersApi.toggleFavorite(id);
      setPlayer((prevPlayer) => ({
        ...prevPlayer,
        is_favorite: !prevPlayer.is_favorite,
      }));
    } catch (err) {
      setError('Errore nel salvare il preferito');
    }
  };

  const saveNotes = async () => {
    try {
      await playersApi.updateNotes(id, notes);
      setEditingNotes(false);
      loadPlayer();
    } catch (err) {
      setError('Errore nel salvare le note');
    }
  };

  if (loading) {
    return (
      <LoadingState
        message="Caricamento giocatore..."
        className="py-16"
      />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Errore caricamento giocatore"
        message={error}
        onRetry={loadPlayer}
        className="py-16"
      />
    );
  }

  if (!player) {
    return (
      <ErrorState
        title="Giocatore non trovato"
        message="Il giocatore richiesto non esiste nel database."
        onRetry={() => navigate('/players')}
        retryLabel="Torna alla lista"
        className="py-16"
      />
    );
  }

  const baseRole = String(player.ruolo || '').trim().charAt(0).toUpperCase();

  const defenseBonus =
    (player.ruolo === 'P' || player.ruolo === 'D') &&
    player.mv_weighted >= 6.0
      ? player.mv_weighted >= 7.0
        ? '+3'
        : player.mv_weighted >= 6.5
          ? '+2'
          : '+1'
      : null;

  const statusTone =
    player.status === 'Titolare'
      ? 'success'
      : player.status === 'Infortunati'
        ? 'danger'
        : player.status === 'Squalificati'
          ? 'warning'
          : 'default';

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title={player.nome}
          description={`${player.squadra} · ${player.ruolo}`}
          actions={
            <div className="flex flex-wrap items-center justify-end gap-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleFavorite}
                className="border-0 bg-transparent text-amber-300 hover:bg-transparent hover:text-amber-200 focus-visible:bg-transparent"
                aria-label={
                  player.is_favorite
                    ? 'Rimuovi dai preferiti'
                    : 'Aggiungi ai preferiti'
                }
              >
                <Star
                  className={`h-4 w-4 ${
                    player.is_favorite
                      ? 'fill-amber-400 text-amber-400'
                      : 'fill-transparent text-amber-400'
                  }`}
                  aria-hidden="true"
                />
                <span className="hidden sm:inline">
                  {player.is_favorite ? 'Preferito' : 'Aggiungi'}
                </span>
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => navigate(`/teams/${player.squadra}`)}
              >
                <Shield className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Info squadra</span>
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="border-sky-400/25 bg-sky-400/[0.05] text-sky-300 hover:border-sky-400/45 hover:bg-sky-400/[0.10] hover:text-sky-200"
                onClick={() => navigate('/players')}
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                <span>Indietro</span>
              </Button>
            </div>
          }
        />

        <main className="mt-5 space-y-5">
          {/* Hero */}
          <section className="overflow-hidden rounded-2xl border border-slate-800/90 bg-gradient-to-br from-[#101827] via-[#0F172A] to-[#0C1421]">
            <div className="border-b border-slate-800/80 px-5 py-5 sm:px-6">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                <div className="flex items-start gap-4">
                  <div className="shrink-0">
                    <PlayerAvatar playerId={player.id} size="medium" />
                  </div>
                  <div className="flex-1">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                    {player.status && (
                      <Badge variant={statusTone}>{player.status}</Badge>
                    )}
                    {player.is_favorite && (
                      <Badge className="border-amber-300/20 bg-amber-400/10 text-amber-300">
                        <Star className="mr-1 h-3 w-3 fill-current" />
                        Preferito
                      </Badge>
                    )}
                  </div>

                  <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
                    {player.nome}
                  </h1>
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamName={player.squadra} size={20} />
                      <span className="font-medium text-slate-300">{player.squadra}</span>
                    </div>
                    <span className="text-slate-600">•</span>
                    <RoleBadge role={player.ruolo} />
                  </div>
                </div>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="min-w-[100px] rounded-xl border border-slate-800/80 bg-slate-950/35 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      Overall
                    </div>
                    <div className="mt-1 text-2xl font-bold text-sky-300">
                      {player.overall || 'N/A'}
                    </div>
                  </div>
                  <div className="min-w-[100px] rounded-xl border border-slate-800/80 bg-slate-950/35 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      FM
                    </div>
                    <div className="mt-1 text-2xl font-bold text-slate-100">
                      {player.fm_weighted?.toFixed(2) || '-'}
                    </div>
                  </div>
                  <div className="min-w-[100px] rounded-xl border border-slate-800/80 bg-slate-950/35 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      MV
                    </div>
                    <div className="mt-1 text-2xl font-bold text-slate-100">
                      {player.mv_weighted?.toFixed(2) || '-'}
                    </div>
                  </div>
                  <div className="min-w-[100px] rounded-xl border border-slate-800/80 bg-slate-950/35 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      Titolarità
                    </div>
                    <div className="mt-1 text-2xl font-bold text-slate-100">
                      {formatTitolarita(player.titolarita)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* KPI */}
          {defenseBonus && (
            <Alert
              variant="success"
              className="border-emerald-400/20 bg-emerald-400/[0.06]"
            >
              <Shield className="h-5 w-5" aria-hidden="true" />
              <div className="min-w-0 pr-2">
                <AlertTitle>Defense Modifier attivo</AlertTitle>
                <AlertDescription>
                  {player.ruolo === 'P'
                    ? 'Portiere con MV alto: contribuisce al bonus difesa squadra'
                    : 'Difensore con MV alto: contribuisce al bonus difesa squadra'}
                </AlertDescription>
              </div>
              <Badge
                variant="success"
                className="ml-auto shrink-0 border-emerald-300/20 bg-emerald-400/10"
              >
                {defenseBonus} bonus/giornata
              </Badge>
            </Alert>
          )}

          {/* Price + stats */}
          <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="pb-4">
                <SectionTitle
                  icon={WalletCards}
                  title="Valutazione prezzo"
                  description="Costo stimato sul budget asta"
                />
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/30 p-4">
                    <div className="text-[11px] uppercase tracking-[0.08em] text-slate-500">
                      Percentuale budget
                    </div>
                    <div className="mt-2 text-3xl font-bold text-sky-300">
                      {player.price_percentage?.toFixed(2) || '-'}%
                    </div>
                  </div>
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/30 p-4">
                    <div className="text-[11px] uppercase tracking-[0.08em] text-slate-500">
                      Crediti
                    </div>
                    <div className="mt-2 text-3xl font-bold text-slate-100">
                      {player.price_credits?.toFixed(1) || '-'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="pb-4">
                <SectionTitle
                  icon={Target}
                  title="Statistiche stagione"
                  description="Valori ponderati della stagione corrente"
                />
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatItem label="Presenze" value={player.pv_weighted?.toFixed(1)} />
                  <StatItem label="Gol" value={player.gf_weighted?.toFixed(1)} accent />
                  <StatItem label="Assist" value={player.ass_weighted?.toFixed(1)} accent />
                  {baseRole !== 'P' && (
                    <StatItem label="Rigori calciati" value={player.rc_weighted?.toFixed(1)} />
                  )}
                  {baseRole === 'P' && (
                    <StatItem label="Gol subiti" value={player.gs_weighted?.toFixed(1)} />
                  )}
                  <StatItem label="Ammonizioni" value={player.amm_weighted?.toFixed(1)} />
                  <StatItem label="Espulsioni" value={player.esp_weighted?.toFixed(1)} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* History */}
          {player.history && player.history.length > 0 && (
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="pb-4">
                <SectionTitle
                  icon={Trophy}
                  title="Storico stagioni"
                  description="Performance nelle stagioni precedenti"
                />
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-xl border border-slate-800/80">
                  <ResponsiveTable caption="Storico performance giocatore per stagione">
                    <thead>
                      <tr className="bg-slate-950/55">
                        <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Stagione</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Squadra</th>
                        <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Pv</th>
                        <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Mv</th>
                        <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Fm</th>                        
                        {baseRole !== 'P' && (
                          <>
                            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Gf</th>
                            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Rc</th>
                            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Ass</th>
                          </>
                        )}
                        {baseRole === 'P' && (
                          <>
                            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Gs</th>
                            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Rp</th>
                          </>
                        )}
<th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Amm</th>
                        <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Esp</th>
                      </tr>
                    </thead>

                    <tbody>
                      {player.history.map((season, idx) => {
                        const bestFm = Math.max(...player.history.map((s) => s.Fm || 0));
                        const isBestSeason = season.Fm === bestFm && season.Fm > 0;

                        return (
                          <tr
                            key={idx}
                            className={`border-t border-slate-800/70 transition-colors hover:bg-slate-800/20 ${
                              isBestSeason ? 'bg-emerald-400/[0.055]' : ''
                            }`}
                          >
                            <td className="px-4 py-3 text-sm font-medium text-slate-200">{season.season || `Stagione ${idx + 1}`}</td>
                            <td className="px-4 py-3 text-sm text-slate-400">{season.squadra || '-'}</td>
                            <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Pv || '-'}</td>
                            <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Mv?.toFixed(2) || '-'}</td>
                            <td className={`px-4 py-3 text-right text-sm ${isBestSeason ? 'font-semibold text-emerald-300' : 'text-slate-300'}`}>
                              {season.Fm?.toFixed(2) || '-'}
                            </td>                            
                            {baseRole !== 'P' && (
                              <>
                                <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Gf || '-'}</td>
                                <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Rc || '-'}</td>
                                <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Ass || '-'}</td>
                              </>
                            )}
                            {baseRole === 'P' && (
                              <>
                                <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Gs || '-'}</td>
                                <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Rp || '-'}</td>
                              </>
                            )}
                            <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Amm || '-'}</td>
                            <td className="px-4 py-3 text-right text-sm text-slate-300">{season.Esp || '-'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </ResponsiveTable>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Fixtures */}
          {player.fixture_projections && player.fixture_projections.length > 0 && (
            <Card className="border-slate-800/90 bg-[#0F172A]">
              <CardHeader className="pb-4">
                <SectionTitle
                  icon={Swords}
                  title="Prossimi avversari"
                  description="Calendario basato sulla giornata corrente (impostazioni)"
                />
              </CardHeader>
              <CardContent>
                <div className="space-y-2.5">
                  {player.fixture_projections.slice(0, 5).map((fixture, idx) => {
                    const difficultyLabel =
                      fixture.difficulty_score < 4.5
                        ? 'Facile'
                        : fixture.difficulty_score < 7.0
                          ? 'Media'
                          : 'Difficile';

                    const difficultyVariant =
                      fixture.difficulty_score < 4.5
                        ? 'success'
                        : fixture.difficulty_score < 7.0
                          ? 'warning'
                          : 'destructive';

                    return (
                      <div
                        key={idx}
                        className="flex flex-col gap-4 rounded-xl border border-slate-800/80 bg-slate-950/25 px-4 py-4 transition-colors hover:bg-slate-900/40 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                            Giornata {fixture.matchday}
                          </div>
                          <div className="mt-1.5 flex items-center gap-2 text-sm font-semibold text-slate-100">
                            {fixture.is_home ? (
                              <Home className="h-4 w-4 text-sky-300" aria-hidden="true" />
                            ) : (
                              <Plane className="h-4 w-4 text-violet-300" aria-hidden="true" />
                            )}
                            <span className="flex items-center gap-2"><span>vs</span><TeamLogo teamName={fixture.opponent} size={20} /></span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between gap-4 sm:justify-end">
                          <div className="text-right">
                            <div className="text-[11px] uppercase tracking-[0.08em] text-slate-500">
                              Voto atteso
                            </div>
                            <div className="mt-1 text-lg font-semibold text-sky-300">
                              {fixture.voto_mean?.toFixed(2)}
                            </div>
                          </div>
                          <Badge variant={difficultyVariant}>{difficultyLabel}</Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {player.fixture_projections.length > 5 && (
                  <p className="mt-3 text-center text-xs text-slate-500">
                    Mostrando primi 5 di {player.fixture_projections.length} avversari rimanenti
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Notes */}
          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="pb-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <SectionTitle
                  icon={FileText}
                  title="Note e tag"
                  description="Annotazioni personalizzate"
                />

                {!editingNotes ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingNotes(true)}
                  >
                    <Edit3 className="h-4 w-4" aria-hidden="true" />
                    Modifica
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditingNotes(false);
                        setNotes({
                          note: player.note || '',
                          tags: player.tags || [],
                        });
                      }}
                    >
                      <X className="h-4 w-4" aria-hidden="true" />
                      Annulla
                    </Button>
                    <Button type="button" size="sm" onClick={saveNotes}>
                      <Save className="h-4 w-4" aria-hidden="true" />
                      Salva
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>

            <CardContent>
              {editingNotes ? (
                <div className="space-y-5">
                  <div>
                    <label
                      htmlFor="player-note"
                      className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400"
                    >
                      Note
                    </label>
                    <textarea
                      id="player-note"
                      rows={5}
                      value={notes.note}
                      onChange={(e) =>
                        setNotes({ ...notes, note: e.target.value })
                      }
                      placeholder="Aggiungi note sul giocatore..."
                      className="w-full rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 focus:border-sky-400/45 focus:ring-2 focus:ring-sky-400/10"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="player-tags-custom"
                      className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400"
                    >
                      Tag personalizzati
                    </label>
                    <Input
                      id="player-tags-custom"
                      type="text"
                      value={notes.tags.join(', ')}
                      onChange={(e) =>
                        setNotes({
                          ...notes,
                          tags: e.target.value
                            .split(',')
                            .map((t) => t.trim())
                            .filter((t) => t),
                        })
                      }
                      placeholder="Separati da virgola..."
                    />
                  </div>

                  <div>
                    <div className="mb-2 text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                      Tag rapidi
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {[
                        'obiettivo',
                        'da evitare',
                        'esca',
                        'riserva',
                        'titolare',
                        'occasione',
                      ].map((quickTag) => (
                        <Button
                          key={quickTag}
                          type="button"
                          variant={
                            notes.tags.includes(quickTag) ? 'default' : 'outline'
                          }
                          size="sm"
                          onClick={() => {
                            const currentTags = notes.tags;

                            if (currentTags.includes(quickTag)) {
                              setNotes({
                                ...notes,
                                tags: currentTags.filter((t) => t !== quickTag),
                              });
                            } else {
                              setNotes({
                                ...notes,
                                tags: [...currentTags, quickTag],
                              });
                            }
                          }}
                        >
                          {quickTag}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4">
                    <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                      Note
                    </div>
                    <div className="whitespace-pre-wrap text-sm leading-6 text-slate-200">
                      {player.note || 'Nessuna nota'}
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/25 p-4">
                    <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                      Tag
                    </div>
                    {player.tags && player.tags.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {player.tags.map((tag, idx) => (
                          <Badge key={idx} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-sm italic text-slate-600">
                        Nessun tag
                      </span>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Separator className="border-slate-800/60" />
        </main>
      </div>
    </div>
  );
}

export default PlayerDetail;
