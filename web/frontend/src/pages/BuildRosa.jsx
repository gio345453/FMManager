import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Download, RotateCcw, TrendingUp, Users, DollarSign } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import KpiCard from '../components/common/KpiCard';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { useAppContext } from '../context/AppContext';


function BuildRosa() {
  const navigate = useNavigate();
  const { settings } = useAppContext();

  // State - usa settings per i valori iniziali
  const defaultComposition = settings?.roster_composition || { P: 3, D: 8, C: 8, A: 6 };
  const defaultBudget = settings?.budget || 500;

  const [budget, setBudget] = useState(defaultBudget);
  const [composition, setComposition] = useState(defaultComposition);
  const [budgetPerRole, setBudgetPerRole] = useState({ P: 15, D: 30, C: 30, A: 25 });
  const [valuePriority, setValuePriority] = useState('FM');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Aggiorna quando cambiano le settings
  useEffect(() => {
    if (settings?.budget) setBudget(settings.budget);
    if (settings?.roster_composition) setComposition(settings.roster_composition);
  }, [settings]);

  const handleGenerate = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/optimizer/build-rosa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget,
          composition,
          budget_per_role: budgetPerRole,
          value_priority: valuePriority
        })
      });

      if (!response.ok) {
        throw new Error('Errore generazione rosa');
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
    setBudget(settings?.budget || 500);
    setComposition(settings?.roster_composition || { P: 3, D: 8, C: 8, A: 6 });
    setBudgetPerRole({ P: 15, D: 30, C: 30, A: 25 });
    setValuePriority('FM');
    setResult(null);
    setError(null);
  };

  const handleExport = () => {
    if (!result) return;

    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `rosa_${Date.now()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const getRoleColor = (ruolo) => {
    const colors = {
      P: 'var(--fm-warning)',
      D: 'var(--fm-success)',
      C: 'var(--fm-text-secondary)',
      A: 'var(--fm-danger)'
    };
    return colors[ruolo] || 'var(--fm-text)';
  };

  if (loading) return <LoadingState message="Generazione rosa in corso..." className="buildrosa-state" />;

  return (
    <div className="buildrosa-page">
      <PageHeader
        title="Genera Rosa"
        description="Ottimizza la tua rosa con l'algoritmo knapsack"
      />

      <main className="buildrosa-content">
        {error && !result && (
          <ErrorState
            title="Errore generazione"
            message={error}
            onRetry={handleGenerate}
            className="buildrosa-state"
          />
        )}

        {!result && (
          <div className="buildrosa-config-section">
            <div className="buildrosa-config-card">
              <h2 className="buildrosa-config-title">Configurazione Rosa</h2>

              {/* Budget */}
              <div className="buildrosa-form-group">
                <label htmlFor="budget" className="buildrosa-label">Budget Totale: {budget} crediti</label>
                <Input
                  id="budget"
                  type="range"
                  min="100"
                  max="2000"
                  step="50"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="buildrosa-slider"
                />
              </div>

              {/* Composition */}
              <div className="buildrosa-form-group">
                <label className="buildrosa-label">Composizione Rosa</label>
                <div className="buildrosa-composition-grid">
                  {['P', 'D', 'C', 'A'].map(role => (
                    <div key={role} className="buildrosa-composition-item">
                      <label htmlFor={`comp-${role}`} className="buildrosa-role-label" style={{ color: getRoleColor(role) }}>
                        {role}
                      </label>
                      <Input
                        id={`comp-${role}`}
                        type="number"
                        min="1"
                        max="15"
                        value={composition[role]}
                        onChange={(e) => setComposition({ ...composition, [role]: Number(e.target.value) })}
                      />
                    </div>
                  ))}
                </div>
                <p className="buildrosa-help-text">
                  Totale: {Object.values(composition).reduce((a, b) => a + b, 0)} giocatori
                </p>
              </div>

              {/* Budget per Role */}
              <div className="buildrosa-form-group">
                <label className="buildrosa-label">Budget per Ruolo (%)</label>
                <div className="buildrosa-budget-grid">
                  {['P', 'D', 'C', 'A'].map(role => (
                    <div key={role} className="buildrosa-budget-item">
                      <label htmlFor={`budget-${role}`} className="buildrosa-role-label" style={{ color: getRoleColor(role) }}>
                        {role}: {budgetPerRole[role]}%
                      </label>
                      <Input
                        id={`budget-${role}`}
                        type="range"
                        min="5"
                        max="50"
                        step="5"
                        value={budgetPerRole[role]}
                        onChange={(e) => setBudgetPerRole({ ...budgetPerRole, [role]: Number(e.target.value) })}
                        className="buildrosa-slider"
                      />
                    </div>
                  ))}
                </div>
                <p className="buildrosa-help-text">
                  Totale: {Object.values(budgetPerRole).reduce((a, b) => a + b, 0)}%
                </p>
              </div>

              {/* Value Priority */}
              <div className="buildrosa-form-group">
                <label htmlFor="priority" className="buildrosa-label">Priorità Ottimizzazione</label>
                <div className="relative overflow-hidden rounded-lg">
                  <div className="absolute inset-x-0 top-0 z-10 h-0.5 bg-gradient-to-r from-sky-400/70 via-violet-400/45 to-transparent" />
                  <select
                    id="priority"
                    value={valuePriority}
                    onChange={(e) => setValuePriority(e.target.value)}
                    className="buildrosa-select"
                  >
                    <option value="FM">FantaMedia (FM)</option>
                    <option value="MV">Media Voto (MV)</option>
                    <option value="PV">Partite Giocate (PV)</option>
                  </select>
                </div>
              </div>

              {/* Actions */}
              <div className="buildrosa-actions">
                <Button type="button" onClick={handleGenerate} className="buildrosa-generate-btn">
                  <Sparkles className="h-4 w-4" />
                  Genera Rosa Ottimale
                </Button>
                <Button type="button" variant="outline" onClick={handleReset}>
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </Button>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="buildrosa-results-section">
            <Alert className="buildrosa-success-alert">
              <Sparkles className="h-4 w-4" />
              <AlertDescription>
                Rosa generata con successo! {result.players.length} giocatori selezionati.
              </AlertDescription>
            </Alert>

            {/* Stats */}
            <div className="buildrosa-stats-grid">
              <KpiCard
                label="Budget Utilizzato"
                value={`${result.budget_used?.toFixed(1)} cr`}
                icon={DollarSign}
              />
              <KpiCard
                label="Budget Rimanente"
                value={`${result.budget_remaining?.toFixed(1)} cr`}
                icon={DollarSign}
                tone={result.budget_remaining > 0 ? 'success' : 'danger'}
              />
              <KpiCard
                label="Media FM"
                value={result.stats?.avg_fm?.toFixed(2) || 'N/A'}
                icon={TrendingUp}
              />
              <KpiCard
                label="Giocatori"
                value={result.players.length}
                icon={Users}
              />
            </div>

            {/* Actions */}
            <div className="buildrosa-result-actions">
              <Button type="button" onClick={handleGenerate}>
                <Sparkles className="h-4 w-4" />
                Rigenera
              </Button>
              <Button type="button" variant="outline" onClick={handleExport}>
                <Download className="h-4 w-4" />
                Esporta JSON
              </Button>
              <Button type="button" variant="outline" onClick={handleReset}>
                <RotateCcw className="h-4 w-4" />
                Nuova Configurazione
              </Button>
            </div>

            {/* Table */}
            <ResponsiveTable caption="Rosa generata">
              <thead>
                <tr className="buildrosa-table-header">
                  <th className="buildrosa-th">Pos</th>
                  <th className="buildrosa-th">Nome</th>
                  <th className="buildrosa-th">Squadra</th>
                  <th className="buildrosa-th buildrosa-th-center">Ruolo</th>
                  <th className="buildrosa-th buildrosa-th-center">Overall</th>
                  <th className="buildrosa-th buildrosa-th-center">FM</th>
                  <th className="buildrosa-th buildrosa-th-right">Prezzo</th>
                </tr>
              </thead>
              <tbody className="fm-table">
                {result.players.map((player) => (
                  <tr
                    key={player.position}
                    className="buildrosa-table-row"
                    onClick={() => navigate(`/players/${player.id}`)}
                  >
                    <td className="buildrosa-td">{player.position}</td>
                    <td className="buildrosa-td buildrosa-td-name">{player.nome}</td>
                    <td className="buildrosa-td">{player.squadra}</td>
                    <td className="buildrosa-td buildrosa-td-center">
                      <Badge variant="outline" style={{ borderColor: getRoleColor(player.ruolo), color: getRoleColor(player.ruolo) }}>
                        {player.ruolo}
                      </Badge>
                    </td>
                    <td className="buildrosa-td buildrosa-td-center">{player.overall || 'N/A'}</td>
                    <td className="buildrosa-td buildrosa-td-center">{player.fm_weighted?.toFixed(2) || '-'}</td>
                    <td className="buildrosa-td buildrosa-td-right">{player.price_credits?.toFixed(1)} cr</td>
                  </tr>
                ))}
              </tbody>
            </ResponsiveTable>
          </div>
        )}
      </main>
    </div>
  );
}

export default BuildRosa;
