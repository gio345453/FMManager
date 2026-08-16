"""
Algoritmo zaino multidimensionale per ottimizzazione rosa
"""
import pandas as pd
from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path
from datetime import datetime

try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


class KnapsackOptimizer:
    """Ottimizzatore rosa con algoritmo zaino multidimensionale"""

    def __init__(self, df: pd.DataFrame, price_calculator, budget: float):
        """
        Inizializza ottimizzatore

        Args:
            df: DataFrame giocatori
            price_calculator: Calcolatore prezzi
            budget: Budget totale
        """
        self.df = df
        self.price_calculator = price_calculator
        self.budget = budget
        self.griglia_portieri = self._load_griglia_portieri()

        # Cache prezzi e tracking prezzi invalidi
        self._price_cache = {}
        self._invalid_price_ids = set()

    def _to_float(self, value, default=0.0):
        """Converte valore in float gestendo formato italiano con virgola"""
        try:
            return float(str(value).strip().replace(',', '.'))
        except (TypeError, ValueError):
            return default

    def _get_price_credits(self, player_id: str) -> float:
        """
        Calcola prezzo giocatore in crediti assoluti con cache

        Args:
            player_id: ID giocatore

        Returns:
            Prezzo in crediti (minimo 1.0)
        """
        # Usa cache se disponibile
        if player_id in self._price_cache:
            return self._price_cache[player_id]

        data = self.price_calculator.calculate_price_percentage(
            player_id, self.budget
        )

        # Prova prima 'absolute'
        price = self._to_float(data.get('absolute'), 0.0)

        # Se non presente o zero, calcola da 'percentage'
        if price <= 0:
            percentage = self._to_float(data.get('percentage'), 0.0)
            price = (percentage / 100.0) * self.budget

        # Segnala prezzi invalidi (una sola volta)
        if price <= 0:
            price = 1.0
            self._invalid_price_ids.add(player_id)

        # Salva in cache
        self._price_cache[player_id] = price
        return price

    def _load_griglia_portieri(self) -> Dict:
        """Carica griglia portieri (scarica se necessario)"""
        griglia_path = Path('data/GrigliaPortieri/griglia_portieri.json')

        if griglia_path.exists():
            # Controlla se è aggiornata (scaricata dopo 15 luglio anno corrente)
            mod_time = datetime.fromtimestamp(griglia_path.stat().st_mtime)
            current_year = datetime.now().year
            cutoff_date = datetime(current_year, 7, 15)

            if mod_time >= cutoff_date:
                # Griglia valida
                with open(griglia_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Troppo vecchia, controlla se siamo oltre il 15 luglio
                if datetime.now() >= cutoff_date:
                    # Scarica nuova griglia
                    return self._download_griglia_portieri()
                else:
                    # Usa quella esistente
                    with open(griglia_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
        else:
            # Non esiste, scarica
            return self._download_griglia_portieri()

    def _download_griglia_portieri(self) -> Dict:
        """Scarica griglia portieri usando lo script esistente"""
        try:
            import subprocess
            import sys

            # Esegui script griglia portieri
            script_path = Path('data/GrigliaPortieri/griglia_portieri_scraper.py')
            if script_path.exists():
                subprocess.run([sys.executable, str(script_path)], check=True)

            # Ricarica JSON
            griglia_path = Path('data/GrigliaPortieri/griglia_portieri.json')
            if griglia_path.exists():
                with open(griglia_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Errore scaricamento griglia: {e}")

        return {}

    def get_role_slots_structure(self, role: str, total_slots: int) -> List[Dict]:
        """
        Definisce la struttura a fasce per ogni ruolo

        Args:
            role: Ruolo (P/D/C/A)
            total_slots: Numero totale di slot per il ruolo

        Returns:
            Lista di dict con {tier, budget_pct, weight}
        """
        if role == 'P':
            # Portieri: top + riserva + terzo
            if total_slots >= 3:
                return [
                    {'tier': 'top', 'budget_pct': 60, 'weight': 1.0},
                    {'tier': 'riserva', 'budget_pct': 35, 'weight': 0.4},
                    {'tier': 'terzo', 'budget_pct': 5, 'weight': 0.05}
                ]
            elif total_slots == 2:
                return [
                    {'tier': 'top', 'budget_pct': 65, 'weight': 1.0},
                    {'tier': 'riserva', 'budget_pct': 35, 'weight': 0.4}
                ]
            else:
                return [{'tier': 'top', 'budget_pct': 100, 'weight': 1.0}]

        elif role == 'D':
            # Difensori: distribuzione su 8 slot
            if total_slots >= 8:
                return [
                    {'tier': 'top', 'budget_pct': 25, 'weight': 1.0},
                    {'tier': 'semitop', 'budget_pct': 20, 'weight': 1.0},
                    {'tier': 'medio1', 'budget_pct': 15, 'weight': 1.0},
                    {'tier': 'medio2', 'budget_pct': 15, 'weight': 0.5},
                    {'tier': 'medio3', 'budget_pct': 10, 'weight': 0.4},
                    {'tier': 'economico1', 'budget_pct': 8, 'weight': 0.3},
                    {'tier': 'economico2', 'budget_pct': 5, 'weight': 0.1},
                    {'tier': 'copertura', 'budget_pct': 2, 'weight': 0.05}
                ]
            else:
                # Per meno slot, distribuisci uniformemente
                return self._uniform_distribution(total_slots)

        elif role == 'C':
            # Centrocampisti: distribuzione su 8 slot
            if total_slots >= 8:
                return [
                    {'tier': 'top', 'budget_pct': 30, 'weight': 1.0},
                    {'tier': 'semitop', 'budget_pct': 25, 'weight': 1.0},
                    {'tier': 'medio1', 'budget_pct': 15, 'weight': 1.0},
                    {'tier': 'medio2', 'budget_pct': 12, 'weight': 0.5},
                    {'tier': 'medio3', 'budget_pct': 8, 'weight': 0.4},
                    {'tier': 'economico1', 'budget_pct': 6, 'weight': 0.3},
                    {'tier': 'economico2', 'budget_pct': 3, 'weight': 0.1},
                    {'tier': 'copertura', 'budget_pct': 1, 'weight': 0.05}
                ]
            else:
                return self._uniform_distribution(total_slots)

        elif role == 'A':
            # Attaccanti: distribuzione su 6 slot
            if total_slots >= 6:
                return [
                    {'tier': 'top', 'budget_pct': 35, 'weight': 1.0},
                    {'tier': 'semitop', 'budget_pct': 25, 'weight': 1.0},
                    {'tier': 'medio1', 'budget_pct': 15, 'weight': 1.0},
                    {'tier': 'medio2', 'budget_pct': 13, 'weight': 0.4},
                    {'tier': 'economico', 'budget_pct': 10, 'weight': 0.2},
                    {'tier': 'copertura', 'budget_pct': 2, 'weight': 0.05}
                ]
            else:
                return self._uniform_distribution(total_slots)

        return []

    def _uniform_distribution(self, total_slots: int) -> List[Dict]:
        """Distribuzione uniforme per configurazioni non standard"""
        budget_per_slot = 100 / total_slots
        return [
            {'tier': f'slot{i+1}', 'budget_pct': budget_per_slot, 'weight': 1.0 if i < total_slots // 2 else 0.3}
            for i in range(total_slots)
        ]

    def classify_slots(self, empty_positions: List[int], position_roles: Dict[int, str],
                       budget_per_role: Dict[str, float], selected_players: Dict,
                       custom_credits: Dict[int, float]) -> Dict[str, List[Dict]]:
        """
        Classifica slot vuoti usando sistema a fasce con budget progressivo

        Args:
            empty_positions: Indici posizioni vuote
            position_roles: Mappa posizione -> ruolo
            budget_per_role: Budget % allocato per ruolo
            selected_players: Giocatori già selezionati dall'utente
            custom_credits: Prezzi custom per posizione

        Returns:
            Dict con lista di slot per ogni ruolo: {role: [{'pos': idx, 'tier': name, 'budget': credits, 'weight': w}]}
        """
        classification = {
            'P': [],
            'D': [],
            'C': [],
            'A': []
        }

        # Calcola budget già usato per ogni ruolo
        used_budget_by_role = {'P': 0.0, 'D': 0.0, 'C': 0.0, 'A': 0.0}

        for pos, player_data in selected_players.items():
            role = position_roles.get(pos)
            if not role:
                continue

            # Calcola prezzo del giocatore selezionato
            if pos in custom_credits:
                price = max(self._to_float(custom_credits[pos], 1), 1)
            else:
                player_id = player_data.get('id', '')
                if player_id:
                    price = self._get_price_credits(player_id)
                else:
                    price = 1

            used_budget_by_role[role] += price

        # Conta slot vuoti per ruolo
        role_counts = {'P': 0, 'D': 0, 'C': 0, 'A': 0}
        for pos_idx in empty_positions:
            role = position_roles[pos_idx]
            role_counts[role] += 1

        # Per ogni ruolo, assegna fasce agli slot vuoti
        for role in ['P', 'D', 'C', 'A']:
            if role_counts[role] == 0:
                continue

            # Budget totale per ruolo in crediti assoluti
            total_role_budget = (self._to_float(budget_per_role.get(role, 0), 0) / 100.0) * self.budget

            # Usa l'allocazione totale per distribuire le fasce
            # Il solver CP-SAT applicherà il vincolo sul residuo effettivo
            available_budget = total_role_budget

            # Ottieni struttura fasce per questo ruolo
            tiers = self.get_role_slots_structure(role, role_counts[role])

            # Normalizza budget percentuali (devono sommare a 100)
            total_tier_pct = sum(t['budget_pct'] for t in tiers)
            if total_tier_pct > 0:
                for tier in tiers:
                    tier['budget_pct'] = (tier['budget_pct'] / total_tier_pct) * 100

            # Assegna slot vuoti alle fasce
            role_positions = [pos for pos in empty_positions if position_roles[pos] == role]

            for i, pos_idx in enumerate(role_positions):
                if i < len(tiers):
                    tier_info = tiers[i]
                    # Calcola budget assoluto per questa fascia (crediti, non percentuale)
                    tier_budget_credits = (tier_info['budget_pct'] / 100.0) * available_budget

                    # Assicura minimo 1 credito
                    tier_budget_credits = max(tier_budget_credits, 1.0)

                    classification[role].append({
                        'pos': pos_idx,
                        'tier': tier_info['tier'],
                        'budget': tier_budget_credits,  # crediti assoluti
                        'weight': tier_info['weight']
                    })
                else:
                    # Slot extra: budget minimo
                    classification[role].append({
                        'pos': pos_idx,
                        'tier': 'extra',
                        'budget': 1.0,
                        'weight': 0.05
                    })

        return classification

    def get_goalkeeper_pairs(self, available_goalkeepers: pd.DataFrame) -> List[Dict]:
        """
        Trova coppie ottimali di portieri (stesso team o griglia efficiente)

        Args:
            available_goalkeepers: DataFrame portieri disponibili

        Returns:
            Lista di coppie {titolare, riserva, score}
        """
        pairs = []

        # Coppie stesso team (priorità massima)
        teams = available_goalkeepers['Squadra'].unique()
        for team in teams:
            team_gk = available_goalkeepers[available_goalkeepers['Squadra'] == team]
            if len(team_gk) >= 2:
                # Ordina per FM
                team_gk_sorted = team_gk.sort_values('Fm_weighted', ascending=False)
                for i in range(len(team_gk_sorted) - 1):
                    titolare = team_gk_sorted.iloc[i]
                    riserva = team_gk_sorted.iloc[i + 1]

                    pairs.append({
                        'titolare': titolare,
                        'riserva': riserva,
                        'type': 'same_team',
                        'score': 100  # Score massimo per stesso team
                    })

        # Coppie griglia incrociata
        if self.griglia_portieri:
            for i, gk1 in available_goalkeepers.iterrows():
                for j, gk2 in available_goalkeepers.iterrows():
                    if i >= j:
                        continue

                    team1 = gk1['Squadra']
                    team2 = gk2['Squadra']

                    if team1 == team2:
                        continue  # Già gestito sopra

                    # Calcola score griglia
                    grid_score = self._calculate_grid_score(team1, team2)

                    if grid_score is not None:
                        # Determina titolare/riserva per FM
                        if gk1['Fm_weighted'] >= gk2['Fm_weighted']:
                            titolare, riserva = gk1, gk2
                        else:
                            titolare, riserva = gk2, gk1

                        pairs.append({
                            'titolare': titolare,
                            'riserva': riserva,
                            'type': 'grid',
                            'score': 50 - grid_score  # 0 è migliore, quindi inverti
                        })

        # Ordina per score (migliori prima)
        pairs.sort(key=lambda x: x['score'], reverse=True)
        return pairs

    def _calculate_grid_score(self, team1: str, team2: str) -> Optional[int]:
        """
        Calcola score griglia tra due squadre (0 = migliore)

        Args:
            team1: Nome squadra 1
            team2: Nome squadra 2

        Returns:
            Score griglia (0-19) o None
        """
        if not self.griglia_portieri:
            return None

        # Cerca nella griglia
        for entry in self.griglia_portieri.get('combinations', []):
            teams = entry.get('teams', [])
            if set(teams) == {team1, team2}:
                return entry.get('home_matches', 19)  # Default alto se manca

        return None

    def find_backup_for_player(self, player_id: str, role: str) -> Optional[pd.Series]:
        """
        Trova riserva/coppia per giocatore con bassa titolarità o infortunato

        Args:
            player_id: ID giocatore
            role: Ruolo

        Returns:
            Giocatore riserva o None
        """
        player = self.df[self.df['Id'] == player_id]
        if player.empty:
            return None

        player = player.iloc[0]
        team = player['Squadra']

        # Cerca giocatori stesso team, stesso ruolo, low-cost
        teammates = self.df[
            (self.df['Squadra'] == team) &
            (self.df['R'].str.startswith(role, na=False)) &
            (self.df['Id'] != player_id)
        ].copy()

        if teammates.empty:
            return None

        # Calcola prezzi
        teammates['price_pct'] = teammates['Id'].apply(
            lambda pid: self.price_calculator.calculate_price_percentage(pid, self.budget).get('percentage', 100)
        )

        # Filtra low-cost (< 1% budget = 1 credito)
        low_cost = teammates[teammates['price_pct'] <= 1.0]

        if low_cost.empty:
            return None

        # Ritorna il migliore per FM
        low_cost_sorted = low_cost.sort_values('Fm_weighted', ascending=False)
        return low_cost_sorted.iloc[0]

    def optimize_positions(self, empty_positions: List[int], position_roles: List[str],
                          budget_per_role: Dict[str, float], selected_players: Dict,
                          value_priority: str = 'FM', blacklisted_teams: set = None,
                          custom_credits: Dict[int, float] = None) -> Dict[int, Dict]:
        """
        Ottimizza riempimento posizioni con algoritmo zaino multidimensionale

        Args:
            empty_positions: Posizioni da riempire
            position_roles: Mappa posizione -> ruolo
            budget_per_role: Budget % per ruolo
            selected_players: Giocatori già selezionati
            value_priority: Priorità valutazione (FM/MV/PV)
            blacklisted_teams: Set di squadre da escludere
            custom_credits: Dict {posizione: crediti} con prezzi custom utente

        Returns:
            Dict {posizione: player_data}
        """
        if blacklisted_teams is None:
            blacklisted_teams = set()
        if custom_credits is None:
            custom_credits = {}

        # Converti position_roles da lista a dizionario se necessario
        if isinstance(position_roles, list):
            position_roles_dict = {i: role for i, role in enumerate(position_roles)}
        else:
            position_roles_dict = position_roles

        # Classifica slot basandosi sui giocatori già selezionati
        classification = self.classify_slots(
            empty_positions,
            position_roles_dict,
            budget_per_role,
            selected_players,
            custom_credits
        )

        # Pesi valore
        value_weights = {
            'FM': 0.9 if value_priority == 'FM' else 0.05,
            'MV': 0.9 if value_priority == 'MV' else 0.05,
            'PV': 0.9 if value_priority == 'PV' else 0.05
        }

        # Se OR-Tools disponibile, usa modello unificato multidimensionale
        if HAS_ORTOOLS:
            return self._optimize_unified_cpsat(
                classification,
                selected_players,
                value_weights,
                blacklisted_teams,
                position_roles_dict,
                custom_credits,
                budget_per_role
            )
        else:
            result = {}
            for role in ['P', 'D', 'C', 'A']:
                if classification[role]:
                    role_result = self._optimize_role_greedy(
                        role,
                        classification[role],
                        selected_players,
                        value_weights,
                        blacklisted_teams,
                        position_roles_dict,
                        custom_credits
                    )
                    result.update(role_result)
            return result

    def _optimize_unified_cpsat(self, classification, selected_players, value_weights,
                                blacklisted_teams, position_roles, custom_credits, budget_per_role):
        """
        Modello CP-SAT unificato per tutti i ruoli con vincoli multidimensionali

        Vincoli:
        - Budget totale rosa (inclusi giocatori già selezionati)
        - Budget per ruolo (P, D, C, A) (inclusi giocatori già selezionati)
        - Budget per fascia (vincolo rigido)
        - Ogni slot ha esattamente 1 giocatore
        - Ogni giocatore in max 1 slot

        Args:
            classification: Dict {role: [{pos, tier, budget, weight}]}
            selected_players: Giocatori già selezionati
            value_weights: Pesi FM/MV/PV
            blacklisted_teams: Squadre escluse
            position_roles: Mapping ruoli
            custom_credits: Crediti custom per posizione
            budget_per_role: Budget % per ruolo

        Returns:
            Dict {posizione: player_data}
        """
        SCALE = 100  # Scala per mantenere precisione decimale

        model = cp_model.CpModel()

        # Calcola costo giocatori già selezionati (totale e per ruolo)
        selected_cost_total = 0.0
        selected_cost_by_role = {'P': 0.0, 'D': 0.0, 'C': 0.0, 'A': 0.0}

        for pos, player_data in selected_players.items():
            role = position_roles.get(pos)
            if not role:
                continue

            # Calcola prezzo del giocatore selezionato
            if pos in custom_credits:
                price = max(self._to_float(custom_credits[pos], 1), 1)
            else:
                player_id = player_data.get('id', '')
                if player_id:
                    price = self._get_price_credits(player_id)
                else:
                    price = 1

            selected_cost_total += price
            selected_cost_by_role[role] += price

        # Prepara candidati per tutti gli slot di tutti i ruoli
        all_slots = []
        slot_index = 0

        selected_ids = [p['id'] for p in selected_players.values() if 'id' in p]

        slots_without_candidates = []

        # Soglie minime presenze - definite una sola volta qui
        MIN_PRESENZE = {
            'P': 5,
            'D': 24,
            'C': 24,
            'A': 24,
        }

        for role in ['P', 'D', 'C', 'A']:
            if not classification[role]:
                continue

            available = self.df[self.df['R'].str.startswith(role, na=False)].copy()
            available = available[~available['Id'].isin(selected_ids)]

            if blacklisted_teams:
                available = available[~available['Squadra'].isin(blacklisted_teams)]

            # FILTRO PRESENZE: applica PRIMA di passare ai candidati
            role_letter = role[0]
            min_required = MIN_PRESENZE.get(role_letter, 18)

            # Converti Pv_recent in numerico e filtra
            available['Pv_recent_numeric'] = available['Pv_recent'].apply(
                lambda x: self._to_float(x, 0)
            )
            available = available[available['Pv_recent_numeric'] >= min_required]

            if available.empty:
                for slot_info in classification[role]:
                    if slot_info['pos'] not in selected_players:
                        slots_without_candidates.append({
                            'role': role,
                            'pos': slot_info['pos'],
                            'tier': slot_info['tier'],
                            'budget': slot_info['budget']
                        })
                continue

            for slot_info in classification[role]:
                pos = slot_info['pos']
                tier_budget = slot_info['budget']
                weight = slot_info['weight']

                if pos in selected_players:
                    continue

                candidates = self._get_candidates_for_slot(
                    available, pos, tier_budget, weight, value_weights, custom_credits
                )

                if candidates:
                    all_slots.append({
                        'pos': pos,
                        'role': role,
                        'tier_budget': tier_budget,
                        'weight': weight,
                        'candidates': candidates,
                        'index': slot_index
                    })
                    slot_index += 1
                else:
                    slots_without_candidates.append({
                        'role': role,
                        'pos': pos,
                        'tier': slot_info['tier'],
                        'budget': tier_budget
                    })

        # Verifica se ci sono slot senza candidati
        if slots_without_candidates:
            print(f"\nATTENZIONE: {len(slots_without_candidates)} slot senza candidati compatibili:")
            for slot in slots_without_candidates:
                print(f"  Ruolo {slot['role']}, Posizione {slot['pos']}, Fascia '{slot['tier']}', Budget {slot['budget']:.1f} crediti")
            print("\nProva a:")
            print("- Aumentare il budget per questi ruoli")
            print("- Rimuovere vincoli di blacklist")
            print("- Modificare i giocatori già selezionati")
            return {}

        if not all_slots:
            print("Nessuno slot da ottimizzare")
            return {}

        # Variabili: x[i][j] = 1 se giocatore j assegnato a slot i
        x = {}
        for i, slot_info in enumerate(all_slots):
            for j, candidate in enumerate(slot_info['candidates']):
                x[(i, j)] = model.NewBoolVar(f'x_s{i}_p{j}')

        # Vincolo 1: Ogni slot deve avere esattamente 1 giocatore
        for i in range(len(all_slots)):
            model.Add(sum(x[(i, j)] for j in range(len(all_slots[i]['candidates']))) == 1)

        # Vincolo 2: Ogni giocatore può essere assegnato a max 1 slot
        player_to_slots = {}
        for i, slot_info in enumerate(all_slots):
            for j, candidate in enumerate(slot_info['candidates']):
                player_id = candidate['id']
                if player_id not in player_to_slots:
                    player_to_slots[player_id] = []
                player_to_slots[player_id].append((i, j))

        for player_id, slots in player_to_slots.items():
            if len(slots) > 1:
                model.Add(sum(x[slot] for slot in slots) <= 1)

        # Vincolo 3: Budget totale rosa (inclusi giocatori già selezionati)
        total_budget_credits = self.budget
        generated_cost = sum(
            round(all_slots[i]['candidates'][j]['price'] * SCALE) * x[(i, j)]
            for i in range(len(all_slots))
            for j in range(len(all_slots[i]['candidates']))
        )
        model.Add(generated_cost + round(selected_cost_total * SCALE) <= round(total_budget_credits * SCALE))

        # Vincolo 4: Budget residuo per ruolo sui giocatori generati.
        MIN_ROLE_USAGE = 0.95
        ROLE_OVERFLOW = {
            'P': 30,
            'D': 30,
            'C': 20,
            'A': 20,
        }

        for role in ['P', 'D', 'C', 'A']:
            role_slots = [i for i, s in enumerate(all_slots) if s['role'] == role]
            if role_slots:
                role_total_budget = (
                    self._to_float(budget_per_role.get(role, 0), 0) / 100.0
                ) * self.budget
                role_remaining_budget = max(
                    role_total_budget - selected_cost_by_role[role],
                    0,
                )
                max_role_cost = role_remaining_budget + ROLE_OVERFLOW.get(role, 0)
                generated_role_cost = sum(
                    round(all_slots[i]['candidates'][j]['price'] * SCALE) * x[(i, j)]
                    for i in role_slots
                    for j in range(len(all_slots[i]['candidates']))
                )

                model.Add(generated_role_cost <= round(max_role_cost * SCALE))

                # Vincolo minimo solo se il residuo permette almeno 1 giocatore
                if role_remaining_budget >= 1.0:
                    model.Add(
                        generated_role_cost >= round(
                            role_remaining_budget * MIN_ROLE_USAGE * SCALE
                        )
                    )

        # VINCOLO PER FASCIA RIMOSSO - il budget totale del ruolo è sufficiente
        # I pesi delle fasce guidano comunque l'assegnazione top/economici appropriati
        # for i, slot_info in enumerate(all_slots):
        #     slot_cost = sum(...)
        #     model.Add(slot_cost <= round(slot_info['tier_budget'] * SCALE))

        # Obiettivo: Massimizza score totale pesato + bonus spesa
        SCORE_SCALE = 100
        SPEND_BONUS = 0  # Rimosso - i bonus élite e i vincoli budget sono sufficienti

        objective = sum(
            (
                round(all_slots[i]['candidates'][j]['score'] * SCORE_SCALE)
                + round(all_slots[i]['candidates'][j]['price'] * SPEND_BONUS)
            ) * x[(i, j)]
            for i in range(len(all_slots))
            for j in range(len(all_slots[i]['candidates']))
        )
        model.Maximize(objective)

        # Risolvi
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 15.0
        status = solver.Solve(model)

        # Ricostruisci risultato
        result = {}

        if status == cp_model.OPTIMAL:
            for i, slot_info in enumerate(all_slots):
                for j, candidate in enumerate(slot_info['candidates']):
                    if solver.Value(x[(i, j)]) == 1:
                        result[slot_info['pos']] = candidate['player']
                        break
        elif status == cp_model.FEASIBLE:
            print("NOTA: Soluzione ammissibile trovata (non ottimale)")
            for i, slot_info in enumerate(all_slots):
                for j, candidate in enumerate(slot_info['candidates']):
                    if solver.Value(x[(i, j)]) == 1:
                        result[slot_info['pos']] = candidate['player']
                        break
        elif status == cp_model.INFEASIBLE:
            print("\nIMPOSSIBILE trovare una rosa compatibile con i vincoli:")
            print(f"- Budget totale: {total_budget_credits:.1f} crediti")
            print(f"- Budget già usato: {selected_cost_total:.1f} crediti")
            print(f"- Budget disponibile: {total_budget_credits - selected_cost_total:.1f} crediti")
            print(f"- Slot da riempire: {len(all_slots)}")
            print("\nBudget per ruolo:")
            for role in ['P', 'D', 'C', 'A']:
                role_total_budget = (
                    self._to_float(budget_per_role.get(role, 0), 0) / 100.0
                ) * self.budget
                role_remaining_budget = max(
                    role_total_budget - selected_cost_by_role[role],
                    0,
                )
                print(
                    f"  {role}: {role_total_budget:.1f} assegnati, "
                    f"{selected_cost_by_role[role]:.1f} manuali, "
                    f"{role_remaining_budget:.1f} residui per i generati"
                )
            print("\nProva a:")
            print("- Aumentare il budget per alcuni ruoli")
            print("- Rimuovere o modificare giocatori già selezionati costosi")
            print("- Ridurre le squadre blacklistate")
        else:
            print(f"Solver terminato con status: {status}")

        return result

    def _get_candidates_for_slot(self, available, pos, tier_budget, weight, value_weights, custom_credits):
        """
        Prepara candidati per uno slot applicando vincolo rigido di fascia

        Mantiene:
        - Top candidati per score
        - Candidati più economici
        - Candidati non dominati (Pareto-ottimali)

        Args:
            available: DataFrame giocatori disponibili
            pos: Posizione slot
            tier_budget: Budget fascia (vincolo rigido)
            weight: Peso fascia
            value_weights: Pesi FM/MV/PV
            custom_credits: Crediti custom

        Returns:
            Lista candidati [{player, price, score, id}]
        """
        min_credits = 1.0
        candidates = []

        # Soglie minime presenze recenti per ruolo
        MIN_PRESENZE = {
            'P': 5,
            'D': 24,
            'C': 24,
            'A': 24,
        }

        for idx, player_row in available.iterrows():
            player_id = player_row.get('Id', '')
            team = player_row.get('Squadra', '')

            # Filtra per presenze recenti
            role_letter = str(player_row.get('R', ''))[0] if player_row.get('R') else ''
            presenze = self._to_float(player_row.get('Pv_recent', 0), 0)
            min_required = MIN_PRESENZE.get(role_letter, 18)

            if presenze < min_required:
                continue

            # Calcola prezzo
            if pos in custom_credits:
                price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
            else:
                price = self._get_price_credits(player_id)

            # NON filtrare per tier_budget - il vincolo è sul budget totale del ruolo
            # Il peso della fascia guiderà comunque la scelta verso top/economici appropriati

            # Calcola score
            fm = self._to_float(player_row.get('Fm_weighted', 0), 0)
            mv = self._to_float(player_row.get('MV', 0), 0)
            pv = self._to_float(player_row.get('PV', 0), 0)
            overall = self._to_float(player_row.get('Overall', 'N/A'), 0)

            base_score = (
                fm * value_weights['FM'] +
                mv * value_weights['MV'] +
                pv * value_weights['PV']
            )

            # Bonus élite basato su rendimento
            elite_bonus = 0
            if fm >= 7.0:
                elite_bonus += 200
            if overall >= 85:
                elite_bonus += 150

            # Applica peso fascia per rendimenti decrescenti
            weighted_score = (base_score + elite_bonus) * weight

            player_dict = {
                'id': player_id,
                'name': player_row.get('Nome', ''),
                'role': player_row.get('R', ''),
                'squadra': team,
                'price': price,
                'overall': player_row.get('Overall', 'N/A')
            }

            candidates.append({
                'player': player_dict,
                'price': price,
                'score': weighted_score,
                'id': player_id
            })

        if not candidates:
            return []

        # Ordina per score decrescente
        candidates.sort(key=lambda x: (-x['score'], x['price']))

        # Mantieni: top 20 per score + 10 più economici + Pareto-ottimali
        top_by_score = candidates[:20]
        cheapest = sorted(candidates, key=lambda x: x['price'])[:10]

        # Pareto-ottimali: nessun altro candidato ha score >= e price <=
        pareto = []
        for c1 in candidates:
            dominated = False
            for c2 in candidates:
                if c2['id'] != c1['id'] and c2['score'] >= c1['score'] and c2['price'] <= c1['price']:
                    if c2['score'] > c1['score'] or c2['price'] < c1['price']:
                        dominated = True
                        break
            if not dominated:
                pareto.append(c1)

        # Unisci e rimuovi duplicati
        result = {c['id']: c for c in top_by_score + cheapest + pareto}
        return list(result.values())[:50]  # Limite massimo 50

    def _knapsack_dynamic_programming(self, role, tier_slots, selected_players, value_weights,
                                      blacklisted_teams, position_roles, custom_credits):
        """
        Algoritmo zaino multidimensionale con CP-SAT solver

        Modella il problema come ottimizzazione binaria con vincoli:
        - Ogni slot deve avere esattamente 1 giocatore
        - Ogni giocatore può essere assegnato a max 1 slot
        - Budget totale per ruolo rispettato
        - Budget per fascia rispettato (soft constraint)
        - Massimizza valore totale pesato

        Args:
            role: Ruolo da ottimizzare
            tier_slots: Lista slot con fasce [{pos, tier, budget, weight}]
            selected_players: Giocatori già selezionati
            value_weights: Pesi FM/MV/PV
            blacklisted_teams: Squadre escluse
            position_roles: Mapping ruoli
            custom_credits: Crediti custom per posizione

        Returns:
            Dict {posizione: player_data}
        """
        if not tier_slots:
            return {}

        # Se OR-Tools non disponibile, usa fallback greedy
        if not HAS_ORTOOLS:
            return self._optimize_role_greedy(role, tier_slots, selected_players, value_weights,
                                             blacklisted_teams, position_roles, custom_credits)

        # Prepara giocatori disponibili per il ruolo
        available = self.df[self.df['R'].str.startswith(role, na=False)].copy()
        selected_ids = [p['id'] for p in selected_players.values() if 'id' in p]
        available = available[~available['Id'].isin(selected_ids)]

        if blacklisted_teams:
            available = available[~available['Squadra'].isin(blacklisted_teams)]

        if available.empty:
            return {}

        min_credits = 1.0

        # Calcola budget totale disponibile per il ruolo
        total_budget = sum(slot['budget'] for slot in tier_slots)

        # Crea lista di candidati per ogni slot con score e prezzo
        slot_candidates = []
        for slot_info in tier_slots:
            pos = slot_info['pos']
            tier_budget = slot_info['budget']
            weight = slot_info['weight']

            # Se già selezionato dall'utente, salta
            if pos in selected_players:
                continue

            candidates = []
            for idx, player_row in available.iterrows():
                player_id = player_row.get('Id', '')
                team = player_row.get('Squadra', '')

                # Calcola prezzo
                if pos in custom_credits:
                    price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
                else:
                    price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                    price = max(self._to_float(price_data.get('absolute', 0), min_credits), min_credits)

                # Applica vincolo fascia: salta candidati troppo costosi per questa fascia
                if price > tier_budget * 1.5:  # Tolleranza 50% per flessibilità
                    continue

                # Calcola score con peso fascia
                fm = self._to_float(player_row.get('Fm_weighted', 0), 0)
                mv = self._to_float(player_row.get('MV', 0), 0)
                pv = self._to_float(player_row.get('PV', 0), 0)

                base_score = (
                    fm * value_weights['FM'] +
                    mv * value_weights['MV'] +
                    pv * value_weights['PV']
                )
                weighted_score = base_score * weight

                # Crea dict giocatore
                player_dict = {
                    'id': player_id,
                    'name': player_row.get('Nome', ''),
                    'role': player_row.get('R', ''),
                    'squadra': team,
                    'price': price,
                    'overall': player_row.get('Overall', 'N/A')
                }

                candidates.append({
                    'player': player_dict,
                    'price': price,
                    'score': weighted_score,
                    'id': player_id
                })

            if not candidates:
                # Rilassa vincolo: prendi almeno i 5 più economici
                all_candidates = []
                for idx, player_row in available.iterrows():
                    player_id = player_row.get('Id', '')
                    team = player_row.get('Squadra', '')

                    if pos in custom_credits:
                        price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
                    else:
                        price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                        price = max(self._to_float(price_data.get('absolute', 0), min_credits), min_credits)

                    fm = self._to_float(player_row.get('Fm_weighted', 0), 0)
                    mv = self._to_float(player_row.get('MV', 0), 0)
                    pv = self._to_float(player_row.get('PV', 0), 0)

                    base_score = (fm * value_weights['FM'] + mv * value_weights['MV'] + pv * value_weights['PV'])
                    weighted_score = base_score * weight

                    player_dict = {
                        'id': player_id,
                        'name': player_row.get('Nome', ''),
                        'role': player_row.get('R', ''),
                        'squadra': team,
                        'price': price,
                        'overall': player_row.get('Overall', 'N/A')
                    }

                    all_candidates.append({
                        'player': player_dict,
                        'price': price,
                        'score': weighted_score,
                        'id': player_id
                    })

                all_candidates.sort(key=lambda x: x['price'])
                candidates = all_candidates[:5]

            slot_candidates.append({
                'pos': pos,
                'tier_budget': tier_budget,
                'candidates': candidates[:30],  # Limita per performance
                'weight': weight
            })

        if not slot_candidates:
            return {}

        # Crea modello CP-SAT
        model = cp_model.CpModel()

        # Variabili: x[i][j] = 1 se giocatore j assegnato a slot i
        x = {}
        for i, slot_info in enumerate(slot_candidates):
            for j, candidate in enumerate(slot_info['candidates']):
                x[(i, j)] = model.NewBoolVar(f'x_s{i}_p{j}')

        # Vincolo 1: Ogni slot deve avere esattamente 1 giocatore
        for i in range(len(slot_candidates)):
            model.Add(sum(x[(i, j)] for j in range(len(slot_candidates[i]['candidates']))) == 1)

        # Vincolo 2: Ogni giocatore può essere assegnato a max 1 slot
        player_to_slots = {}
        for i, slot_info in enumerate(slot_candidates):
            for j, candidate in enumerate(slot_info['candidates']):
                player_id = candidate['id']
                if player_id not in player_to_slots:
                    player_to_slots[player_id] = []
                player_to_slots[player_id].append((i, j))

        for player_id, slots in player_to_slots.items():
            if len(slots) > 1:
                model.Add(sum(x[slot] for slot in slots) <= 1)

        # Vincolo 3: Budget totale per ruolo
        total_cost = sum(
            int(slot_candidates[i]['candidates'][j]['price']) * x[(i, j)]
            for i in range(len(slot_candidates))
            for j in range(len(slot_candidates[i]['candidates']))
        )
        model.Add(total_cost <= int(total_budget * 1.05))  # Tolleranza 5%

        # Obiettivo: Massimizza score totale
        objective = sum(
            int(slot_candidates[i]['candidates'][j]['score'] * 1000) * x[(i, j)]
            for i in range(len(slot_candidates))
            for j in range(len(slot_candidates[i]['candidates']))
        )
        model.Maximize(objective)

        # Risolvi
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status = solver.Solve(model)

        # Ricostruisci risultato
        result = {}
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for i, slot_info in enumerate(slot_candidates):
                for j, candidate in enumerate(slot_info['candidates']):
                    if solver.Value(x[(i, j)]) == 1:
                        result[slot_info['pos']] = candidate['player']
                        break

        return result

    def _optimize_role_greedy(self, role, tier_slots, selected_players, value_weights,
                              blacklisted_teams, position_roles, custom_credits):
        """
        Fallback greedy quando OR-Tools non disponibile

        NOTA: Questo è un fallback di emergenza che non garantisce la stessa qualità
        del solver CP-SAT. Risolve i ruoli separatamente e applica vincoli rigidi
        per fascia, ma non può ottimizzare globalmente.

        Args:
            role: Ruolo da ottimizzare
            tier_slots: Lista slot con fasce
            selected_players: Giocatori già selezionati
            value_weights: Pesi FM/MV/PV
            blacklisted_teams: Squadre escluse
            position_roles: Mapping ruoli
            custom_credits: Crediti custom per posizione

        Returns:
            Dict {posizione: player_data}
        """
        available = self.df[self.df['R'].str.startswith(role, na=False)].copy()
        selected_ids = [p['id'] for p in selected_players.values() if 'id' in p]
        available = available[~available['Id'].isin(selected_ids)]

        if blacklisted_teams:
            available = available[~available['Squadra'].isin(blacklisted_teams)]

        if available.empty:
            return {}

        result = {}
        used_ids = set()
        min_credits = 1.0
        total_budget = sum(slot['budget'] for slot in tier_slots)
        budget_used = 0.0

        for slot_info in tier_slots:
            pos = slot_info['pos']
            tier_budget = slot_info['budget']
            weight = slot_info['weight']

            if pos in selected_players:
                result[pos] = selected_players[pos]
                continue

            budget_remaining = total_budget - budget_used

            best_candidate = None
            best_score = -float('inf')

            for idx, player_row in available.iterrows():
                player_id = player_row.get('Id', '')

                if player_id in used_ids:
                    continue

                team = player_row.get('Squadra', '')

                if pos in custom_credits:
                    price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
                else:
                    price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                    price = max(self._to_float(price_data.get('absolute', 0), min_credits), min_credits)

                # Vincoli rigidi: budget fascia E budget rimanente
                if price > tier_budget or price > budget_remaining:
                    continue

                fm = self._to_float(player_row.get('Fm_weighted', 0), 0)
                mv = self._to_float(player_row.get('MV', 0), 0)
                pv = self._to_float(player_row.get('PV', 0), 0)

                base_score = (
                    fm * value_weights['FM'] +
                    mv * value_weights['MV'] +
                    pv * value_weights['PV']
                )
                weighted_score = base_score * weight

                if weighted_score > best_score:
                    best_score = weighted_score
                    best_candidate = {
                        'id': player_id,
                        'name': player_row.get('Nome', ''),
                        'role': player_row.get('R', ''),
                        'squadra': team,
                        'price': price,
                        'overall': player_row.get('Overall', 'N/A')
                    }

            if best_candidate:
                result[pos] = best_candidate
                used_ids.add(best_candidate['id'])
                budget_used += best_candidate['price']
            # Se non trova candidato, lascia slot vuoto (non viola budget)

        return result

    def _optimize_role_with_tiers(self, role, tier_slots, selected_players, value_weights, result, blacklisted_teams, position_roles, custom_credits):
        """
        Ottimizza un ruolo usando il sistema a fasce con rendimenti decrescenti.

        Args:
            role: Ruolo da ottimizzare ('P', 'D', 'C', 'A')
            tier_slots: Lista di slot con tier structure [{'pos': idx, 'tier': name, 'budget': pct, 'weight': w}]
            selected_players: Giocatori già selezionati dall'utente
            value_weights: Pesi per FM/MV/PV
            result: Dizionario risultati da popolare
            blacklisted_teams: Set squadre blacklisted
            position_roles: Dict mapping posizioni a ruoli
            custom_credits: Dict crediti custom per giocatore
        """
        # Filtra giocatori per ruolo dal DataFrame
        available = self.df[self.df['R'].str.startswith(role, na=False)].copy()

        # IDs già selezionati
        selected_ids = [p['id'] for p in result.values() if 'id' in p]
        selected_ids.extend([p['id'] for p in selected_players.values() if 'id' in p])

        for slot_info in tier_slots:
            pos = slot_info['pos']
            tier = slot_info['tier']
            tier_budget = slot_info['budget']  # già in crediti assoluti
            weight = slot_info['weight']

            # Se l'utente ha già selezionato un giocatore in questa posizione
            if pos in selected_players:
                result[pos] = selected_players[pos]
                continue

            # Minimo 1 credito
            min_credits = 1.0

            # Filtra candidati
            candidates = []
            for idx, player_row in available.iterrows():
                player_id = player_row.get('Id', '')

                # Salta se già selezionato
                if player_id in selected_ids:
                    continue

                # Salta se squadra blacklisted
                team = player_row.get('Squadra', '')
                if team in blacklisted_teams:
                    continue

                # Calcola prezzo effettivo (usa pos per custom_credits, non player_id)
                if pos in custom_credits:
                    price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
                else:
                    price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                    price = max(self._to_float(price_data.get('absolute', 0), min_credits), min_credits)

                # Verifica se rientra nel budget della fascia
                if price <= tier_budget:
                    # Calcola score pesato per la fascia
                    try:
                        fm = float(player_row.get('Fm_weighted', 0) or 0)
                    except (ValueError, TypeError):
                        fm = 0

                    try:
                        mv = float(player_row.get('MV', 0) or 0)
                    except (ValueError, TypeError):
                        mv = 0

                    try:
                        pv = float(player_row.get('PV', 0) or 0)
                    except (ValueError, TypeError):
                        pv = 0

                    base_score = (
                        fm * value_weights['FM'] +
                        mv * value_weights['MV'] +
                        pv * value_weights['PV']
                    )

                    # Applica peso fascia per rendimenti decrescenti
                    weighted_score = base_score * weight

                    # Converti player_row in dizionario compatibile
                    player_dict = {
                        'id': player_id,
                        'name': player_row.get('Nome', ''),
                        'role': player_row.get('R', ''),
                        'squadra': team,
                        'price': price,
                        'overall': player_row.get('Overall', 'N/A')
                    }

                    candidates.append({
                        'player': player_dict,
                        'price': price,
                        'score': weighted_score
                    })

            # Seleziona miglior candidato
            if candidates:
                # Ordina per score decrescente
                candidates.sort(key=lambda x: x['score'], reverse=True)
                best = candidates[0]
                result[pos] = best['player']
                selected_ids.append(best['player']['id'])
            else:
                # Se non ci sono candidati entro il budget della fascia, prendi il più economico disponibile
                # NOTA: questo può violare il budget della fascia ma garantisce una rosa completa
                cheapest = None
                cheapest_price = float('inf')

                for idx, player_row in available.iterrows():
                    player_id = player_row.get('Id', '')

                    # Salta se già selezionato
                    if player_id in selected_ids:
                        continue

                    # Salta se blacklisted
                    team = player_row.get('Squadra', '')
                    if team in blacklisted_teams:
                        continue

                    # Calcola prezzo (usa pos per custom_credits)
                    if pos in custom_credits:
                        price = max(self._to_float(custom_credits[pos], min_credits), min_credits)
                    else:
                        price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                        price = max(self._to_float(price_data.get('absolute', 0), min_credits), min_credits)

                    if price < cheapest_price:
                        cheapest_price = price
                        cheapest = {
                            'id': player_id,
                            'name': player_row.get('Nome', ''),
                            'role': player_row.get('R', ''),
                            'squadra': team,
                            'price': price,
                            'overall': player_row.get('Overall', 'N/A')
                        }

                if cheapest:
                    result[pos] = cheapest
                    selected_ids.append(cheapest['id'])

        return result

    def _optimize_goalkeepers(self, gk_slots: Dict, budget_pct: float,
                             selected_players: Dict, value_weights: Dict,
                             result: Dict, blacklisted_teams: set,
                             position_roles: List[str], custom_credits: Dict[int, float]) -> Dict:
        """Ottimizza selezione portieri con vincoli specifici"""
        titolari_slots = gk_slots['titolari']
        low_cost_slots = gk_slots['low_cost']

        if not titolari_slots and not low_cost_slots:
            return result

        # Calcola budget usato da giocatori già selezionati per questo ruolo
        used_budget_pct = 0
        manual_gk_team = None
        manual_gk_id = None

        for pos_idx, player_data in selected_players.items():
            if position_roles[pos_idx] == 'P':
                if pos_idx in custom_credits:
                    used_budget_pct += (custom_credits[pos_idx] / self.budget) * 100
                else:
                    price_data = self.price_calculator.calculate_price_percentage(
                        player_data['id'], self.budget
                    )
                    used_budget_pct += price_data.get('percentage', 0)

                # Memorizza squadra del portiere manuale
                manual_gk_team = player_data.get('squadra')
                manual_gk_id = player_data.get('id')

        remaining_budget_pct = budget_pct - used_budget_pct

        # Giocatori disponibili
        available = self.df[self.df['R'].str.startswith('P', na=False)].copy()
        selected_ids = [p['id'] for p in selected_players.values()]
        available = available[~available['Id'].isin(selected_ids)]

        if blacklisted_teams:
            available = available[~available['Squadra'].isin(blacklisted_teams)]

        if available.empty:
            return result

        available['Fm_weighted'] = pd.to_numeric(available['Fm_weighted'], errors='coerce').fillna(0)
        available['price_pct'] = available['Id'].apply(
            lambda pid: self.price_calculator.calculate_price_percentage(pid, self.budget).get('percentage', 0)
        )
        min_price_pct = (1.0 / self.budget) * 100
        available['price_pct'] = available['price_pct'].apply(lambda p: max(p, min_price_pct))

        # Converti price_pct in crediti assoluti per confronto con soglia 5
        available['price_credits'] = available['price_pct'] * self.budget / 100.0

        # Se c'è un portiere manuale, cerca prima il secondo della stessa squadra
        if manual_gk_team and len(titolari_slots) > 0:
            same_team = available[
                (available['Squadra'] == manual_gk_team) &
                (available['price_credits'] < 5.0)
            ]

            if not same_team.empty:
                best_same_team = same_team.nlargest(1, 'Fm_weighted').iloc[0]
                result[titolari_slots[0]] = {
                    'id': best_same_team['Id'],
                    'name': best_same_team['Nome'],
                    'role': best_same_team['R'],
                    'squadra': best_same_team['Squadra'],
                    'overall': best_same_team['Overall']
                }
                available = available[available['Id'] != best_same_team['Id']]
                titolari_slots = titolari_slots[1:]

                # Se serve il terzo, prendilo a 1 credito dalla stessa squadra
                if len(low_cost_slots) > 0:
                    terzo_same_team = available[
                        (available['Squadra'] == manual_gk_team) &
                        (available['price_credits'] <= 1.0)
                    ]
                    if not terzo_same_team.empty:
                        terzo = terzo_same_team.iloc[0]
                        result[low_cost_slots[0]] = {
                            'id': terzo['Id'],
                            'name': terzo['Nome'],
                            'role': terzo['R'],
                            'squadra': terzo['Squadra'],
                            'overall': terzo['Overall']
                        }
                        available = available[available['Id'] != terzo['Id']]
                        low_cost_slots = low_cost_slots[1:]

        # Se servono ancora titolari (coppia senza manuale o secondo slot), usa griglia
        if len(titolari_slots) >= 2:
            pairs = self.get_goalkeeper_pairs(available)

            if pairs:
                # Filtra coppie dove riserva < 5 crediti
                valid_pairs = []
                for p in pairs:
                    tit_price_pct = self.price_calculator.calculate_price_percentage(
                        p['titolare']['Id'], self.budget
                    ).get('percentage', 0)
                    ris_price_pct = self.price_calculator.calculate_price_percentage(
                        p['riserva']['Id'], self.budget
                    ).get('percentage', 0)
                    ris_price_credits = ris_price_pct * self.budget / 100.0
                    total_pct = tit_price_pct + ris_price_pct

                    if ris_price_credits < 5.0 and total_pct <= remaining_budget_pct:
                        valid_pairs.append(p)

                if valid_pairs:
                    # Ordina per score (già fatto in get_goalkeeper_pairs, migliori prima)
                    # Score più alto = migliore (same_team=100, grid=50-grid_value)
                    best_pair = valid_pairs[0]

                    result[titolari_slots[0]] = {
                        'id': best_pair['titolare']['Id'],
                        'name': best_pair['titolare']['Nome'],
                        'role': best_pair['titolare']['R'],
                        'squadra': best_pair['titolare']['Squadra'],
                        'overall': best_pair['titolare']['Overall']
                    }
                    result[titolari_slots[1]] = {
                        'id': best_pair['riserva']['Id'],
                        'name': best_pair['riserva']['Nome'],
                        'role': best_pair['riserva']['R'],
                        'squadra': best_pair['riserva']['Squadra'],
                        'overall': best_pair['riserva']['Overall']
                    }
                    available = available[
                        (~available['Id'].isin([best_pair['titolare']['Id'], best_pair['riserva']['Id']]))
                    ]
                    titolari_slots = titolari_slots[2:]

        # Slot titolari rimanenti: budget rimanente, riserva < 5 crediti
        for slot in titolari_slots:
            # Secondo/terzo portiere: sotto 5 crediti
            if slot != titolari_slots[0] if titolari_slots else False:
                candidates = available[available['price_credits'] < 5.0]
            else:
                # Primo portiere: usa budget
                budget_slot = remaining_budget_pct / max(1, len(titolari_slots))
                candidates = available[available['price_pct'] <= budget_slot]

            if candidates.empty:
                continue

            best = candidates.nlargest(1, 'Fm_weighted').iloc[0]
            result[slot] = {
                'id': best['Id'],
                'name': best['Nome'],
                'role': best['R'],
                'squadra': best['Squadra'],
                'overall': best['Overall']
            }
            available = available[available['Id'] != best['Id']]

        # Slot low-cost: sempre sotto 5 crediti, preferibilmente 1
        for slot in low_cost_slots:
            candidates = available[available['price_credits'] <= 5.0]
            # Preferisci a 1 credito
            one_credit = candidates[candidates['price_credits'] <= 1.0]
            if not one_credit.empty:
                candidates = one_credit

            if candidates.empty:
                continue

            best = candidates.nlargest(1, 'Fm_weighted').iloc[0]
            result[slot] = {
                'id': best['Id'],
                'name': best['Nome'],
                'role': best['R'],
                'squadra': best['Squadra'],
                'overall': best['Overall']
            }
            available = available[available['Id'] != best['Id']]

        return result

    def _optimize_role(self, role: str, role_slots: Dict, budget_pct: float,
                      selected_players: Dict, value_weights: Dict,
                      result: Dict, blacklisted_teams: set,
                      position_roles: List[str], custom_credits: Dict[int, float]) -> Dict:
        """Ottimizza selezione per un ruolo"""
        titolari_slots = role_slots['titolari']
        low_cost_slots = role_slots['low_cost']

        if not titolari_slots and not low_cost_slots:
            return result

        # Calcola budget usato da giocatori già selezionati per questo ruolo
        used_budget_pct = 0
        for pos_idx, player_data in selected_players.items():
            if position_roles[pos_idx] == role:
                if pos_idx in custom_credits:
                    # Usa prezzo custom
                    used_budget_pct += (custom_credits[pos_idx] / self.budget) * 100
                else:
                    # Usa prezzo calcolato
                    price_data = self.price_calculator.calculate_price_percentage(
                        player_data['id'], self.budget
                    )
                    used_budget_pct += price_data.get('percentage', 0)

        # Budget rimanente per slot vuoti
        remaining_budget_pct = budget_pct - used_budget_pct

        # Riserva budget per low-cost (1% ciascuno)
        low_cost_budget = len(low_cost_slots) * 1.0
        budget_for_titolari = remaining_budget_pct - low_cost_budget

        # Giocatori disponibili
        available = self.df[self.df['R'].str.startswith(role, na=False)].copy()
        selected_ids = [p['id'] for p in selected_players.values()] + [result[k]['id'] for k in result]
        available = available[~available['Id'].isin(selected_ids)]

        # Filtra squadre blacklist
        if blacklisted_teams:
            available = available[~available['Squadra'].isin(blacklisted_teams)]

        if available.empty:
            return result

        # Converti colonne
        available['Fm_weighted'] = pd.to_numeric(available['Fm_weighted'], errors='coerce').fillna(0)
        available['Mv_weighted'] = pd.to_numeric(available['Mv_weighted'], errors='coerce').fillna(0)
        available['Pv_weighted'] = pd.to_numeric(available.get('Pv_weighted', available['Mv_weighted']), errors='coerce').fillna(0)

        # Score composito
        available['score'] = (
            available['Fm_weighted'] * value_weights['FM'] +
            available['Mv_weighted'] * value_weights['MV'] +
            available['Pv_weighted'] * value_weights['PV']
        )

        # Calcola prezzi
        available['price_pct'] = available['Id'].apply(
            lambda pid: self.price_calculator.calculate_price_percentage(pid, self.budget).get('percentage', 0)
        )

        # Forza prezzo minimo di 1 credito
        min_price_pct = (1.0 / self.budget) * 100
        available['price_pct'] = available['price_pct'].apply(lambda p: max(p, min_price_pct))

        # Calcola rapporto valore/prezzo per ottimizzazione budget
        available['value_ratio'] = available['score'] / (available['price_pct'] + 0.1)  # +0.1 per evitare divisione per zero

        # Riempi titolari con strategia greedy per massimizzare utilizzo budget
        if titolari_slots:
            for slot in titolari_slots:
                # Usa il budget rimanente per titolari
                candidates = available[available['price_pct'] <= budget_for_titolari]

                if candidates.empty:
                    # Budget esaurito: cerca il giocatore PIÙ ECONOMICO tra quelli rimasti
                    if available.empty:
                        continue
                    best = available.nsmallest(1, 'price_pct').iloc[0]
                else:
                    # Strategia: seleziona il giocatore PIÙ COSTOSO tra i top 10 per score
                    # Questo massimizza l'utilizzo del budget prendendo comunque buoni giocatori
                    top_candidates = candidates.nlargest(10, 'score')
                    best = top_candidates.nlargest(1, 'price_pct').iloc[0]

                result[slot] = {
                    'id': best['Id'],
                    'name': best['Nome'],
                    'role': best['R'],
                    'squadra': best['Squadra'],
                    'overall': best['Overall']
                }

                # Sottrai dal budget rimanente per titolari
                budget_for_titolari -= best['price_pct']
                available = available[available['Id'] != best['Id']]

        # Riempi low-cost
        for slot in low_cost_slots:
            low_cost_candidates = available[available['price_pct'] <= 1.0]

            if low_cost_candidates.empty:
                continue

            best = low_cost_candidates.nlargest(1, 'score').iloc[0]

            result[slot] = {
                'id': best['Id'],
                'name': best['Nome'],
                'role': best['R'],
                'squadra': best['Squadra'],
                'overall': best['Overall']
            }

            available = available[available['Id'] != best['Id']]

        return result
