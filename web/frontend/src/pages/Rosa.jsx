import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Lock, Unlock, Ban, Save, Download, Upload, Settings, Zap, Check, X, Edit3, Library, Star, Shield } from 'lucide-react';
import { playersApi } from '../api/client';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { useAppContext } from '../context/AppContext';
import { formatTitolarita } from '../utils/formatters';
import { PlayerAvatar, TeamLogo } from '../components/common/PlayerMedia';
import { readMediaPreference } from '../utils/playerMedia';


// Helper to generate POSITIONS and POSITION_ROLES from composition
const generatePositions = (composition) => {
  const totalSlots = composition.P + composition.D + composition.C + composition.A;
  const positions = Array.from({ length: totalSlots }, (_, i) => i + 1);

  const positionRoles = {};
  let currentPos = 1;

  // Assign roles based on composition
  for (let i = 0; i < composition.P; i++) positionRoles[currentPos++] = 'P';
  for (let i = 0; i < composition.D; i++) positionRoles[currentPos++] = 'D';
  for (let i = 0; i < composition.C; i++) positionRoles[currentPos++] = 'C';
  for (let i = 0; i < composition.A; i++) positionRoles[currentPos++] = 'A';

  return { positions, positionRoles, totalSlots };
};

function Rosa() {
  const { settings, players: allPlayers, toggleFavorite } = useAppContext();

  // Get composition from settings or use default
  const composition = settings?.roster_composition || { P: 3, D: 8, C: 8, A: 6 };
  const { positions: POSITIONS, positionRoles: POSITION_ROLES, totalSlots: TOTAL_SLOTS } = generatePositions(composition);

  // Roster state - array of 25 positions
  const [roster, setRoster] = useState(
    POSITIONS.map(pos => ({
      position: pos,
      player: null,
      customPrice: null,
      locked: false
    }))
  );

  // Search state
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState(null);

  // Optimizer config state
  const [showOptimizerConfig, setShowOptimizerConfig] = useState(false);
  const [optimizerConfig, setOptimizerConfig] = useState({
    budget: settings?.budget || 500,
    budgetPerRole: { P: 15, D: 30, C: 30, A: 25 },
    valuePriority: 'FM',
    pricePercentage: 100
  });

  // Blacklist state (session-based)
  const [blacklistedIds, setBlacklistedIds] = useState([]);

  // Aggiorna budget quando cambiano le settings
  useEffect(() => {
    if (settings?.budget) {
      setOptimizerConfig(prev => ({
        ...prev,
        budget: settings.budget
      }));
    }
  }, [settings]);

  // Library state
  const [savedRosas, setSavedRosas] = useState([]);
  const [currentRosaName, setCurrentRosaName] = useState('');
  const [showLibrary, setShowLibrary] = useState(false);
  const [editingName, setEditingName] = useState(null);
  const [newName, setNewName] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showMedia] = useState(() => readMediaPreference());

  useEffect(() => {
    const initializeData = () => {
      loadSavedRosas();
      loadSessionData();
      setIsInitialized(true);
    };
    initializeData();
  }, []);

  // Save to session when any state changes (but only after initialization)
  useEffect(() => {
    if (isInitialized) {
      saveSessionData();
    }
  }, [roster, currentRosaName, blacklistedIds, optimizerConfig, showOptimizerConfig, showLibrary, isInitialized]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (searchTerm.length >= 2 && selectedPosition) {
        setSearching(true);
        try {
          const requiredRole = POSITION_ROLES[selectedPosition];

          // Chiediamo direttamente al backend solo giocatori compatibili
          // con il ruolo dello slot selezionato.
          const res = await playersApi.getAll({
            search: searchTerm,
            role: requiredRole,
          });

          // Guard di sicurezza lato frontend: anche se il backend dovesse
          // restituire dati fuori filtro, non devono mai essere mostrati.
          const compatiblePlayers = (res.data || []).filter((player) => {
            const playerRole = String(player.ruolo || '').trim().toUpperCase();
            return playerRole === requiredRole ||
              playerRole.startsWith(`${requiredRole}/`) ||
              playerRole.includes(`/${requiredRole}`);
          });

          setSearchResults(compatiblePlayers.slice(0, 20));
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
  }, [searchTerm, selectedPosition]);

  const loadSavedRosas = () => {
    try {
      const saved = JSON.parse(localStorage.getItem('completa_rosa_library') || '[]');
      setSavedRosas(saved);
    } catch (err) {
      console.error('Error loading saved rosas:', err);
    }
  };

  const loadSessionData = () => {
    try {
      const saved = sessionStorage.getItem('rosa_session');
      if (saved) {
        const data = JSON.parse(saved);
        if (data.roster) setRoster(data.roster);
        if (data.currentRosaName) setCurrentRosaName(data.currentRosaName);
        if (data.blacklistedIds) setBlacklistedIds(data.blacklistedIds);
        if (data.optimizerConfig) setOptimizerConfig(data.optimizerConfig);
        if (data.showOptimizerConfig !== undefined) setShowOptimizerConfig(data.showOptimizerConfig);
        if (data.showLibrary !== undefined) setShowLibrary(data.showLibrary);
      }
    } catch (err) {
      console.error('Error loading session data:', err);
    }
  };

  const saveSessionData = () => {
    try {
      sessionStorage.setItem('rosa_session', JSON.stringify({
        roster,
        currentRosaName,
        blacklistedIds,
        optimizerConfig,
        showOptimizerConfig,
        showLibrary
      }));
    } catch (err) {
      console.error('Error saving session data:', err);
    }
  };

  const handleAddPlayer = (position, player) => {
    const requiredRole = POSITION_ROLES[position];
    const playerRole = String(player?.ruolo || '').trim().toUpperCase();

    const roleMatches =
      playerRole === requiredRole ||
      playerRole.startsWith(`${requiredRole}/`) ||
      playerRole.includes(`/${requiredRole}`);

    if (!roleMatches) {
      console.warn(`Tentativo di inserire un giocatore ${player?.ruolo || '-'} in uno slot ${requiredRole}.`);
      return;
    }

    const updated = [...roster];
    updated[position - 1] = {
      position,
      player: {
        id: player.id,
        nome: player.nome,
        squadra: player.squadra,
        ruolo: player.ruolo,
        fm_weighted: player.fm_weighted,
        price_percentage: player.price_percentage,
        price_credits: player.price_credits
      },
      customPrice: null,
      locked: false
    };
    setRoster(updated);
    setSelectedPosition(null);
    setSearchTerm('');
    setSearchResults([]);
  };

  const handleRemovePlayer = (position) => {
    const updated = [...roster];
    updated[position - 1] = {
      position,
      player: null,
      customPrice: null,
      locked: false
    };
    setRoster(updated);
  };

  const handleToggleLock = (position) => {
    const updated = [...roster];
    updated[position - 1].locked = !updated[position - 1].locked;
    setRoster(updated);
  };

  const handleDiscardPlayer = (position) => {
    const slot = roster[position - 1];
    if (slot.player) {
      // Add to blacklist for this session
      setBlacklistedIds(prev => [...prev, slot.player.id]);
      handleRemovePlayer(position);
    }
  };

  const handleSetCustomPrice = (position, price) => {
    const updated = [...roster];
    updated[position - 1].customPrice = price;
    setRoster(updated);
  };

  const handleGenerateRosa = async () => {
    setOptimizing(true);
    setError(null);

    try {
      // Prepare locked players
      const selectedPlayers = {};
      const customCredits = {};

      roster.forEach(slot => {
        if (slot.player && slot.locked) {
          selectedPlayers[slot.position - 1] = {
            id: slot.player.id,
            nome: slot.player.nome,
            squadra: slot.player.squadra,
            ruolo: slot.player.ruolo
          };

          if (slot.customPrice) {
            customCredits[slot.position - 1] = parseFloat(slot.customPrice);
          }
        }
      });

      const composition = settings?.roster_composition || { P: 3, D: 8, C: 8, A: 6 };

      const response = await fetch('/api/optimizer/build-rosa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget: optimizerConfig.budget,
          composition,
          budget_per_role: optimizerConfig.budgetPerRole,
          value_priority: optimizerConfig.valuePriority,
          price_percentage: optimizerConfig.pricePercentage,
          selected_players: selectedPlayers,
          custom_credits: customCredits,
          blacklisted_player_ids: blacklistedIds
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'Errore generazione rosa';
        throw new Error(errorMessage);
      }

      const result = await response.json();

      // Update roster with generated players
      const updated = [...roster];

      result.players.forEach(player => {
        const pos = player.position + 1; // API uses 0-indexed
        if (!updated[pos - 1].locked) {
          updated[pos - 1] = {
            position: pos,
            player: {
              id: player.id,
              nome: player.nome,
              squadra: player.squadra,
              ruolo: player.ruolo,
              fm_weighted: player.fm_weighted,
              price_credits: player.price_credits
            },
            customPrice: null,
            locked: false
          };
        }
      });

      setRoster(updated);
      setShowOptimizerConfig(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setOptimizing(false);
    }
  };

  const handleSaveRosa = () => {
    if (!currentRosaName.trim()) {
      alert('Inserisci un nome per la rosa');
      return;
    }

    const filledPositions = roster.filter(r => r.player !== null);
    if (filledPositions.length === 0) {
      alert('Aggiungi almeno un giocatore');
      return;
    }

    const rosaData = {
      name: currentRosaName,
      date: new Date().toISOString(),
      roster: roster.map(r => ({
        position: r.position,
        player: r.player,
        customPrice: r.customPrice,
        locked: r.locked
      }))
    };

    const updated = [...savedRosas, rosaData];
    localStorage.setItem('completa_rosa_library', JSON.stringify(updated));
    setSavedRosas(updated);
    alert('Rosa salvata!');
  };

  const handleLoadRosa = (rosa) => {
    setRoster(rosa.roster);
    setCurrentRosaName(rosa.name);
    setShowLibrary(false);
  };

  const handleDeleteRosa = (index) => {
    if (confirm('Eliminare questa rosa?')) {
      const updated = savedRosas.filter((_, i) => i !== index);
      localStorage.setItem('completa_rosa_library', JSON.stringify(updated));
      setSavedRosas(updated);
    }
  };

  const handleRenameRosa = (index, newName) => {
    if (!newName.trim()) return;

    const updated = [...savedRosas];
    updated[index].name = newName;
    localStorage.setItem('completa_rosa_library', JSON.stringify(updated));
    setSavedRosas(updated);
    setEditingName(null);
    setNewName('');
  };

  const handleExportRosa = () => {
    const filledPositions = roster.filter(r => r.player !== null);
    if (filledPositions.length === 0) {
      alert('Nessun giocatore da esportare');
      return;
    }

    const exportData = {
      name: currentRosaName || 'rosa',
      date: new Date().toISOString(),
      roster
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `${currentRosaName || 'rosa'}_${Date.now()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImportRosa = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        if (parsed.roster && Array.isArray(parsed.roster)) {
          setRoster(parsed.roster);
          setCurrentRosaName(parsed.name || '');
          alert('Rosa importata!');
        } else {
          alert('Formato file non valido');
        }
      } catch (err) {
        alert('Errore lettura file');
      }
    };
    reader.readAsText(file);
  };

  const handleClearRosa = () => {
    if (confirm('Svuotare completamente la rosa?')) {
      setRoster(
        POSITIONS.map(pos => ({
          position: pos,
          player: null,
          customPrice: null,
          locked: false
        }))
      );
      setCurrentRosaName('');
      setBlacklistedIds([]);
      sessionStorage.removeItem('rosa_session');
    }
  };

  const getRoleColor = (ruolo) => {
    const colors = {
      P: 'var(--fm-warning)',
      D: 'var(--fm-info)',
      C: 'var(--fm-success)',
      A: 'var(--fm-danger)'
    };
    return colors[ruolo] || 'var(--fm-text)';
  };

  const getPlayerDetails = (slot) => {
    if (!slot?.player) return null;
    const source = allPlayers?.find((p) => p.id === slot.player.id);
    return source ? { ...slot.player, ...source } : slot.player;
  };

  const handleToggleFavorite = async (playerId, event) => {
    event?.stopPropagation?.();
    try {
      await toggleFavorite(playerId);
    } catch (err) {
      console.error('Errore nel toggle del preferito:', err);
    }
  };

  const getDisplayRole = (role) => role?.split('/')?.[0] || role || '';

  const calculateStats = () => {
    const filled = roster.filter(r => r.player !== null);
    const locked = roster.filter(r => r.locked && r.player !== null);
    const totalCost = filled.reduce((sum, r) => {
      const price = r.customPrice || r.player?.price_credits || 0;
      return sum + price;
    }, 0);
    const avgFM = filled.length > 0
      ? filled.reduce((sum, r) => sum + (r.player?.fm_weighted || 0), 0) / filled.length
      : 0;

    return {
      filled: filled.length,
      locked: locked.length,
      totalCost: totalCost.toFixed(1),
      avgFM: avgFM.toFixed(2),
      remaining: (optimizerConfig.budget - totalCost).toFixed(1)
    };
  };

  const stats = calculateStats();

  if (loading) return <LoadingState message="Caricamento..." className="rosa-state" />;
  if (error && !optimizing) return <ErrorState title="Errore" message={error} onRetry={() => setError(null)} className="rosa-state" />;

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <main className="space-y-5">
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ['Giocatori', `${stats.filled}/${TOTAL_SLOTS}`, 'bg-sky-400/10 text-sky-300 border-sky-400/15', Plus],
              ['Bloccati', stats.locked, 'bg-amber-400/10 text-amber-300 border-amber-400/15', Lock],
              ['Costo totale', `${stats.totalCost} cr`, 'bg-emerald-400/10 text-emerald-300 border-emerald-400/15', Save, `${stats.remaining} cr rimasti`],
              ['Media FM', stats.avgFM, 'bg-blue-400/10 text-blue-300 border-blue-400/15', Zap],
            ].map(([label, value, iconStyle, Icon, secondary]) => (
              <div
                key={label}
                className="rounded-2xl border border-slate-800/90 bg-[#0F172A] p-4 shadow-[0_8px_24px_rgba(0,0,0,0.14)]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</div>
                    <div className="mt-2 text-2xl font-bold tracking-tight text-slate-100">{value}</div>
                    {secondary && (
                      <div className={`mt-0.5 text-xs font-medium ${parseFloat(stats.remaining) >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
                        {secondary}
                      </div>
                    )}
                  </div>
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${iconStyle}`}>
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                </div>
              </div>
            ))}
          </section>

          <section className="relative overflow-hidden rounded-2xl border border-slate-800/90 bg-[#0F172A] shadow-[0_10px_30px_rgba(0,0,0,0.16)]">
            <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/35 to-transparent" />
            <div className="flex flex-col gap-4 p-4 sm:p-5 xl:flex-row xl:items-end xl:justify-between">
              <div className="min-w-0">
                <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Rosa</div>
                <div className="mt-1 text-lg font-semibold text-slate-100">{currentRosaName || 'Nuova rosa'}</div>
                <div className="mt-0.5 text-xs text-slate-500">Gestisci i giocatori e prepara la rosa per l'ottimizzatore.</div>
                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
                  <Input
                    placeholder="Nome rosa..."
                    value={currentRosaName}
                    onChange={(e) => setCurrentRosaName(e.target.value)}
                    className="h-10 max-w-md border-slate-700 bg-slate-950/60"
                    aria-label="Nome della rosa"
                  />
                  <Button type="button" onClick={handleSaveRosa} disabled={stats.filled === 0}>
                    <Save className="h-4 w-4" aria-hidden="true" />
                    Salva rosa
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 xl:max-w-[640px] xl:justify-end">
                <Button type="button" onClick={() => setShowOptimizerConfig(true)} disabled={optimizing}>
                  <Zap className="h-4 w-4" aria-hidden="true" />
                  {optimizing ? 'Generazione...' : 'Genera Rosa'}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowLibrary(!showLibrary)}>
                  <Library className="h-4 w-4" aria-hidden="true" />
                  Libreria <span className="rounded-full bg-slate-800 px-1.5 py-0.5 text-[10px]">{savedRosas.length}</span>
                </Button>
                <Button type="button" variant="outline" onClick={handleExportRosa} disabled={stats.filled === 0}>
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Esporta
                </Button>
                <Button type="button" variant="outline" onClick={() => document.getElementById('import-file').click()}>
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Importa
                </Button>
                <input id="import-file" type="file" accept=".json" onChange={handleImportRosa} className="hidden" />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClearRosa}
                  disabled={stats.filled === 0}
                  className="text-red-300 hover:border-red-400/30 hover:bg-red-400/10 hover:text-red-200"
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                  Svuota
                </Button>
              </div>
            </div>
          </section>

          {blacklistedIds.length > 0 && (
            <Alert className="border-amber-400/20 bg-amber-400/[0.05]">
              <Ban className="h-4 w-4 text-amber-300" aria-hidden="true" />
              <AlertDescription className="text-amber-100">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{blacklistedIds.length} giocatori scartati ed esclusi dalla generazione automatica.</span>
                  <Button type="button" variant="ghost" size="sm" onClick={() => setBlacklistedIds([])} className="text-amber-200">
                    Reset blacklist
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {showLibrary && (
            <section className="rounded-2xl border border-violet-400/15 bg-[#0F172A] p-4 shadow-[0_8px_24px_rgba(0,0,0,0.12)] sm:p-5">
              <div className="mb-4 flex items-end justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">Rose salvate</div>
                  <div className="mt-0.5 text-xs text-slate-500">Richiama, rinomina o elimina una configurazione.</div>
                </div>
                <Badge variant="secondary">{savedRosas.length}</Badge>
              </div>
              {savedRosas.length === 0 ? (
                <EmptyState icon={Library} title="Nessuna rosa salvata" description="Crea e salva la tua prima rosa" />
              ) : (
                <div className="grid gap-2.5 lg:grid-cols-2">
                  {savedRosas.map((rosa, idx) => (
                    <div key={idx} className="flex flex-col gap-3 rounded-xl border border-slate-800/80 bg-slate-950/25 p-3.5 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        {editingName === idx ? (
                          <div className="flex gap-2">
                            <Input value={newName} onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleRenameRosa(idx, newName)} autoFocus className="h-9" />
                            <Button type="button" size="sm" onClick={() => handleRenameRosa(idx, newName)}><Check className="h-3.5 w-3.5" /></Button>
                            <Button type="button" variant="ghost" size="sm" onClick={() => setEditingName(null)}><X className="h-3.5 w-3.5" /></Button>
                          </div>
                        ) : (
                          <>
                            <div className="truncate text-sm font-semibold text-slate-100">{rosa.name}</div>
                            <div className="mt-1 flex gap-3 text-xs text-slate-500">
                              <span>{new Date(rosa.date).toLocaleDateString()}</span>
                              <span>{rosa.roster.filter(r => r.player).length} giocatori</span>
                            </div>
                          </>
                        )}
                      </div>
                      {editingName !== idx && (
                        <div className="flex shrink-0 items-center gap-1.5">
                          <Button type="button" size="sm" onClick={() => handleLoadRosa(rosa)}>Carica</Button>
                          <Button type="button" variant="ghost" size="icon" onClick={() => { setEditingName(idx); setNewName(rosa.name); }} aria-label={`Rinomina ${rosa.name}`}><Edit3 className="h-4 w-4" /></Button>
                          <Button type="button" variant="ghost" size="icon" onClick={() => handleDeleteRosa(idx)} aria-label={`Elimina ${rosa.name}`} className="text-red-300 hover:bg-red-400/10"><Trash2 className="h-4 w-4" /></Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {selectedPosition && (
            <section className="relative overflow-visible rounded-2xl border border-sky-400/20 bg-[#0F172A] p-4 shadow-[0_10px_30px_rgba(0,0,0,0.15)] sm:p-5">
              <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-sky-400/70 to-transparent" />
              <div className="flex items-end justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Inserimento giocatore</div>
                  <h2 className="mt-1 text-sm font-semibold text-slate-100">
                    Posizione {selectedPosition}
                    <span className="ml-2 rounded-full border border-slate-700 bg-slate-950/40 px-2 py-0.5 text-[10px] text-slate-300">{POSITION_ROLES[selectedPosition]}</span>
                  </h2>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={() => { setSelectedPosition(null); setSearchTerm(''); setSearchResults([]); }}>
                  <X className="h-4 w-4" aria-hidden="true" /> Chiudi
                </Button>
              </div>
              <div className="relative mt-4">
                <Input placeholder="Cerca giocatore per nome..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="h-11 border-slate-700 bg-slate-950/65" autoFocus />
                {searching && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] text-slate-500">Ricerca...</span>}
              </div>
              {searchResults.length > 0 && (
                <div className="mt-2 grid gap-2">
                  {searchResults.map(player => (
                    <button key={player.id} type="button" onClick={() => handleAddPlayer(selectedPosition, player)} className="group flex w-full items-center gap-3 rounded-xl border border-slate-800/80 bg-[#111827] p-3 text-left hover:border-emerald-400/35 hover:bg-emerald-400/[0.06]">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-xs font-bold" style={{ borderColor: getRoleColor(player.ruolo), color: getRoleColor(player.ruolo) }}>{player.ruolo}</div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-semibold text-white">{player.nome}</div>
                        <div className="mt-0.5 truncate text-xs text-slate-400">{player.squadra}</div>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <span className="text-sm font-semibold text-sky-300">{player.fm_weighted?.toFixed(2) || '-'}</span>
                        <span className="rounded-full bg-slate-950 px-2 py-1 text-xs font-semibold text-amber-300">{player.price_credits?.toFixed(1)} cr</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>
          )}

          <section className="overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0F172A] shadow-[0_12px_34px_rgba(0,0,0,0.18)]">
            <div className="flex flex-col gap-2 border-b border-slate-700/80 bg-slate-950/20 px-4 py-4 sm:flex-row sm:items-end sm:justify-between sm:px-5">
              <div>
                <div className="text-sm font-semibold text-slate-100">Composizione rosa</div>
              </div>
              <Badge variant="secondary">{stats.filled}/{TOTAL_SLOTS} completata</Badge>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-[1750px] w-full">
                <thead>
                  <tr>
                    <th className="w-28 border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Azioni
                    </th>
                    <th className="w-12 border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-center"><Star className="mx-auto h-4 w-4 text-slate-600" aria-hidden="true" /></th>
                    {['Overall','Nome','Squadra','Ruolo','Tag','FM','MV','PV','Gol','Assist','Tit%','Prezzo %','Crediti','Prezzo personalizzato'].map((label) => (
                      <th key={label} className={`border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 ${['FM','MV','PV','Gol','Assist','Tit%','Prezzo %','Crediti','Prezzo personalizzato'].includes(label) ? 'text-right' : 'text-left'}`}>
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {roster.map((slot, index) => {
                    const player = getPlayerDetails(slot);
                    const displayRole = getDisplayRole(player?.ruolo || POSITION_ROLES[slot.position]);
                    const slotRole = POSITION_ROLES[slot.position];
                    const previousRole = index > 0 ? POSITION_ROLES[roster[index - 1].position] : null;
                    const roleLabels = {
                      P: 'Portieri',
                      D: 'Difensori',
                      C: 'Centrocampisti',
                      A: 'Attaccanti',
                    };
                    const roleSlots = roster.filter((item) => POSITION_ROLES[item.position] === slotRole);
                    const roleFilled = roleSlots.filter((item) => item.player).length;
                    const showRoleHeader = slotRole !== previousRole;

                    return (
                      <React.Fragment key={slot.position}>
                        {showRoleHeader && (
                          <tr>
                            <td colSpan="15" className="border-y border-slate-800 bg-slate-950/75 px-4 py-3.5">
                              <div className="flex items-center justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <Badge
                                    variant="outline"
                                    style={{ borderColor: getRoleColor(slotRole), color: getRoleColor(slotRole) }}
                                    className="font-semibold"
                                  >
                                    {slotRole}
                                  </Badge>
                                  <div>
                                    <div className="text-sm font-semibold text-slate-100">{roleLabels[slotRole]}</div>
                                    <div className="text-[11px] text-slate-500">
                                      {roleFilled}/{roleSlots.length} completati · {roleSlots.length - roleFilled} slot liberi
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                        <tr key={`${slot.position}-row` } className={`border-b border-slate-800/60 transition-colors ${slot.locked ? 'bg-amber-400/[0.04]' : 'hover:bg-slate-900/70'}`}>
                        <td className="px-3 py-3.5 text-center">
                          {player ? (
                            <div className="inline-flex items-center gap-1">
                              <Button type="button" variant="ghost" size="icon" onClick={() => handleToggleLock(slot.position)} title={slot.locked ? 'Sblocca' : 'Blocca'} className={slot.locked ? 'text-amber-300' : 'text-slate-500'}>{slot.locked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}</Button>
                              <Button type="button" variant="ghost" size="icon" onClick={() => handleDiscardPlayer(slot.position)} title="Scarta (blacklist)" className="text-slate-500 hover:text-amber-300"><Ban className="h-4 w-4" /></Button>
                              <Button type="button" variant="ghost" size="icon" onClick={() => handleRemovePlayer(slot.position)} title="Rimuovi" className="text-slate-500 hover:text-red-300"><Trash2 className="h-4 w-4" /></Button>
                            </div>
                          ) : (
                            <span className="text-slate-700">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3.5 text-center">
                          {player && (
                            <button type="button" onClick={(e) => handleToggleFavorite(player.id, e)} className="rounded-lg border-0 bg-transparent p-2 text-amber-400 transition hover:bg-transparent hover:text-amber-300 focus-visible:bg-transparent" aria-label={player.is_favorite ? 'Rimuovi da preferiti' : 'Aggiungi ai preferiti'}>
                              <Star className={`h-4 w-4 ${player.is_favorite ? 'fill-amber-400 text-amber-400' : 'fill-transparent text-amber-400'}`} aria-hidden="true" />
                            </button>
                          )}
                        </td>
                        {player ? (
                          <>
                            <td className="px-3 py-3.5 text-base font-bold text-sky-400">{player.overall || 'N/A'}</td>
                            <td className="px-3 py-3.5">
                              <div className="flex items-center gap-3">
                                {showMedia && <div className="shrink-0"><PlayerAvatar playerId={player.id} size="small" /></div>}
                                <div className="min-w-0"><div className="flex items-center gap-2 truncate font-semibold text-slate-100">{slot.locked && <Lock className="h-3.5 w-3.5 shrink-0 text-amber-300" />}<span className="truncate">{player.nome}</span></div></div>
                                {(displayRole === 'P' || displayRole === 'D') && player.mv_weighted >= 6.0 && <Shield className="h-4 w-4 shrink-0 text-sky-400" aria-hidden="true" title="Defense Modifier attivo" />}
                              </div>
                            </td>
                            <td className="px-3 py-3.5"><div className="flex items-center gap-2 text-sm text-slate-400">{showMedia && <TeamLogo teamName={player.squadra} size={24} />}<span>{player.squadra || '-'}</span></div></td>
                            <td className="px-3 py-3.5">
                              {player.ruolo?.includes('/') ? <div className="flex items-center gap-1.5">{player.ruolo.split('/').map((role, idx) => <Badge key={`${slot.position}-${idx}`} variant="outline" style={{ borderColor: getRoleColor(role), color: getRoleColor(role) }}>{role}</Badge>)}</div> : <Badge variant="outline" style={{ borderColor: getRoleColor(displayRole), color: getRoleColor(displayRole) }}>{player.ruolo || displayRole || '-'}</Badge>}
                            </td>
                            <td className="px-3 py-3.5">{player.tags?.length ? <div className="flex max-w-48 flex-wrap gap-1.5">{player.tags.map((tag, idx) => <Badge key={`${slot.position}-tag-${idx}`} variant={tag === 'rigorista' ? 'default' : 'secondary'} className="text-[10px]">{tag}</Badge>)}</div> : <span className="text-slate-700">-</span>}</td>
                            <td className="px-3 py-3.5 text-right text-sm font-semibold text-slate-100">{player.fm_weighted?.toFixed(2) || '-'}</td>
                            <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.mv_weighted?.toFixed(2) || '-'}</td>
                            <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.pv_weighted?.toFixed(1) || '-'}</td>
                            <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.gf_weighted?.toFixed(1) || '-'}</td>
                            <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.ass_weighted?.toFixed(1) || '-'}</td>
                            <td className="px-3 py-3.5 text-right text-sm text-slate-300">{formatTitolarita(player.titolarita)}</td>
                            <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_percentage?.toFixed(1) || '-'}%</td>
                            <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_credits?.toFixed(0) || '-'}</td>
                            <td className="px-3 py-3.5 text-right"><Input type="number" step="0.5" min="1" max="200" placeholder="—" value={slot.customPrice || ''} onChange={(e) => handleSetCustomPrice(slot.position, e.target.value ? parseFloat(e.target.value) : null)} className="ml-auto h-8 w-28 border-slate-700 bg-slate-950/50 text-right" /></td>
                          </>
                        ) : (
                          <td className="px-3 py-3.5" colSpan="15"><button type="button" onClick={() => setSelectedPosition(slot.position)} className="group flex w-full items-center gap-2 rounded-xl border border-slate-800/80 bg-slate-950/35 px-3 py-2.5 text-left shadow-inner shadow-black/10 transition-all duration-200 hover:border-sky-400/30 hover:bg-sky-400/[0.05]"><div className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-800/90 bg-slate-900/70 text-slate-500 transition-colors group-hover:border-sky-400/30 group-hover:bg-sky-400/10 group-hover:text-sky-300"><Plus className="h-4 w-4" /></div><span className="text-xs font-medium text-slate-500 transition-colors group-hover:text-slate-200">Posizione {slot.position} · aggiungi giocatore</span></button></td>
                        )}
                        </tr>
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>

      {showOptimizerConfig && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/75 p-4 backdrop-blur-sm" onClick={() => setShowOptimizerConfig(false)}>
          <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-2xl border border-slate-700/80 bg-[#0F172A] shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
              <div>
                <div className="text-base font-semibold text-slate-100">Configurazione generazione</div>
                <div className="mt-0.5 text-xs text-slate-500">Imposta i parametri dell'ottimizzatore.</div>
              </div>
              <Button type="button" variant="ghost" size="icon" onClick={() => setShowOptimizerConfig(false)}><X className="h-4 w-4" /></Button>
            </div>
            <div className="space-y-5 p-5">
              <div>
                <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Budget totale</label>
                <Input type="number" value={optimizerConfig.budget} onChange={(e) => setOptimizerConfig({ ...optimizerConfig, budget: parseFloat(e.target.value) })} />
              </div>
              <div>
                <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Budget per ruolo (%)</div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ['P','Portieri'],['D','Difensori'],['C','Centrocampisti'],['A','Attaccanti'],
                  ].map(([role,label]) => (
                    <div key={role}>
                      <label className="mb-1.5 block text-xs text-slate-400">{label}</label>
                      <Input type="number" value={optimizerConfig.budgetPerRole[role]} onChange={(e) => setOptimizerConfig({ ...optimizerConfig, budgetPerRole: { ...optimizerConfig.budgetPerRole, [role]: parseFloat(e.target.value) } })} />
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Priorità valutazione</label>
                <div className="relative overflow-hidden rounded-lg">
                  <div className="absolute inset-x-0 top-0 z-10 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
                  <select value={optimizerConfig.valuePriority} onChange={(e) => setOptimizerConfig({ ...optimizerConfig, valuePriority: e.target.value })} className="h-10 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100 outline-none">
                    <option value="FM">FM (Fantamedia)</option><option value="MV">MV (Media Voto)</option><option value="PV">PV (Punteggio Voto)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Percentuale prezzo</label>
                <Input type="number" min="60" max="140" value={optimizerConfig.pricePercentage} onChange={(e) => setOptimizerConfig({ ...optimizerConfig, pricePercentage: parseFloat(e.target.value) })} />
                <p className="mt-1 text-xs text-slate-600">60–140% del prezzo base</p>
              </div>
              <Alert className="border-sky-400/15 bg-sky-400/[0.04]">
                <Settings className="h-4 w-4 text-sky-300" />
                <AlertDescription>I giocatori bloccati rimarranno fissi. I giocatori scartati ({blacklistedIds.length}) saranno esclusi.{stats.locked > 0 && ` ${stats.locked} giocatori bloccati.`}</AlertDescription>
              </Alert>
            </div>
            <div className="flex flex-col-reverse gap-2 border-t border-slate-800 px-5 py-4 sm:flex-row sm:justify-end">
              <Button type="button" variant="outline" onClick={() => setShowOptimizerConfig(false)}>Annulla</Button>
              <Button type="button" onClick={handleGenerateRosa} disabled={optimizing}><Zap className="h-4 w-4" />{optimizing ? 'Generazione...' : 'Genera'}</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Rosa;
