import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  Filter,
  Search,
  Shield,
  Star,
  Users,
  Image,
} from 'lucide-react';
import { formatTitolarita } from '../utils/formatters';
import { useAppContext } from '../context/AppContext';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import ResponsiveTable from '../components/common/ResponsiveTable';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { PlayerAvatar, TeamLogo } from '../components/common/PlayerMedia';

const ROLE_VARIANTS = {
  P: 'warning',
  D: 'success',
  C: 'default',
  A: 'destructive',
};

const HIDDEN_FILTER_TAGS = new Set([
  'rigorista_1',
  'rigorista_2',
  'rigorista_3',
  'tiratore_1',
  'tiratore_2',
  'tiratore_3',
]);

// Ruoli speciali con colori custom
const SPECIAL_ROLE_COLORS = {
  'C (E)': 'bg-sky-500/10 text-sky-300 border-sky-400/20',
  'C (T)': 'bg-sky-500/10 text-sky-300 border-sky-400/20',
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

function SortableHeader({ label, column, currentSort, currentOrder, onSort, align = 'left' }) {
  const isActive = currentSort === column;

  return (
    <th
      scope="col"
      onClick={() => onSort(column)}
      className={`cursor-pointer select-none whitespace-nowrap border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 transition-colors hover:bg-slate-900 hover:text-slate-300 ${
        isActive ? 'text-sky-400' : ''
      }`}
      style={{ textAlign: align }}
    >
      <span className="inline-flex items-center gap-1.5">
        {label}
        {isActive && (
          currentOrder === 'asc' ? (
            <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
          )
        )}
      </span>
    </th>
  );
}

function FilterField({ label, children }) {
  return (
    <div className="min-w-0">
      <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </div>
      {children}
    </div>
  );
}

function Favorites() {
  const navigate = useNavigate();
  const {
    players: allPlayers,
    loading: globalLoading,
    toggleFavorite,
  } = useAppContext();

  const [localPlayers, setLocalPlayers] = useState([]);
  const [error, setError] = useState(null);
  const [sortColumn, setSortColumn] = useState('overall');
  const [sortOrder, setSortOrder] = useState('desc');
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({
    role: '', team: '', tag: '', status: '', fm_min: '', fm_max: '', price_min: '', price_max: '', budget: 500,
  });

  const favoritePlayers = React.useMemo(
    () => allPlayers.filter((player) => player.is_favorite),
    [allPlayers],
  );
  const teams = React.useMemo(() => [...new Set(favoritePlayers.map((p) => p.squadra).filter(Boolean))].sort(), [favoritePlayers]);
  const tags = React.useMemo(() => [...new Set(favoritePlayers.flatMap((p) => p.tags || []))].sort(), [favoritePlayers]);
  const statuses = React.useMemo(() => [...new Set(favoritePlayers.map((p) => p.status).filter(Boolean))].sort(), [favoritePlayers]);

  useEffect(() => {
    applyFilters();
  }, [favoritePlayers, filters, globalLoading]);

  const applyFilters = () => {
    let filtered = [...favoritePlayers];
    if (filters.role) filtered = filtered.filter((p) => p.ruolo && p.ruolo.startsWith(filters.role));
    if (filters.team) filtered = filtered.filter((p) => p.squadra === filters.team);
    if (filters.tag) filtered = filtered.filter((p) => p.tags && p.tags.includes(filters.tag));
    if (filters.status) filtered = filtered.filter((p) => p.status === filters.status);
    if (filters.fm_min) filtered = filtered.filter((p) => p.fm_weighted >= parseFloat(filters.fm_min));
    if (filters.fm_max) filtered = filtered.filter((p) => p.fm_weighted <= parseFloat(filters.fm_max));
    if (filters.price_min) filtered = filtered.filter((p) => p.price_percentage >= parseFloat(filters.price_min));
    if (filters.price_max) filtered = filtered.filter((p) => p.price_percentage <= parseFloat(filters.price_max));
    setLocalPlayers(filtered);
  };

  const handleToggleFavorite = async (playerId, e) => {
    e.stopPropagation();
    try {
      await toggleFavorite(playerId);
      setLocalPlayers((prev) => prev.filter((player) => player.id !== playerId));
    } catch (err) {
      setError('Errore nel toggle del preferito');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setSearchText('');
    setFilters({
      role: '',
      team: '',
      tag: '',
      status: '',
      fm_min: '',
      fm_max: '',
      price_min: '',
      price_max: '',
      budget: 500,
    });
    setSortColumn('overall');
    setSortOrder('desc');
  };

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortOrder('desc');
    }
  };

  const getSortedPlayers = () => {
    let filtered = localPlayers;

    if (searchText.trim()) {
      const search = searchText.toLowerCase().trim();
      filtered = localPlayers.filter(
        (player) => player.nome && player.nome.toLowerCase().includes(search),
      );
    }

    return [...filtered].sort((a, b) => {
      let aVal = a[sortColumn];
      let bVal = b[sortColumn];

      if (aVal == null) aVal = sortOrder === 'asc' ? Infinity : -Infinity;
      if (bVal == null) bVal = sortOrder === 'asc' ? Infinity : -Infinity;

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc'
          ? aVal.localeCompare(bVal, 'it')
          : bVal.localeCompare(aVal, 'it');
      }

      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });
  };

  const displayedPlayers = getSortedPlayers();

  if (globalLoading) {
    return <LoadingState message="Caricamento giocatori..." className="players-state" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Errore caricamento giocatori"
        message={error}
        onRetry={() => setError(null)}
        className="players-state"
      />
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#0B0E14] text-slate-100">
      <div className="mx-auto max-w-[1800px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
        <header className="mb-6 flex flex-col gap-4 border-b border-slate-800/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">
              <span>FMManager</span>
              <span className="text-slate-700">/</span>
              <span>Analisi</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-slate-50 sm:text-3xl">Preferiti</h1>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/20 bg-sky-400/10 px-2.5 py-1 text-xs font-medium text-sky-300">
                <Star className="h-3.5 w-3.5 fill-current" aria-hidden="true" />
                {displayedPlayers.length}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              I tuoi giocatori preferiti, con la stessa analisi della lista giocatori.
            </p>
          </div>

          <div className="flex gap-2">
            
            

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={resetFilters}
              className="border-slate-700 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              <Filter className="mr-2 h-4 w-4" aria-hidden="true" />
              Reset filtri
            </Button>
          </div>
        </header>

        <section className="mb-5 overflow-hidden rounded-2xl border border-slate-800/80 bg-[#0F172A]/85 shadow-[0_10px_40px_rgba(0,0,0,0.18)]">
          <div className="flex flex-col gap-3 border-b border-slate-800/70 px-4 py-4 sm:px-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-100">Filtri giocatori</div>
              <div className="mt-0.5 text-xs text-slate-500">Riduci rapidamente il database ai profili che ti interessano.</div>
            </div>
            <div className="text-xs text-slate-500">
              {displayedPlayers.length} risultati
            </div>
          </div>

          <div className="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4 sm:p-5">
            <FilterField label="Ricerca">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" aria-hidden="true" />
                <Input
                  id="players-search"
                  type="text"
                  placeholder="Nome giocatore..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="h-10 border-slate-700 bg-[#0B0E14] pl-9 text-sm text-slate-100 placeholder:text-slate-600 focus-visible:ring-sky-400"
                />
              </div>
            </FilterField>

            <FilterField label="Ruolo">
              <Select
                id="players-role"
                value={filters.role}
                onChange={(e) => handleFilterChange('role', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              >
                <option value="">Tutti</option>
                <option value="P">Portiere</option>
                <option value="D">Difensore</option>
                <option value="C">Centrocampista</option>
                <option value="A">Attaccante</option>
              </Select>
            </FilterField>

            <FilterField label="Squadra">
              <Select
                id="players-team"
                value={filters.team}
                onChange={(e) => handleFilterChange('team', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              >
                <option value="">Tutte</option>
                {teams.map((team) => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </Select>
            </FilterField>

            <FilterField label="Tag">
              <Select
                id="players-tag"
                value={filters.tag}
                onChange={(e) => handleFilterChange('tag', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              >
                <option value="">Tutti</option>
                {tags.filter((tag) => !HIDDEN_FILTER_TAGS.has(tag)).map((tag) => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </Select>
            </FilterField>

            <FilterField label="Status">
              <Select
                id="players-status"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              >
                <option value="">Tutti</option>
                {statuses.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </Select>
            </FilterField>

            <FilterField label="FM min">
              <Input
                id="players-fm-min"
                type="number"
                step="0.1"
                placeholder="6.0"
                value={filters.fm_min}
                onChange={(e) => handleFilterChange('fm_min', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              />
            </FilterField>

            <FilterField label="FM max">
              <Input
                id="players-fm-max"
                type="number"
                step="0.1"
                placeholder="8.0"
                value={filters.fm_max}
                onChange={(e) => handleFilterChange('fm_max', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              />
            </FilterField>

            <FilterField label="Prezzo min %">
              <Input
                id="players-price-min"
                type="number"
                step="0.1"
                placeholder="2.0"
                value={filters.price_min}
                onChange={(e) => handleFilterChange('price_min', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              />
            </FilterField>

            <FilterField label="Prezzo max %">
              <Input
                id="players-price-max"
                type="number"
                step="0.1"
                placeholder="10.0"
                value={filters.price_max}
                onChange={(e) => handleFilterChange('price_max', e.target.value)}
                className="h-10 border-slate-700 bg-[#0B0E14] text-sm"
              />
            </FilterField>

          </div>
        </section>

        {displayedPlayers.length === 0 ? (
          <div className="rounded-2xl border border-slate-800/80 bg-[#0F172A]/70 p-6 sm:p-10">
            <EmptyState
              icon={Search}
              title="Nessun giocatore trovato nei preferiti"
              description="Prova a modificare i filtri o la ricerca oppure aggiungi nuovi giocatori ai preferiti."
              action={{ label: 'Reset filtri', onClick: resetFilters, variant: 'outline' }}
            />
          </div>
        ) : (
          <ResponsiveTable
            caption="Elenco giocatori preferiti filtrati e ordinati"
            mobileContent={
              <div className="space-y-3 p-3">
                {displayedPlayers.map((player) => (
                  <div
                    key={player.id}
                    onClick={() => navigate(`/players/${player.id}`)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') navigate(`/players/${player.id}`);
                    }}
                    role="button"
                    tabIndex={0}
                    className="block w-full cursor-pointer rounded-2xl border border-slate-800 bg-[#0F172A]/85 p-4 text-left transition-all hover:border-sky-400/20 hover:bg-slate-900/80 focus:outline-none focus:ring-2 focus:ring-sky-400/30 active:scale-[0.995]"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <PlayerAvatar playerId={player.id} size="medium" />
                        <div className="min-w-0">
                          <div className="truncate text-[15px] font-semibold text-slate-100">{player.nome}</div>
                          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                            <TeamLogo teamName={player.squadra} size={20} />
                            <span>{player.squadra}</span>
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => handleToggleFavorite(player.id, e)}
                        className="shrink-0 rounded-lg border-0 bg-transparent p-2 text-amber-400 transition hover:bg-transparent hover:text-amber-300 focus-visible:bg-transparent"
                        aria-label={player.is_favorite ? 'Rimuovi da preferiti' : 'Aggiungi a preferiti'}
                      >
                        <Star
                          className={`h-5 w-5 ${
                            player.is_favorite
                              ? 'fill-amber-400 text-amber-400'
                              : 'fill-transparent text-amber-400'
                          }`}
                          aria-hidden="true"
                        />
                      </button>
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
                        <RoleBadge role={player.ruolo?.split('/')?.[0]} />
                      </div>
                    </div>

                    <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                      <span>MV {player.mv_weighted?.toFixed(2) || '-'}</span>
                      <span>PV {player.pv_weighted?.toFixed(1) || '-'}</span>
                      <span>Gol {player.gf_weighted?.toFixed(1) || '-'}</span>
                      <ChevronRight className="h-4 w-4 text-slate-600" aria-hidden="true" />
                    </div>
                  </div>
                ))}
              </div>
            }
          >
            <thead>
                  <tr>
                    <th className="w-12 border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-center">
                      <Star className="mx-auto h-4 w-4 text-slate-600" aria-hidden="true" />
                    </th>
                    <SortableHeader label="Overall" column="overall" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} />
                    <SortableHeader label="Nome" column="nome" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} />
                    <SortableHeader label="Squadra" column="squadra" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} />
                    <SortableHeader label="Ruolo" column="ruolo" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} />
                    <th className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Tag</th>
                    <SortableHeader label="FM" column="fm_weighted" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="MV" column="mv_weighted" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="PV" column="pv_weighted" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="Gol" column="gf_weighted" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="Assist" column="ass_weighted" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="Tit%" column="titolarita" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="Prezzo %" column="price_percentage" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                    <SortableHeader label="Crediti" column="price_credits" currentSort={sortColumn} currentOrder={sortOrder} onSort={handleSort} align="right" />
                  </tr>
                </thead>
                <tbody>
                  {displayedPlayers.map((player) => (
                    <tr
                      key={player.id}
                      onClick={() => navigate(`/players/${player.id}`)}
                      className="cursor-pointer border-b border-slate-800/60 transition-colors hover:bg-slate-900/70"
                    >
                      <td className="px-3 py-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={(e) => handleToggleFavorite(player.id, e)}
                          className="rounded-lg border-0 bg-transparent p-2 text-amber-400 transition hover:bg-transparent hover:text-amber-300 focus-visible:bg-transparent"
                          aria-label={player.is_favorite ? 'Rimuovi da preferiti' : 'Aggiungi a preferiti'}
                        >
                          <Star
                            className={`h-4 w-4 ${
                              player.is_favorite
                                ? 'fill-amber-400 text-amber-400'
                                : 'fill-transparent text-amber-400'
                            }`}
                            aria-hidden="true"
                          />
                        </button>
                      </td>
                      <td className="px-3 py-3.5 text-base font-bold text-sky-400">{player.overall || 'N/A'}</td>
                      <td className="px-3 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="shrink-0">
                            <PlayerAvatar playerId={player.id} size="small" />
                          </div>
                          <div className="min-w-0">
                            <div className="truncate font-semibold text-slate-100">{player.nome}</div>
                          </div>
                          {(player.ruolo === 'P' || player.ruolo === 'D') && player.mv_weighted >= 6.0 && (
                            <Shield className="h-4 w-4 shrink-0 text-sky-400" aria-hidden="true" title="Defense Modifier attivo" />
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3.5">
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                          <TeamLogo teamName={player.squadra} size={24} />
                          <span>{player.squadra}</span>
                        </div>
                      </td>
                      <td className="px-3 py-3.5">
                        {player.ruolo && player.ruolo.includes('/') ? (
                          <div className="flex items-center gap-1.5">
                            {player.ruolo.split('/').map((role, idx) => (
                              <RoleBadge key={idx} role={role} />
                            ))}
                          </div>
                        ) : (
                          <RoleBadge role={player.ruolo} />
                        )}
                      </td>
                      <td className="px-3 py-3.5">
                        {player.tags && player.tags.length > 0 ? (
                          <div className="flex max-w-40 flex-wrap gap-1.5">
                            {player.tags.map((tag, idx) => (
                              <Badge key={idx} variant={tag === 'rigorista' ? 'default' : 'secondary'} className="text-[10px]">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-700">-</span>
                        )}
                      </td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-slate-100">{player.fm_weighted?.toFixed(2) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.mv_weighted?.toFixed(2) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-400">{player.pv_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.gf_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{player.ass_weighted?.toFixed(1) || '-'}</td>
                      <td className="px-3 py-3.5 text-right text-sm text-slate-300">{formatTitolarita(player.titolarita)}</td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_percentage?.toFixed(1) || '-'}%</td>
                      <td className="px-3 py-3.5 text-right text-sm font-semibold text-amber-400">{player.price_credits?.toFixed(0) || '-'}</td>
                    </tr>
                  ))}
                </tbody>
          </ResponsiveTable>
        )}
      </div>
    </div>
  );
}

export default Favorites;
