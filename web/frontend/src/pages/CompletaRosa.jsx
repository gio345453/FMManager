import React, { useState, useEffect } from 'react';
import { Save, Trash2, Edit3, Plus, Search, Download, Upload, Library, Check, X } from 'lucide-react';
import { playersApi } from '../api/client';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import KpiCard from '../components/common/KpiCard';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';


const POSITIONS = Array.from({ length: 25 }, (_, i) => i + 1);

function CompletaRosa() {
  // Rosa state - array of 25 positions
  const [roster, setRoster] = useState(
    POSITIONS.map(pos => ({
      position: pos,
      player: null,
      customPrice: null
    }))
  );

  // Search state
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState(null);

  // Library state
  const [savedRosas, setSavedRosas] = useState([]);
  const [currentRosaName, setCurrentRosaName] = useState('');
  const [showLibrary, setShowLibrary] = useState(false);
  const [editingName, setEditingName] = useState(null);
  const [newName, setNewName] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSavedRosas();
  }, []);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (searchTerm.length >= 2) {
        setSearching(true);
        try {
          const res = await playersApi.getAll({ search: searchTerm });
          setSearchResults(res.data.slice(0, 20));
        } catch (err) {
          console.error('Search error:', err);
        }
        setSearching(false);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadSavedRosas = () => {
    try {
      const saved = JSON.parse(localStorage.getItem('completa_rosa_library') || '[]');
      setSavedRosas(saved);
    } catch (err) {
      console.error('Error loading saved rosas:', err);
    }
  };

  const handleAddPlayer = (position, player) => {
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
      customPrice: null
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
      customPrice: null
    };
    setRoster(updated);
  };

  const handleSetCustomPrice = (position, price) => {
    const updated = [...roster];
    updated[position - 1].customPrice = price;
    setRoster(updated);
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
        customPrice: r.customPrice
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
      roster: roster
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
          customPrice: null
        }))
      );
      setCurrentRosaName('');
    }
  };

  const getRoleColor = (ruolo) => {
    const colors = { P: 'var(--fm-warning)', D: 'var(--fm-success)', C: 'var(--fm-text-secondary)', A: 'var(--fm-danger)' };
    return colors[ruolo] || 'var(--fm-text)';
  };

  const calculateStats = () => {
    const filled = roster.filter(r => r.player !== null);
    const totalCost = filled.reduce((sum, r) => {
      const price = r.customPrice || r.player?.price_credits || 0;
      return sum + price;
    }, 0);
    const avgFM = filled.length > 0
      ? filled.reduce((sum, r) => sum + (r.player?.fm_weighted || 0), 0) / filled.length
      : 0;

    return {
      filled: filled.length,
      totalCost: totalCost.toFixed(1),
      avgFM: avgFM.toFixed(2),
      remaining: (500 - totalCost).toFixed(1)
    };
  };

  const stats = calculateStats();

  return (
    <div className="completarosa-page">
      <PageHeader
        title="Completa Rosa"
        description="Editor manuale rosa - 25 posizioni"
      />

      <main className="completarosa-content">
        {/* Stats */}
        <div className="completarosa-stats-grid">
          <KpiCard label="Giocatori" value={`${stats.filled}/25`} icon={Plus} />
          <KpiCard label="Costo Totale" value={`${stats.totalCost} cr`} icon={Save} />
          <KpiCard label="Budget Rimanente" value={`${stats.remaining} cr`} icon={Save} tone={parseFloat(stats.remaining) >= 0 ? 'success' : 'danger'} />
          <KpiCard label="Media FM" value={stats.avgFM} icon={Plus} />
        </div>

        {/* Actions Bar */}
        <div className="completarosa-actions-bar">
          <div className="completarosa-name-section">
            <Input
              placeholder="Nome rosa..."
              value={currentRosaName}
              onChange={(e) => setCurrentRosaName(e.target.value)}
              className="completarosa-name-input"
            />
            <Button type="button" onClick={handleSaveRosa} disabled={stats.filled === 0}>
              <Save className="h-4 w-4" />
              Salva
            </Button>
          </div>

          <div className="completarosa-actions-buttons">
            <Button type="button" variant="outline" onClick={() => setShowLibrary(!showLibrary)}>
              <Library className="h-4 w-4" />
              Libreria ({savedRosas.length})
            </Button>
            <Button type="button" variant="outline" onClick={handleExportRosa} disabled={stats.filled === 0}>
              <Download className="h-4 w-4" />
              Esporta
            </Button>
            <label htmlFor="import-file">
              <Button type="button" variant="outline" onClick={() => document.getElementById('import-file').click()}>
                <Upload className="h-4 w-4" />
                Importa
              </Button>
            </label>
            <input
              id="import-file"
              type="file"
              accept=".json"
              onChange={handleImportRosa}
              style={{ display: 'none' }}
            />
            <Button type="button" variant="outline" onClick={handleClearRosa} disabled={stats.filled === 0}>
              <Trash2 className="h-4 w-4" />
              Svuota
            </Button>
          </div>
        </div>

        {/* Library */}
        {showLibrary && (
          <div className="completarosa-library-section">
            <h3 className="completarosa-library-title">Rose Salvate</h3>
            {savedRosas.length === 0 ? (
              <EmptyState
                icon={Library}
                title="Nessuna rosa salvata"
                description="Crea e salva la tua prima rosa"
              />
            ) : (
              <div className="completarosa-library-list">
                {savedRosas.map((rosa, idx) => (
                  <div key={idx} className="completarosa-library-item">
                    <div className="completarosa-library-info">
                      {editingName === idx ? (
                        <div className="completarosa-rename-section">
                          <Input
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') handleRenameRosa(idx, newName);
                            }}
                            autoFocus
                          />
                          <Button type="button" size="sm" onClick={() => handleRenameRosa(idx, newName)}>
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button type="button" variant="ghost" size="sm" onClick={() => setEditingName(null)}>
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <span className="completarosa-library-name">{rosa.name}</span>
                          <div className="completarosa-library-meta">
                            <span className="completarosa-library-date">{new Date(rosa.date).toLocaleDateString()}</span>
                            <span className="completarosa-library-count">
                              {rosa.roster.filter(r => r.player).length} giocatori
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                    {editingName !== idx && (
                      <div className="completarosa-library-actions">
                        <Button type="button" size="sm" onClick={() => handleLoadRosa(rosa)}>Carica</Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingName(idx);
                            setNewName(rosa.name);
                          }}
                        >
                          <Edit3 className="h-3 w-3" />
                        </Button>
                        <Button type="button" variant="ghost" size="sm" onClick={() => handleDeleteRosa(idx)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Search Section */}
        {selectedPosition && (
          <div className="completarosa-search-section">
            <div className="completarosa-search-header">
              <h3 className="completarosa-search-title">Seleziona giocatore per posizione {selectedPosition}</h3>
              <Button type="button" variant="ghost" size="sm" onClick={() => {
                setSelectedPosition(null);
                setSearchTerm('');
                setSearchResults([]);
              }}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="completarosa-search-input-wrapper">
              <Search className="completarosa-search-icon" />
              <Input
                placeholder="Cerca giocatore per nome..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="completarosa-search-input"
              />
              {searching && <span className="completarosa-searching">Ricerca...</span>}
            </div>

            {searchResults.length > 0 && (
              <div className="completarosa-search-results">
                {searchResults.map(player => (
                  <div
                    key={player.id}
                    className="completarosa-search-result"
                    onClick={() => handleAddPlayer(selectedPosition, player)}
                  >
                    <div className="completarosa-search-result-info">
                      <span className="completarosa-search-result-name">{player.nome}</span>
                      <span className="completarosa-search-result-team">{player.squadra}</span>
                    </div>
                    <div className="completarosa-search-result-stats">
                      <Badge variant="outline" style={{ borderColor: getRoleColor(player.ruolo), color: getRoleColor(player.ruolo) }}>
                        {player.ruolo}
                      </Badge>
                      <span className="completarosa-search-result-fm">FM: {player.fm_weighted?.toFixed(2) || '-'}</span>
                      <span className="completarosa-search-result-price">{player.price_credits?.toFixed(1)} cr</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Roster Table */}
        <ResponsiveTable caption="Rosa completa - 25 posizioni">
          <thead>
            <tr className="completarosa-table-header">
              <th className="completarosa-th">Pos</th>
              <th className="completarosa-th">Nome</th>
              <th className="completarosa-th">Squadra</th>
              <th className="completarosa-th completarosa-th-center">Ruolo</th>
              <th className="completarosa-th completarosa-th-center">FM</th>
              <th className="completarosa-th completarosa-th-right">Prezzo</th>
              <th className="completarosa-th completarosa-th-right">Prezzo Custom</th>
              <th className="completarosa-th completarosa-th-right">Azioni</th>
            </tr>
          </thead>
          <tbody className="fm-table">
            {roster.map((slot) => (
              <tr key={slot.position} className="completarosa-table-row">
                <td className="completarosa-td">{slot.position}</td>
                {slot.player ? (
                  <>
                    <td className="completarosa-td completarosa-td-name">{slot.player.nome}</td>
                    <td className="completarosa-td">{slot.player.squadra}</td>
                    <td className="completarosa-td completarosa-td-center">
                      <Badge variant="outline" style={{ borderColor: getRoleColor(slot.player.ruolo), color: getRoleColor(slot.player.ruolo) }}>
                        {slot.player.ruolo}
                      </Badge>
                    </td>
                    <td className="completarosa-td completarosa-td-center">
                      {slot.player.fm_weighted?.toFixed(2) || '-'}
                    </td>
                    <td className="completarosa-td completarosa-td-right">
                      {slot.player.price_credits?.toFixed(1)} cr
                    </td>
                    <td className="completarosa-td completarosa-td-right">
                      <Input
                        type="number"
                        step="0.5"
                        min="1"
                        max="200"
                        placeholder="Custom..."
                        value={slot.customPrice || ''}
                        onChange={(e) => handleSetCustomPrice(slot.position, e.target.value ? parseFloat(e.target.value) : null)}
                        className="completarosa-price-input"
                      />
                    </td>
                    <td className="completarosa-td completarosa-td-right">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemovePlayer(slot.position)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="completarosa-td completarosa-empty" colSpan="6">
                      <EmptyState
                        icon={Plus}
                        title=""
                        description="Posizione vuota"
                        compact
                      />
                    </td>
                    <td className="completarosa-td completarosa-td-right">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedPosition(slot.position)}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </ResponsiveTable>
      </main>
    </div>
  );
}

export default CompletaRosa;
