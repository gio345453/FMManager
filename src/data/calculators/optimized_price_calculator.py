"""
Calcolatore prezzi con algoritmo analitico avanzato.
Considera: contesto tattico, forza squadra, incidenza giocatore.
"""
import sys
import os

# Aggiungi il path per gli import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.titolarita_loader import load_titolarita_map
from src.data.clean_sheets_data import get_clean_sheets
import pandas as pd
import json


class OptimizedPriceCalculator:
    """Calcolatore prezzi con algoritmo analitico avanzato"""

    def __init__(self, players_df):
        self.players_df = players_df
        self.titolarita_map = load_titolarita_map()
        self.rigoristi_map = self._load_rigoristi_data()
        self.moduli = self._load_moduli_data()
        self.team_stats = self._calculate_team_stats()

        # Calcola score per tutti i giocatori (per ranking)
        self.all_scores = {'A': [], 'C': [], 'D': [], 'P': []}
        self._calculate_all_scores()

    def _load_rigoristi_data(self):
        """Carica rigoristi con pesi analitici"""
        tiratori_file = os.path.join('data', 'Tiratori', 'tiratori.json')
        rigoristi_map = {}

        if not os.path.exists(tiratori_file):
            return rigoristi_map

        try:
            with open(tiratori_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team_data in data:
                    rigoristi = team_data.get('rigoristi', {})
                    if '1_rigorista' in rigoristi:
                        nome = rigoristi['1_rigorista']
                        rigoristi_map[nome] = 1.0
                        rigoristi_map[nome + ' *'] = 1.0
                    if '2_rigorista' in rigoristi:
                        nome = rigoristi['2_rigorista']
                        rigoristi_map[nome] = 0.6
                        rigoristi_map[nome + ' *'] = 0.6
                    if '3_rigorista' in rigoristi:
                        nome = rigoristi['3_rigorista']
                        rigoristi_map[nome] = 0.3
                        rigoristi_map[nome + ' *'] = 0.3
        except Exception:
            pass

        return rigoristi_map

    def _load_moduli_data(self):
        """Carica moduli squadre"""
        moduli_file = os.path.join('data', 'Moduli', 'modulo.json')
        moduli = {}

        if not os.path.exists(moduli_file):
            return moduli

        try:
            with open(moduli_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team_data in data:
                    squadra = team_data.get('squadra', '')
                    modulo = team_data.get('modulo', '4-3-3')
                    moduli[squadra] = modulo
        except Exception:
            pass

        return moduli

    def _calculate_team_stats(self):
        """Calcola statistiche aggregate per squadra"""
        team_data = {}

        for _, row in self.players_df.iterrows():
            squadra = row.get('Squadra', '')
            if not squadra or squadra == 'Unknown':
                continue

            if squadra not in team_data:
                team_data[squadra] = {
                    'gol_totali': 0,
                    'assist_totali': 0,
                    'fm_sum': 0,
                    'fm_count': 0,
                    'clean_sheets': 0,
                    'gol_subiti': 0
                }

            # Estrai dati usando _get_stat_value
            gf = self._get_stat_value(row, 'Gf')
            ass = self._get_stat_value(row, 'Ass')
            fm = self._get_stat_value(row, 'Fm')
            pv = self._get_stat_value(row, 'Pv')
            role = row.get('R', '').split('/')[0].strip()  # Estrai ruolo base

            # Solo giocatori con presenze significative
            if pv > 10:
                team_data[squadra]['gol_totali'] += gf
                team_data[squadra]['assist_totali'] += ass

                if fm > 0:
                    team_data[squadra]['fm_sum'] += fm
                    team_data[squadra]['fm_count'] += 1

            # Portieri: clean sheets
            if role == 'P' and pv > 15:
                nome = row.get('Nome', '').replace(' *', '').strip()
                cs = get_clean_sheets(nome)
                gs = self._get_stat_value(row, 'Gs')
                if cs > team_data[squadra]['clean_sheets']:
                    team_data[squadra]['clean_sheets'] = cs
                    team_data[squadra]['gol_subiti'] = gs

        # Calcola metriche finali
        for squadra, data in team_data.items():
            data['fm_media'] = data['fm_sum'] / data['fm_count'] if data['fm_count'] > 0 else 6.0
            data['forza_offensiva'] = data['gol_totali'] + (data['assist_totali'] * 0.5)
            data['forza_difensiva'] = data['clean_sheets'] - (data['gol_subiti'] / 38 * 10) if data['gol_subiti'] > 0 else 0

        return team_data

    def _safe_float(self, value):
        """Converte in float gestendo valori non numerici"""
        if value is None or value == '' or pd.isna(value):
            return 0.0
        try:
            if isinstance(value, str):
                # Rimuovi simboli trend (↑↓→) se presenti
                value = value.replace('↑', '').replace('↓', '').replace('→', '').strip()
                value = value.replace(',', '.')
            return float(value)
        except:
            return 0.0

    def _get_stat_value(self, player_row, stat_name):
        """Estrae valore statistico dal DataFrame, gestendo colonne _weighted"""
        # Prova prima con _weighted (formato UI)
        weighted_col = f'{stat_name}_weighted'
        if weighted_col in player_row.index:
            return self._safe_float(player_row.get(weighted_col, 0))
        # Fallback su colonna diretta
        return self._safe_float(player_row.get(stat_name, 0))

    def _get_team_strength(self, squadra):
        """Calcola forza squadra (0-1)"""
        if squadra not in self.team_stats:
            return 0.5

        fm_media = self.team_stats[squadra].get('fm_media', 6.0)
        strength = (fm_media - 5.5) / 1.0
        return max(0.0, min(1.0, strength))

    def _get_player_impact(self, nome, squadra, metric='gol'):
        """Calcola % incidenza giocatore sul totale squadra"""
        if squadra not in self.team_stats:
            return 0.0

        team_total = self.team_stats[squadra].get(f'{metric}_totali', 0)
        if team_total == 0:
            return 0.0

        # Trova giocatore nel DataFrame
        nome_clean = nome.replace(' *', '').strip()
        player = self.players_df[self.players_df['Nome'].str.replace(' *', '').str.strip() == nome_clean]
        if player.empty:
            return 0.0

        if metric == 'gol':
            player_value = self._get_stat_value(player.iloc[0], 'Gf')
        elif metric == 'assist':
            player_value = self._get_stat_value(player.iloc[0], 'Ass')
        else:
            return 0.0

        return (player_value / team_total) * 100 if team_total > 0 else 0.0

    def _get_tactical_context(self, player_row):
        """Analizza contesto tattico dal modulo"""
        squadra = player_row.get('Squadra', '')
        role_full = player_row.get('R', '')

        # Estrai ruolo base e secondari
        # Formato: "A", "D (E)", "C/D", etc.
        role = role_full.split('/')[0].split('(')[0].strip()

        # Estrai ruoli multipli dalle parentesi o dopo /
        rm = ''
        if '(' in role_full:
            rm = role_full.split('(')[1].split(')')[0].strip()
        elif '/' in role_full:
            rm = role_full.split('/')[1].strip()

        modulo = self.moduli.get(squadra, '4-3-3')
        context = {
            'modulo': modulo,
            'is_punta_unica': False,
            'is_esterno_offensivo': False,
            'is_mediano': False,
            'difesa_a_tre': False
        }

        # Parse modulo
        parts = modulo.split('-')
        if len(parts) >= 3:
            num_attaccanti = int(parts[-1])
            num_difensori = int(parts[0])

            # Attaccanti
            if role == 'A' and num_attaccanti == 1:
                context['is_punta_unica'] = True
            if role == 'A' and ('W' in rm or 'A' in rm):
                context['is_esterno_offensivo'] = True

            # Centrocampisti
            if role == 'C':
                if 'M' in rm or 'C' in rm:
                    context['is_mediano'] = True
                if 'W' in rm or 'T' in rm or 'A' in rm:
                    context['is_esterno_offensivo'] = True

            # Difensori
            if role == 'D':
                if 'E' in rm:
                    context['is_esterno_offensivo'] = True
                context['difesa_a_tre'] = (num_difensori == 3)

        return context

    # ==================== ATTACCANTI ====================
    def _calculate_striker_price(self, player_row):
        """Algoritmo analitico per ATTACCANTI"""
        score = 0.0
        nome = player_row.get('Nome', '').replace(' *', '').strip()
        squadra = player_row.get('Squadra', '')

        # Contesto
        context = self._get_tactical_context(player_row)
        team_strength = self._get_team_strength(squadra)

        # Gol con peso variabile
        gf = self._get_stat_value(player_row, 'Gf')

        if context['is_punta_unica']:
            peso_gol = 1.6 if gf >= 12 else 1.3
        else:
            peso_gol = 1.5

        # Adjust per forza squadra
        peso_gol *= (0.8 + team_strength * 0.4)
        score += gf * peso_gol

        # Assist
        ass = self._get_stat_value(player_row, 'Ass')
        score += ass * 0.55

        # FM
        fm = self._get_stat_value(player_row, 'Fm')
        score += (fm - 6.0) * 3.2

        # Presenze
        pv = self._get_stat_value(player_row, 'Pv')
        score += (pv / 38) * 2.0

        # Rigori
        rigorista_peso = self.rigoristi_map.get(nome, 0)
        if rigorista_peso == 0:
            rigorista_peso = self.rigoristi_map.get(nome + ' *', 0)
        score += rigorista_peso * 3.2

        # Penalità cartellini
        amm = self._get_stat_value(player_row, 'Amm')
        esp = self._get_stat_value(player_row, 'Esp')
        score -= (amm * 0.07 + esp * 0.4)

        return max(0, score)

    # ==================== CENTROCAMPISTI ====================
    def _calculate_midfielder_price(self, player_row):
        """Algoritmo analitico per CENTROCAMPISTI"""
        score = 0.0
        nome = player_row.get('Nome', '').replace(' *', '').strip()
        squadra = player_row.get('Squadra', '')

        context = self._get_tactical_context(player_row)
        team_strength = self._get_team_strength(squadra)

        # FM dominante
        fm = self._get_stat_value(player_row, 'Fm')
        score += (fm - 6.0) * 5.5

        # Gol e Assist (peso variabile)
        gf = self._get_stat_value(player_row, 'Gf')
        ass = self._get_stat_value(player_row, 'Ass')

        if context['is_esterno_offensivo']:
            score += gf * 1.0
            score += ass * 0.9
        elif context['is_mediano']:
            score += gf * 0.6
            score += ass * 0.5
        else:
            score += gf * 0.85
            score += ass * 0.75

        # Recuperi (valgono di più in squadre forti)
        rc = self._get_stat_value(player_row, 'Rc')
        peso_recuperi = 0.15 + (team_strength * 0.1)
        score += rc * peso_recuperi

        # Presenze
        pv = self._get_stat_value(player_row, 'Pv')
        score += (pv / 38) * 2.0

        # Rigori
        rigorista_peso = self.rigoristi_map.get(nome, 0)
        if rigorista_peso == 0:
            rigorista_peso = self.rigoristi_map.get(nome + ' *', 0)
        score += rigorista_peso * 1.8

        # Penalità cartellini
        amm = self._get_stat_value(player_row, 'Amm')
        esp = self._get_stat_value(player_row, 'Esp')
        score -= (amm * 0.05 + esp * 0.35)

        return max(0, score)

    # ==================== DIFENSORI ====================
    def _calculate_defender_price(self, player_row):
        """Algoritmo analitico per DIFENSORI"""
        score = 0.0
        squadra = player_row.get('Squadra', '')

        context = self._get_tactical_context(player_row)

        # FM
        fm = self._get_stat_value(player_row, 'Fm')
        score += (fm - 6.0) * 6.0

        # Presenze (peso altissimo)
        pv = self._get_stat_value(player_row, 'Pv')
        score += (pv / 38) * 3.8

        # Forza difensiva squadra
        if squadra in self.team_stats:
            forza_dif = self.team_stats[squadra].get('forza_difensiva', 0)
            bonus_difesa = max(0, forza_dif / 10)
            score += bonus_difesa

        # Contributo offensivo
        gf = self._get_stat_value(player_row, 'Gf')
        ass = self._get_stat_value(player_row, 'Ass')

        if context['is_esterno_offensivo']:
            if context.get('difesa_a_tre', False):
                score += gf * 1.1
                score += ass * 1.0
            else:
                score += gf * 0.9
                score += ass * 0.8
        else:
            score += gf * 0.5
            score += ass * 0.4

        # Penalità cartellini
        amm = self._get_stat_value(player_row, 'Amm')
        esp = self._get_stat_value(player_row, 'Esp')
        score -= (amm * 0.08 + esp * 0.5)

        return max(0, score)

    # ==================== PORTIERI ====================
    def _calculate_goalkeeper_price(self, player_row):
        """Algoritmo analitico per PORTIERI"""
        score = 0.0
        nome = player_row.get('Nome', '').replace(' *', '').strip()
        squadra = player_row.get('Squadra', '')

        team_strength = self._get_team_strength(squadra)

        # FM dominante
        fm = self._get_stat_value(player_row, 'Fm')
        score += (fm - 5.0) * 5.5

        # Clean sheets (valgono DI PIÙ in squadre deboli)
        clean_sheets = get_clean_sheets(nome)
        peso_cs = 0.5 - (team_strength * 0.15)
        score += clean_sheets * peso_cs

        # Presenze
        pv = self._get_stat_value(player_row, 'Pv')
        score += (pv / 38) * 2.3

        # Rigori parati
        rp = self._get_stat_value(player_row, 'Rp')
        score += rp * 0.55

        # Penalità gol subiti
        gs = self._get_stat_value(player_row, 'Gs')
        if pv > 0:
            gol_per_partita = gs / pv
            score -= gol_per_partita * 0.3

        return max(0, score)

    # ==================== CALCOLO PERCENTUALI ====================
    def _calculate_all_scores(self):
        """Calcola score per tutti i giocatori per ranking"""
        for _, row in self.players_df.iterrows():
            role_full = row.get('R', '')
            role = role_full.split('/')[0].split('(')[0].strip()  # Estrai ruolo base

            if role == 'A':
                score = self._calculate_striker_price(row)
                self.all_scores['A'].append(score)
            elif role == 'C':
                score = self._calculate_midfielder_price(row)
                self.all_scores['C'].append(score)
            elif role == 'D':
                score = self._calculate_defender_price(row)
                self.all_scores['D'].append(score)
            elif role == 'P':
                score = self._calculate_goalkeeper_price(row)
                self.all_scores['P'].append(score)

    def calculate_price_percentage(self, player_id, budget=500):
        """Calcola percentuale di budget usando algoritmo analitico"""
        player = self.players_df[self.players_df['Id'] == player_id]

        if player.empty:
            return {
                'percentage': 0,
                'credits': 0,
                'budget': budget,
                'breakdown': {}
            }

        player_row = player.iloc[0]
        ruolo_full = player_row.get('R', '')
        ruolo = ruolo_full.split('/')[0].split('(')[0].strip()  # Estrai ruolo base

        # Calcola score
        if ruolo == 'P':
            player_score = self._calculate_goalkeeper_price(player_row)
            max_percentage = 11.0
            exponent = 1.22
            role_key = 'P'
        elif ruolo == 'D':
            player_score = self._calculate_defender_price(player_row)
            max_percentage = 15.0
            exponent = 1.12
            role_key = 'D'
        elif ruolo == 'C':
            player_score = self._calculate_midfielder_price(player_row)
            max_percentage = 17.0
            exponent = 1.45
            role_key = 'C'
        elif ruolo == 'A':
            player_score = self._calculate_striker_price(player_row)
            max_percentage = 30.0
            exponent = 1.35
            role_key = 'A'
        else:
            # Fallback
            percentage = 5.0
            credits = int(round((percentage / 100) * budget))
            return {
                'percentage': percentage,
                'credits': credits,
                'budget': budget,
                'breakdown': {}
            }

        # Normalizza e applica trasformazione
        all_scores_role = self.all_scores.get(role_key, [])
        if not all_scores_role:
            max_score = 1.0
        else:
            max_score = max(all_scores_role) if max(all_scores_role) > 0 else 1.0

        normalized = player_score / max_score if max_score > 0 else 0
        adjusted = normalized ** exponent
        percentage = adjusted * max_percentage

        percentage = round(max(0.0, min(max_percentage, percentage)), 1)
        credits = int(round((percentage / 100) * budget))

        return {
            'percentage': percentage,
            'credits': credits,
            'budget': budget,
            'breakdown': {
                'score': player_score,
                'max_score': max_score,
                'normalized': normalized
            }
        }
