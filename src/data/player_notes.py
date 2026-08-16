"""
Gestione note personali e tag per i giocatori
Permette di salvare note, tag/etichette per ogni giocatore con persistenza su file JSON
"""
import json
import os
from typing import Dict, List, Optional


class PlayerNotesManager:
    """Gestisce note e tag personali per i giocatori con persistenza su file JSON"""

    _instance = None

    def __new__(cls):
        """Singleton pattern per avere una sola istanza del manager"""
        if cls._instance is None:
            cls._instance = super(PlayerNotesManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inizializza il manager e carica i dati dal file"""
        if self._initialized:
            return

        self._initialized = True
        self.data_file = os.path.join('data', 'player_notes.json')
        self.notes_data: Dict[int, Dict] = {}
        self._load_data()

    def _load_data(self):
        """Carica i dati dal file JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    # Carica e converte le chiavi da string a int
                    raw_data = json.load(f)
                    self.notes_data = {int(k): v for k, v in raw_data.items()}
            except Exception as e:
                print(f"Errore nel caricamento delle note: {e}")
                self.notes_data = {}
        else:
            self.notes_data = {}

    def _save_data(self):
        """Salva i dati nel file JSON"""
        try:
            # Crea la directory data se non esiste
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Errore nel salvataggio delle note: {e}")

    def get_note(self, player_id: int) -> str:
        """Restituisce la nota per un giocatore"""
        player_data = self.notes_data.get(player_id, {})
        return player_data.get('note', '')

    def set_note(self, player_id: int, note: str):
        """Imposta la nota per un giocatore"""
        if player_id not in self.notes_data:
            self.notes_data[player_id] = {}

        self.notes_data[player_id]['note'] = note.strip()
        self._save_data()

    def get_tags(self, player_id: int) -> List[str]:
        """Restituisce la lista di tag per un giocatore"""
        player_data = self.notes_data.get(player_id, {})
        return player_data.get('tags', [])

    def set_tags(self, player_id: int, tags: List[str]):
        """Imposta i tag per un giocatore"""
        if player_id not in self.notes_data:
            self.notes_data[player_id] = {}

        # Rimuovi duplicati e stringhe vuote
        cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
        self.notes_data[player_id]['tags'] = cleaned_tags
        self._save_data()

    def add_tag(self, player_id: int, tag: str):
        """Aggiunge un tag a un giocatore (se non esiste già)"""
        tags = self.get_tags(player_id)
        tag = tag.strip()

        if tag and tag not in tags:
            tags.append(tag)
            self.set_tags(player_id, tags)

    def remove_tag(self, player_id: int, tag: str):
        """Rimuove un tag da un giocatore"""
        tags = self.get_tags(player_id)
        if tag in tags:
            tags.remove(tag)
            self.set_tags(player_id, tags)

    def get_tags_string(self, player_id: int) -> str:
        """Restituisce i tag come stringa separata da virgole"""
        tags = self.get_tags(player_id)
        return ', '.join(tags) if tags else ''

    def get_note_preview(self, player_id: int, max_length: int = 50) -> str:
        """Restituisce un'anteprima della nota (troncata se troppo lunga)"""
        note = self.get_note(player_id)
        if not note:
            return ''

        if len(note) <= max_length:
            return note

        return note[:max_length-3] + '...'

    def has_data(self, player_id: int) -> bool:
        """Verifica se un giocatore ha note o tag"""
        return player_id in self.notes_data and (
            self.notes_data[player_id].get('note', '') or
            self.notes_data[player_id].get('tags', [])
        )

    def delete_player_data(self, player_id: int):
        """Elimina tutti i dati di un giocatore"""
        if player_id in self.notes_data:
            del self.notes_data[player_id]
            self._save_data()

    def get_all_tags(self) -> List[str]:
        """Restituisce tutti i tag utilizzati (senza duplicati)"""
        all_tags = set()
        for player_data in self.notes_data.values():
            tags = player_data.get('tags', [])
            all_tags.update(tags)
        return sorted(list(all_tags))

    def search_by_tag(self, tag: str) -> List[int]:
        """Restituisce l'elenco degli ID giocatori che hanno un certo tag"""
        player_ids = []
        for player_id, player_data in self.notes_data.items():
            tags = player_data.get('tags', [])
            if tag in tags:
                player_ids.append(player_id)
        return player_ids
