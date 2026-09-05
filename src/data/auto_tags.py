"""
Gestione automatica dei tag per rigoristi e tiratori di piazzati
"""
import json
import os
from pathlib import Path
from typing import Dict, List
from src.data.player_notes import PlayerNotesManager


class AutoTagsManager:
    """Gestisce l'assegnazione automatica dei tag per rigoristi e tiratori"""

    def __init__(self):
        # Path assoluto dalla root del progetto
        _ROOT_DIR = Path(__file__).parent.parent.parent
        self.tiratori_file = _ROOT_DIR / 'data' / 'Tiratori' / 'tiratori.json'
        self.titolarita_file = _ROOT_DIR / 'data' / 'Titolarita' / 'Titolarita.json'
        self.player_notes = PlayerNotesManager()

    def load_tiratori_data(self) -> List[Dict]:
        """Carica i dati dei tiratori dal file JSON"""
        if not self.tiratori_file.exists():
            print(f"File {self.tiratori_file} non trovato")
            return []

        try:
            with open(self.tiratori_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento dei tiratori: {e}")
            return []

    def load_titolarita_data(self) -> List[Dict]:
        """Carica i dati della titolarità dal file JSON"""
        if not self.titolarita_file.exists():
            print(f"File {self.titolarita_file} non trovato")
            return []

        try:
            with open(self.titolarita_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento della titolarità: {e}")
            return []

    def find_player_id_by_name(self, player_name: str, players_df) -> int:
        """
        Trova l'ID di un giocatore dal nome

        Args:
            player_name: Nome del giocatore da cercare
            players_df: DataFrame con tutti i giocatori

        Returns:
            ID del giocatore o None se non trovato
        """
        if not player_name:
            return None

        # Cerca corrispondenza esatta
        match = players_df[players_df['Nome'] == player_name]

        if not match.empty:
            return int(match.iloc[0]['Id'])

        # Prova con asterisco (molti giocatori nel DB hanno " *")
        match = players_df[players_df['Nome'] == player_name + ' *']
        if not match.empty:
            return int(match.iloc[0]['Id'])

        # Se non trovato, cerca corrispondenza parziale (case insensitive)
        match = players_df[players_df['Nome'].str.lower() == player_name.lower()]
        if not match.empty:
            return int(match.iloc[0]['Id'])

        # Prova case insensitive con asterisco
        match = players_df[players_df['Nome'].str.lower() == (player_name + ' *').lower()]
        if not match.empty:
            return int(match.iloc[0]['Id'])

        return None

    def assign_auto_tags(self, players_df):
        """
        Assegna automaticamente i tag ai primi rigoristi e tiratori di piazzati

        Args:
            players_df: DataFrame con tutti i giocatori
        """
        tiratori_data = self.load_tiratori_data()

        if not tiratori_data:
            print("Nessun dato tiratori disponibile")
            return

        tags_assigned = {
            'rigorista': 0,
            'tiratore piazzati': 0
        }

        for team_data in tiratori_data:
            team_name = team_data.get('squadra', '')
            rigoristi = team_data.get('rigoristi', {})
            piazzati = team_data.get('piazzati_e_angoli', {})

            # Assegna tag al primo rigorista
            first_rigorista = rigoristi.get('1_rigorista')
            if first_rigorista:
                player_id = self.find_player_id_by_name(first_rigorista, players_df)
                if player_id:
                    self.player_notes.add_tag(player_id, 'rigorista')
                    tags_assigned['rigorista'] += 1
                    print(f"Tag 'rigorista' assegnato a {first_rigorista} ({team_name})")

            # Assegna tag al primo tiratore piazzati
            first_tiratore = piazzati.get('1_tiratore')
            if first_tiratore:
                player_id = self.find_player_id_by_name(first_tiratore, players_df)
                if player_id:
                    self.player_notes.add_tag(player_id, 'tiratore piazzati')
                    tags_assigned['tiratore piazzati'] += 1
                    print(f"Tag 'tiratore piazzati' assegnato a {first_tiratore} ({team_name})")

        print(f"\nTag automatici assegnati:")
        print(f"   - Rigoristi: {tags_assigned['rigorista']}")
        print(f"   - Tiratori piazzati: {tags_assigned['tiratore piazzati']}")

    def assign_all_auto_data(self, players_df):
        """
        Assegna tutti i dati automatici: solo tag (titolarità rimane nella sua colonna)

        Args:
            players_df: DataFrame con tutti i giocatori
        """
        print("\nAssegnazione dati automatici in corso...")
        self.assign_auto_tags(players_df)
        print("\nTutti i dati automatici sono stati assegnati!")


    def remove_auto_tags(self):
        """Rimuove tutti i tag automatici (rigorista e tiratore piazzati)"""
        count_removed = 0

        for player_id in list(self.player_notes.notes_data.keys()):
            tags = self.player_notes.get_tags(player_id)

            if 'rigorista' in tags:
                self.player_notes.remove_tag(player_id, 'rigorista')
                count_removed += 1

            if 'tiratore piazzati' in tags:
                self.player_notes.remove_tag(player_id, 'tiratore piazzati')
                count_removed += 1

        print(f"Rimossi {count_removed} tag automatici")
