"""
Player service - wrappa StatsCalculator e PriceCalculator esistenti
NON modifica le formule, usa direttamente la logica esistente
"""
import pandas as pd
from typing import List, Optional, Dict, Any
from src.data.calculator import StatsCalculator
from src.data.calculators.price_calculator import PriceCalculator
from src.data.player_notes import PlayerNotesManager
from src.data.favorites_manager import FavoritesManager
from src.data.cache import DataCache
from src.config import STATS_FILES, get_season_labels, DEFAULT_AUCTION_BUDGET
from src.data.titolarita_loader import load_titolarita_map, load_status_map
from src.data.fixture_difficulty import calculate_player_fixture_projections


class PlayerService:
    """Service layer per operazioni sui giocatori"""

    def __init__(self):
        """Inizializza service con logica esistente"""
        self.calculator = StatsCalculator()
        self.notes_manager = PlayerNotesManager()
        self.favorites_manager = FavoritesManager()

        # Calcola dati completi all'avvio
        self.df_with_overall = None
        self.price_calculator = None
        self._load_data()

    @staticmethod
    def _clean_numeric_value(value) -> float:
        """Pulisce valori numerici rimuovendo trend arrows (↑↓→) e simboli %"""
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        # Rimuovi frecce trend e simboli percentuale
        str_val = str(value).replace('↑', '').replace('↓', '').replace('→', '').replace('%', '').strip()
        # Gestisci N/A come None
        if str_val.upper() in ('N/A', 'NA', ''):
            return None
        try:
            return float(str_val)
        except:
            return None

    def _load_data(self):
        """Carica e calcola dati completi"""
        try:
            # Calcola statistiche ponderate
            df = self.calculator.calculate_weighted_stats()

            # Calcola Overall
            self.df_with_overall = self.calculator.calculate_overall_scores(df)

            # Inizializza price calculator
            self.price_calculator = PriceCalculator(
                all_players_df=self.df_with_overall,
                use_optimized=True
            )

            if self.df_with_overall is not None and not self.df_with_overall.empty:
                print(f"PlayerService: {len(self.df_with_overall)} giocatori caricati")
            else:
                print("PlayerService: Nessun giocatore caricato")
        except Exception as e:
            print(f"Errore caricamento dati: {e}")
            self.df_with_overall = pd.DataFrame()

    def reload_data(self):
        """Ricarica dati (dopo update listone)"""
        # Pulisci cache
        DataCache.clear_all_caches()

        # Reinizializza calculator per forzare reload CSV
        self.calculator = StatsCalculator()

        # Ricarica dati
        self._load_data()

        if self.df_with_overall is not None and not self.df_with_overall.empty:
            print(f"Dati ricaricati: {len(self.df_with_overall)} giocatori")
        else:
            print("Dati ricaricati: Nessun giocatore")

    def invalidate_price_cache(self):
        """Invalida la cache dei prezzi quando le impostazioni cambiano"""
        if self.price_calculator:
            self.price_calculator.price_cache.clear()
            print("OK Cache prezzi invalidata - i nuovi prezzi saranno ricalcolati")

    def get_all_players(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        team: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        favorite: Optional[bool] = None,
        fm_min: Optional[float] = None,
        fm_max: Optional[float] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        budget: float = DEFAULT_AUCTION_BUDGET,
        sort_by: str = "Overall",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Ottieni lista giocatori con filtri

        Args:
            search: Ricerca per nome
            role: Filtro ruolo (P/D/C/A)
            team: Filtro squadra
            tag: Filtro per tag
            favorite: Solo preferiti
            fm_min: FM minimo
            fm_max: FM massimo
            price_min: Prezzo minimo %
            price_max: Prezzo massimo %
            budget: Budget per calcolo prezzi
            sort_by: Colonna ordinamento
            sort_order: asc/desc

        Returns:
            Lista dizionari con dati giocatori
        """
        if self.df_with_overall is None or self.df_with_overall.empty:
            return []

        # Copia DataFrame
        df = self.df_with_overall.copy()

        # Pulisci colonne numeriche rimuovendo trend arrows per filtri
        df['Fm_numeric'] = df['Fm_weighted'].apply(self._clean_numeric_value)

        # Applica filtri
        if search:
            df = df[df['Nome'].str.contains(search, case=False, na=False)]

        if role:
            df = df[df['R'].str.startswith(role, na=False)]

        if team:
            df = df[df['Squadra'] == team]

        if fm_min is not None:
            df = df[df['Fm_numeric'] >= fm_min]

        if fm_max is not None:
            df = df[df['Fm_numeric'] <= fm_max]

        # Filtro tag
        if tag:
            player_ids_with_tag = [
                pid for pid in df['Id'].tolist()
                if tag in self.notes_manager.get_tags(pid)
            ]
            df = df[df['Id'].isin(player_ids_with_tag)]

        # Filtro preferiti
        if favorite:
            favorites = self.favorites_manager.get_all_favorites()
            df = df[df['Id'].isin(favorites)]

        # Filtro status
        if status:
            status_map = load_status_map()
            player_ids_with_status = [
                pid for pid in df['Id'].tolist()
                if status_map.get(df[df['Id'] == pid].iloc[0]['Nome']) == status
            ]
            df = df[df['Id'].isin(player_ids_with_status)]

        # Calcola prezzi per batch
        player_ids = df['Id'].tolist()
        prices = self.price_calculator.calculate_batch_prices(player_ids, budget)

        # Filtra per prezzo se richiesto
        if price_min is not None or price_max is not None:
            valid_ids = []
            for pid in player_ids:
                price_pct = prices[pid].get('percentage', 0)
                if price_min is not None and price_pct < price_min:
                    continue
                if price_max is not None and price_pct > price_max:
                    continue
                valid_ids.append(pid)
            df = df[df['Id'].isin(valid_ids)]

        # Carica titolarità e status
        titolarita_map = load_titolarita_map()
        status_map = load_status_map()

        # Costruisci risultati
        results = []
        for _, row in df.iterrows():
            player_id = row['Id']
            player_name = row['Nome']
            price_data = prices[player_id]

            # Titolarità
            titolarita = titolarita_map.get(player_name, 0.0)

            # Pulisci titolarita rimuovendo % se presente
            titolarita_clean = self._clean_numeric_value(titolarita) if titolarita else None

            # Status (non sovrascrivere la variabile del filtro!)
            player_status = status_map.get(player_name, None)

            # Pulisci Overall gestendo N/A
            overall_val = self._clean_numeric_value(row.get('Overall'))
            overall_int = int(overall_val) if overall_val is not None else None

            results.append({
                'id': int(player_id),
                'nome': str(row['Nome']),
                'squadra': str(row['Squadra']),
                'ruolo': str(row['R']),
                'ruolo_multiple': str(row.get('RM', '')),
                'overall': overall_int,
                'fm_weighted': self._clean_numeric_value(row.get('Fm_weighted')),
                'mv_weighted': self._clean_numeric_value(row.get('Mv_weighted')),
                'pv_weighted': self._clean_numeric_value(row.get('Pv_weighted')),
                'gf_weighted': self._clean_numeric_value(row.get('Gf_weighted')),
                'ass_weighted': self._clean_numeric_value(row.get('Ass_weighted')),
                'esp_weighted': self._clean_numeric_value(row.get('Esp_weighted')),
                'amm_weighted': self._clean_numeric_value(row.get('Amm_weighted')),
                'rc_weighted': self._clean_numeric_value(row.get('Rc_weighted')),
                'rp_weighted': self._clean_numeric_value(row.get('Rp_weighted')),
                'gs_weighted': self._clean_numeric_value(row.get('Gs_weighted')),
                'price_percentage': float(price_data.get('percentage', 0)),
                'price_credits': float(price_data.get('credits', 0)),
                'titolarita': titolarita_clean,
                'status': player_status,
                'is_favorite': self.favorites_manager.is_favorite(player_id),
                'tags': self.notes_manager.get_tags(player_id),
                'note': self.notes_manager.get_note(player_id)
            })

        # Ordinamento
        if sort_by in ['Overall', 'Fm_weighted', 'Mv_weighted', 'price_percentage', 'titolarita']:
            key_map = {
                'Overall': 'overall',
                'Fm_weighted': 'fm_weighted',
                'Mv_weighted': 'mv_weighted',
                'price_percentage': 'price_percentage',
                'titolarita': 'titolarita'
            }
            sort_key = key_map.get(sort_by, 'overall')
            results.sort(
                key=lambda x: x[sort_key] if x[sort_key] is not None else -999,
                reverse=(sort_order == 'desc')
            )

        return results

    def get_player_by_id(self, player_id: int, budget: float = DEFAULT_AUCTION_BUDGET) -> Optional[Dict[str, Any]]:
        """
        Ottieni dettagli completi giocatore con storico

        Args:
            player_id: ID giocatore
            budget: Budget per calcolo prezzo

        Returns:
            Dizionario con dettagli completi o None
        """
        if self.df_with_overall is None or self.df_with_overall.empty:
            return None

        # Trova giocatore
        player = self.df_with_overall[self.df_with_overall['Id'] == player_id]
        if player.empty:
            return None

        player = player.iloc[0]
        player_name = player['Nome']

        # Calcola prezzo con breakdown
        price_data = self.price_calculator.calculate_price_percentage(player_id, budget)

        # Carica storico da cache
        history = []
        cache = DataCache()
        season_labels = get_season_labels()

        for key, (filename, weight) in STATS_FILES.items():
            df_season = cache.get(filename)
            if df_season is not None and not df_season.empty:
                player_row = df_season[df_season['Id'] == player_id]
                if not player_row.empty:
                    row = player_row.iloc[0]
                    history.append({
                        'season': season_labels[key],
                        'squadra': str(row['Squadra']) if pd.notna(row.get('Squadra')) else 'N/A',
                        'Pv': int(row['Pv']) if pd.notna(row.get('Pv')) else 0,
                        'Mv': float(row['Mv']) if pd.notna(row.get('Mv')) else 0.0,
                        'Fm': float(row['Fm']) if pd.notna(row.get('Fm')) else 0.0,
                        'Gf': int(row['Gf']) if pd.notna(row.get('Gf')) else 0,
                        'Gs': int(row['Gs']) if pd.notna(row.get('Gs')) else 0,
                        'Rp': int(row['Rp']) if pd.notna(row.get('Rp')) else 0,
                        'Rc': int(row['Rc']) if pd.notna(row.get('Rc')) else 0,
                        'Ass': int(row['Ass']) if pd.notna(row.get('Ass')) else 0,
                        'Amm': int(row['Amm']) if pd.notna(row.get('Amm')) else 0,
                        'Esp': int(row['Esp']) if pd.notna(row.get('Esp')) else 0
                    })

        # Rigori calciati ponderati.
        # Preferisce la colonna calcolata da StatsCalculator; se non è presente,
        # ricostruisce il valore usando gli stessi pesi definiti in STATS_FILES.
        rc_weighted = self._clean_numeric_value(player.get('Rc_weighted'))
        if rc_weighted is None:
            weighted_rc = 0.0
            total_weight = 0.0
            try:
                for key, (filename, weight) in STATS_FILES.items():
                    df_weighted = cache.get(filename)
                    if df_weighted is None or df_weighted.empty:
                        continue
                    row_weighted = df_weighted[df_weighted['Id'] == player_id]
                    if row_weighted.empty:
                        continue
                    raw_rc = row_weighted.iloc[0].get('Rc')
                    rc_value = self._clean_numeric_value(raw_rc)
                    if rc_value is None:
                        continue
                    weighted_rc += rc_value * float(weight)
                    total_weight += float(weight)
                if total_weight > 0:
                    rc_weighted = weighted_rc / total_weight
            except Exception as exc:
                print(f"Warning: errore calcolo Rc_weighted per {player_name}: {exc}")

        # Fallback weighted disciplinary stats when the aggregated DataFrame
        # does not expose them. Uses exactly the configured season weights.
        amm_weighted = self._clean_numeric_value(player.get('Amm_weighted'))
        esp_weighted = self._clean_numeric_value(player.get('Esp_weighted'))

        if amm_weighted is None or esp_weighted is None:
            for stat_key, target_name in (('Amm', 'amm'), ('Esp', 'esp')):
                if (stat_key == 'Amm' and amm_weighted is not None) or (stat_key == 'Esp' and esp_weighted is not None):
                    continue
                weighted_value = 0.0
                total_weight = 0.0
                try:
                    for season_key, (filename, weight) in STATS_FILES.items():
                        df_stat = cache.get(filename)
                        if df_stat is None or df_stat.empty:
                            continue
                        row_stat = df_stat[df_stat['Id'] == player_id]
                        if row_stat.empty:
                            continue
                        raw_value = row_stat.iloc[0].get(stat_key)
                        value = self._clean_numeric_value(raw_value)
                        if value is None:
                            continue
                        weighted_value += value * float(weight)
                        total_weight += float(weight)
                    if total_weight > 0:
                        result_value = weighted_value / total_weight
                        if stat_key == 'Amm':
                            amm_weighted = result_value
                        else:
                            esp_weighted = result_value
                except Exception as exc:
                    print(f"Warning: errore calcolo {stat_key}_weighted per {player_name}: {exc}")

        # Titolarità e status
        titolarita_map = load_titolarita_map()
        status_map = load_status_map()
        titolarita = titolarita_map.get(player_name, 0.0)
        titolarita_clean = self._clean_numeric_value(titolarita) if titolarita else None
        status = status_map.get(player_name, None)

        # Calcola proiezioni fixture difficulty per giornata
        fixture_projections = []
        try:
            team = str(player['Squadra'])
            role = str(player['R'])[0] if player['R'] else 'C'

            # Valori base per proiezioni
            base_p_gioca = 0.75  # Default, può essere raffinato con titolarità
            if titolarita_clean:
                base_p_gioca = min(0.95, titolarita_clean / 100.0)

            base_voto_mean = self._clean_numeric_value(player.get('Mv_weighted')) or 6.0
            base_voto_std = 0.8  # Deviazione standard standard
            base_bonus = self._clean_numeric_value(player.get('Gf_weighted', 0)) or 0

            # Calcola proiezioni per 38 giornate
            fixture_projections = calculate_player_fixture_projections(
                team=team,
                role=role,
                base_p_gioca=base_p_gioca,
                base_voto_mean=base_voto_mean,
                base_voto_std=base_voto_std,
                base_bonus=base_bonus
            )
        except Exception as e:
            print(f"Warning: Errore calcolo fixture projections per {player_name}: {e}")
            fixture_projections = []

        # Pulisci Overall gestendo N/A
        overall_val = self._clean_numeric_value(player.get('Overall'))
        overall_int = int(overall_val) if overall_val is not None else None

        return {
            'id': int(player_id),
            'nome': str(player['Nome']),
            'squadra': str(player['Squadra']),
            'ruolo': str(player['R']),
            'ruolo_multiple': str(player.get('RM', '')),
            'overall': overall_int,
            'fm_weighted': self._clean_numeric_value(player.get('Fm_weighted')),
            'mv_weighted': self._clean_numeric_value(player.get('Mv_weighted')),
            'pv_weighted': self._clean_numeric_value(player.get('Pv_weighted')),
            'gf_weighted': self._clean_numeric_value(player.get('Gf_weighted')),
            'ass_weighted': self._clean_numeric_value(player.get('Ass_weighted')),
            'esp_weighted': esp_weighted,
            'amm_weighted': amm_weighted,
            'rc_weighted': rc_weighted,
            'rp_weighted': self._clean_numeric_value(player.get('Rp_weighted')),
            'gs_weighted': self._clean_numeric_value(player.get('Gs_weighted')),
            'price_percentage': float(price_data.get('percentage', 0)),
            'price_credits': float(price_data.get('credits', 0)),
            'titolarita': titolarita_clean,
            'status': status,
            'is_favorite': self.favorites_manager.is_favorite(player_id),
            'tags': self.notes_manager.get_tags(player_id),
            'note': self.notes_manager.get_note(player_id),
            'history': history,
            'price_breakdown': price_data.get('breakdown', {}),
            'fixture_projections': fixture_projections
        }

    def toggle_favorite(self, player_id: int) -> bool:
        """
        Toggle preferito

        Args:
            player_id: ID giocatore

        Returns:
            Nuovo stato (True = preferito)
        """
        return self.favorites_manager.toggle_favorite(player_id)

    def get_favorites(self) -> List[int]:
        """Ottieni lista ID preferiti"""
        return self.favorites_manager.get_all_favorites()

    def get_player_notes(self, player_id: int) -> Dict[str, Any]:
        """
        Ottieni note e tag giocatore

        Args:
            player_id: ID giocatore

        Returns:
            Dict con note e tags
        """
        return {
            'note': self.notes_manager.get_note(player_id),
            'tags': self.notes_manager.get_tags(player_id)
        }

    def update_player_notes(self, player_id: int, note: str, tags: List[str]) -> Dict[str, Any]:
        """
        Aggiorna note e tag giocatore

        Args:
            player_id: ID giocatore
            note: Testo nota
            tags: Lista tag

        Returns:
            Dict con note e tags aggiornati
        """
        self.notes_manager.set_note(player_id, note)
        self.notes_manager.set_tags(player_id, tags)

        return {
            'note': note,
            'tags': tags
        }

    def get_all_teams(self) -> List[str]:
        """Ottieni lista squadre uniche"""
        if self.df_with_overall is None or self.df_with_overall.empty:
            return []

        teams = self.df_with_overall['Squadra'].unique().tolist()
        return sorted([str(t) for t in teams if pd.notna(t)])

    def get_all_tags(self) -> List[str]:
        """Ottieni lista tutti i tag usati (inclusi auto-tags)"""
        all_tags = set()

        # Tag auto-generati sempre disponibili
        auto_tags = [
            'rigorista_1',
            'rigorista_2',
            'rigorista_3',
            'tiratore_1',
            'tiratore_2',
            'tiratore_3',
            'titolare',
            'obiettivo',
            'da_evitare',
            'riserva'
        ]
        all_tags.update(auto_tags)

        # Tag custom dagli utenti
        if self.df_with_overall is not None:
            for player_id in self.df_with_overall['Id'].tolist():
                tags = self.notes_manager.get_tags(player_id)
                all_tags.update(tags)

        return sorted(list(all_tags))

    def get_all_statuses(self) -> List[str]:
        """Ottieni lista tutti gli status disponibili dalla titolarità"""
        status_map = load_status_map()
        all_statuses = set(status_map.values())
        # Rimuovi None/vuoti e ritorna lista ordinata
        return sorted([s for s in all_statuses if s and s != '-'])
