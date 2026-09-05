import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  Check,
  Info,
  RotateCcw,
  Save,
  Settings2,
  Trophy,
  Users,
  WalletCards,
} from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAppContext } from '../context/AppContext';

function Settings() {
  const { reloadAfterSettingsChange } = useAppContext();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/settings');
      const data = await response.json();
      setSettings(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await fetch('/api/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error('Errore nel salvataggio');
      }

      const updated = await response.json();
      setSettings(updated);
      setSuccess(true);
      setSaving(false);

      // Ricarica i dati dell'app con il nuovo budget
      if (reloadAfterSettingsChange) {
        await reloadAfterSettingsChange();
      }

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleBonusChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      bonus: {
        ...prev.bonus,
        [field]: value,
      },
    }));
  };

  const handleCoefficienteChange = (ruolo, value) => {
    setSettings((prev) => ({
      ...prev,
      coefficienti_gol: {
        ...prev.coefficienti_gol,
        [ruolo]: value,
      },
    }));
  };

  const handleRosterChange = (ruolo, value) => {
    setSettings((prev) => ({
      ...prev,
      roster_composition: {
        ...prev.roster_composition,
        [ruolo]: value,
      },
    }));
  };

  const handleScoringChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      scoring: {
        ...prev.scoring,
        [field]: value,
      },
    }));
  };

  if (loading) {
    return <LoadingState message="Caricamento impostazioni..." className="py-16" />;
  }

  if (error && !settings) {
    return (
      <ErrorState
        title="Errore caricamento impostazioni"
        message={error}
        onRetry={loadSettings}
        className="py-16"
      />
    );
  }

  return (
    <div className="min-h-full bg-[#0B0E14]">
      <div className="mx-auto w-full max-w-[1180px] px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <PageHeader
          title="Impostazioni"
          description="Configura i parametri della tua lega"
          actions={
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={saving}
              className="border-sky-400/20 bg-sky-400/[0.04] text-sky-300 hover:border-sky-400/40 hover:bg-sky-400/[0.10] hover:text-sky-200"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Salvataggio...' : 'Salva'}
            </Button>
          }
        />

        <main className="mt-5 space-y-5">
          {success && (
            <Alert className="border-emerald-400/20 bg-emerald-400/[0.055]">
              <Check className="h-4 w-4 text-emerald-300" />
              <AlertDescription className="text-emerald-100/90">
                Impostazioni salvate correttamente.
              </AlertDescription>
            </Alert>
          )}

          {error && settings && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <section className="grid gap-3 sm:grid-cols-2">
            <QuickStat
              icon={WalletCards}
              label="Budget"
              value={settings?.budget ?? '—'}
            />
            <QuickStat
              icon={Users}
              label="Partecipanti"
              value={settings?.participants ?? '—'}
            />
          </section>

          

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={Settings2}
                title="Impostazioni generali"
                description="Parametri base della lega"
              />
            </CardHeader>
            <CardContent className="grid gap-4 p-5 md:grid-cols-2">
              <SettingField
                id="budget"
                label="Budget totale"
                help="Budget disponibile per l'asta (100-5000 crediti)"
                type="number"
                min="100"
                max="5000"
                value={settings.budget}
                onChange={(e) =>
                  handleChange('budget', parseInt(e.target.value, 10))
                }
              />
              <SettingField
                id="participants"
                label="Numero partecipanti"
                help="Numero di partecipanti alla lega (2-20)"
                type="number"
                min="2"
                max="20"
                value={settings.participants}
                onChange={(e) =>
                  handleChange('participants', parseInt(e.target.value, 10))
                }
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={Users}
                title="Composizione Rosa"
                description="Numero di giocatori per ruolo nella rosa"
              />
            </CardHeader>
            <CardContent className="grid gap-4 p-5 sm:grid-cols-4">
              <SettingField
                id="roster-p"
                label="Portieri"
                type="number"
                min="1"
                max="5"
                value={settings.roster_composition?.P || 3}
                onChange={(e) =>
                  handleRosterChange('P', parseInt(e.target.value, 10))
                }
              />
              <SettingField
                id="roster-d"
                label="Difensori"
                type="number"
                min="4"
                max="12"
                value={settings.roster_composition?.D || 8}
                onChange={(e) =>
                  handleRosterChange('D', parseInt(e.target.value, 10))
                }
              />
              <SettingField
                id="roster-c"
                label="Centrocampisti"
                type="number"
                min="4"
                max="12"
                value={settings.roster_composition?.C || 8}
                onChange={(e) =>
                  handleRosterChange('C', parseInt(e.target.value, 10))
                }
              />
              <SettingField
                id="roster-a"
                label="Attaccanti"
                type="number"
                min="3"
                max="10"
                value={settings.roster_composition?.A || 6}
                onChange={(e) =>
                  handleRosterChange('A', parseInt(e.target.value, 10))
                }
              />
            </CardContent>
            <CardContent className="border-t border-slate-800/50 p-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Totale giocatori:</span>
                <span className="font-bold text-sky-300">
                  {(settings.roster_composition?.P || 3) +
                    (settings.roster_composition?.D || 8) +
                    (settings.roster_composition?.C || 8) +
                    (settings.roster_composition?.A || 6)}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={Trophy}
                title="Sistema di Scoring"
                description="Parametri per calcolo punteggi nelle simulazioni"
              />
            </CardHeader>
            <CardContent className="grid gap-4 p-5 md:grid-cols-2">
              <SettingField
                id="goal-threshold"
                label="Soglia Gol (punti base)"
                help="Punti necessari per il primo gol (es. 66)"
                type="number"
                min="50"
                max="100"
                step="1"
                value={settings.scoring?.goal_threshold || 66}
                onChange={(e) =>
                  handleScoringChange('goal_threshold', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="points-per-goal"
                label="Punti per Gol"
                help="Punti necessari per ogni gol successivo (es. 4)"
                type="number"
                min="1"
                max="10"
                step="0.5"
                value={settings.scoring?.points_per_goal || 4}
                onChange={(e) =>
                  handleScoringChange('points_per_goal', parseFloat(e.target.value))
                }
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={Trophy}
                title="Bonus gol"
                description="Valore base assegnato a ogni gol"
              />
            </CardHeader>
            <CardContent className="p-5 md:max-w-sm">
              <SettingField
                id="bonus-gol"
                label="Bonus Gol"
                type="number"
                step="0.5"
                value={settings.bonus.gol}
                onChange={(e) =>
                  handleBonusChange('gol', parseFloat(e.target.value))
                }
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={TrendingIcon}
                title="Bonus e malus"
                description="Valori utilizzati dai calcoli della lega"
              />
            </CardHeader>
            <CardContent className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
              <SettingField
                id="bonus-assist"
                label="Assist"
                type="number"
                step="0.5"
                value={settings.bonus.assist}
                onChange={(e) =>
                  handleBonusChange('assist', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-rigore-parato"
                label="Rigore Parato"
                type="number"
                step="0.5"
                value={settings.bonus.rigore_parato}
                onChange={(e) =>
                  handleBonusChange('rigore_parato', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-rigore-segnato"
                label="Rigore Segnato"
                type="number"
                step="0.5"
                value={settings.bonus.rigore_segnato}
                onChange={(e) =>
                  handleBonusChange('rigore_segnato', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-rigore-sbagliato"
                label="Rigore Sbagliato"
                type="number"
                step="0.5"
                value={settings.bonus.rigore_sbagliato}
                onChange={(e) =>
                  handleBonusChange('rigore_sbagliato', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-autogol"
                label="Autogol"
                type="number"
                step="0.5"
                value={settings.bonus.autogol}
                onChange={(e) =>
                  handleBonusChange('autogol', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-ammonizione"
                label="Ammonizione"
                type="number"
                step="0.5"
                value={settings.bonus.ammonizione}
                onChange={(e) =>
                  handleBonusChange('ammonizione', parseFloat(e.target.value))
                }
              />
              <SettingField
                id="bonus-espulsione"
                label="Espulsione"
                type="number"
                step="0.5"
                value={settings.bonus.espulsione}
                onChange={(e) =>
                  handleBonusChange('espulsione', parseFloat(e.target.value))
                }
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800/90 bg-[#0F172A]">
            <CardHeader className="border-b border-slate-800/70 px-5 py-4">
              <SectionHeading
                icon={ShieldIcon}
                title="Porta inviolata"
                description="Configura i bonus clean sheet"
              />
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              <ToggleSetting
                checked={settings.bonus.clean_sheet_portiere_enabled}
                label="Abilita bonus portiere"
                onChange={(checked) =>
                  handleBonusChange('clean_sheet_portiere_enabled', checked)
                }
              />
              {settings.bonus.clean_sheet_portiere_enabled && (
                <div className="ml-0 rounded-xl border border-slate-800 bg-slate-950/25 p-4 sm:ml-4">
                  <SettingField
                    id="clean-sheet-portiere"
                    label="Bonus Clean Sheet Portiere"
                    type="number"
                    step="0.5"
                    value={settings.bonus.clean_sheet_portiere}
                    onChange={(e) =>
                      handleBonusChange(
                        'clean_sheet_portiere',
                        parseFloat(e.target.value)
                      )
                    }
                  />
                </div>
              )}

              <ToggleSetting
                checked={settings.bonus.clean_sheet_difensore_enabled}
                label="Abilita bonus difensore"
                onChange={(checked) =>
                  handleBonusChange('clean_sheet_difensore_enabled', checked)
                }
              />
              {settings.bonus.clean_sheet_difensore_enabled && (
                <div className="ml-0 rounded-xl border border-slate-800 bg-slate-950/25 p-4 sm:ml-4">
                  <SettingField
                    id="clean-sheet-difensore"
                    label="Bonus Clean Sheet Difensore"
                    type="number"
                    step="0.5"
                    value={settings.bonus.clean_sheet_difensore}
                    onChange={(e) =>
                      handleBonusChange(
                        'clean_sheet_difensore',
                        parseFloat(e.target.value)
                      )
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={loadSettings}
              disabled={saving}
            >
              <RotateCcw className="h-4 w-4" />
              Annulla modifiche
            </Button>
            <Button type="button" onClick={handleSave} disabled={saving}>
              <Save className="h-4 w-4" />
              {saving ? 'Salvataggio...' : 'Salva impostazioni'}
            </Button>
          </div>

          <Alert className="border-slate-800 bg-[#0F172A]">
            <Info className="h-4 w-4 text-slate-400" />
            <AlertDescription>
              <strong>Nota:</strong> questi valori sono informativi e mostrano i
              bonus/malus standard del fantacalcio. Le statistiche dei giocatori
              sono già calcolate con questi bonus nei dati importati.
            </AlertDescription>
          </Alert>
        </main>
      </div>
    </div>
  );
}

function SectionHeading({ icon: Icon, title, description }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/[0.07] text-sky-300">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-slate-100">{title}</h2>
        {description && (
          <p className="mt-0.5 text-xs text-slate-500">{description}</p>
        )}
      </div>
    </div>
  );
}

function QuickStat({ icon: Icon, label, value }) {
  return (
    <Card className="border-slate-800/90 bg-[#0F172A]">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-400/15 bg-sky-400/[0.07] text-sky-300">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
              {label}
            </div>
            <div className="mt-1 text-xl font-bold text-slate-100">{value}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SettingField({ id, label, help, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-xs font-medium text-slate-400">
        {label}
      </label>
      <Input id={id} {...props} />
      {help && <p className="mt-1.5 text-xs text-slate-600">{help}</p>}
    </div>
  );
}

function ToggleSetting({ checked, onChange, label }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-950/20 px-4 py-3.5">
      <span className="text-sm font-medium text-slate-300">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-sky-400"
      />
    </label>
  );
}

function TrendingIcon(props) {
  return <TrendingUpIcon {...props} />;
}

function TrendingUpIcon({ className = 'h-4 w-4' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <polyline points="22 7 13.5 15.5 9 11 2 18" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}

function ShieldIcon({ className = 'h-4 w-4' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
    </svg>
  );
}

export default Settings;
