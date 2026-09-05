"""
Modulo per la gestione delle note delle squadre
"""
import json
import os


class TeamNotesManager:
    """Gestisce le note personalizzate per le squadre"""

    def __init__(self, notes_file='data/user_data/team_notes.json'):
        """
        Inizializza il manager delle note squadre

        Args:
            notes_file: Path del file JSON per le note
        """
        self.notes_file = notes_file
        self.notes = {}
        self._load_notes()

    def _load_notes(self):
        """Carica le note dal file JSON"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except Exception as e:
                print(f"Errore caricamento note squadre: {e}")
                self.notes = {}
        else:
            self.notes = {}

    def _save_notes(self):
        """Salva le note nel file JSON"""
        try:
            os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Errore salvataggio note squadre: {e}")

    def get_note(self, team_name):
        """
        Ottieni la nota per una squadra

        Args:
            team_name: Nome della squadra

        Returns:
            str: Nota della squadra (stringa vuota se non presente)
        """
        return self.notes.get(team_name, '')

    def set_note(self, team_name, note):
        """
        Imposta la nota per una squadra

        Args:
            team_name: Nome della squadra
            note: Testo della nota
        """
        self.notes[team_name] = note
        self._save_notes()

    def delete_note(self, team_name):
        """
        Elimina la nota per una squadra

        Args:
            team_name: Nome della squadra
        """
        if team_name in self.notes:
            del self.notes[team_name]
            self._save_notes()
