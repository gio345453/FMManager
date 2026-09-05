"""Gestione lista preferiti giocatori."""
import json
import os
import shutil
import tempfile


class FavoritesManager:
    """Manager per gestire la lista dei giocatori preferiti."""

    _reported_errors = set()

    def __init__(self, filepath="data/user_data/favorites.json"):
        self.filepath = filepath
        self.backup_filepath = f"{filepath}.bak"
        self.corrupt_filepath = f"{filepath}.corrupt"
        self.favorites = set()
        self._load()

    def _warn_once(self, category, message):
        key = (os.path.abspath(self.filepath), category)
        if key not in self._reported_errors:
            self._reported_errors.add(key)
            print(message)

    @staticmethod
    def _to_json_native(value):
        item = getattr(value, "item", None)
        if callable(item):
            value = item()
        return value

    @classmethod
    def _read_favorites(cls, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if not isinstance(data, dict) or not isinstance(data.get('favorites', []), list):
            raise ValueError("Formato preferiti non valido")

        return {cls._to_json_native(player_id) for player_id in data.get('favorites', [])}

    def _preserve_corrupt_file(self):
        if os.path.exists(self.corrupt_filepath):
            return

        try:
            shutil.copy2(self.filepath, self.corrupt_filepath)
        except OSError as error:
            self._warn_once(
                "corrupt-copy",
                f"Impossibile conservare il file preferiti danneggiato: {error}"
            )

    def _load(self):
        """Carica i preferiti dal file JSON o dall'ultimo backup valido."""
        if not os.path.exists(self.filepath):
            return

        try:
            self.favorites = self._read_favorites(self.filepath)
            return
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as error:
            self._preserve_corrupt_file()

            try:
                self.favorites = self._read_favorites(self.backup_filepath)
                self._warn_once(
                    "load-recovered",
                    "File preferiti non valido: ripristinati i preferiti dall'ultimo backup valido."
                )
                return
            except FileNotFoundError:
                backup_error = "backup non disponibile"
            except (json.JSONDecodeError, OSError, ValueError, TypeError) as backup_exception:
                backup_error = str(backup_exception)

            self.favorites = set()
            self._warn_once(
                "load-failed",
                f"Errore nel caricamento preferiti: {error}. Nessun backup utilizzabile ({backup_error})."
            )

    def _build_payload(self, favorites):
        player_ids = [self._to_json_native(player_id) for player_id in favorites]
        player_ids.sort(key=lambda player_id: (type(player_id).__name__, repr(player_id)))
        payload = {'favorites': player_ids}
        json.dumps(payload)
        return payload

    @staticmethod
    def _is_valid_favorites_file(filepath):
        try:
            FavoritesManager._read_favorites(filepath)
            return True
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError, TypeError):
            return False

    def _save(self, favorites):
        """Salva un set candidato senza modificare il file esistente finché non è valido."""
        try:
            payload = self._build_payload(favorites)
        except (TypeError, ValueError) as error:
            self._warn_once("save-serialization", f"Errore nel salvataggio preferiti: {error}")
            return False

        directory = os.path.dirname(os.path.abspath(self.filepath))
        temporary_path = None

        try:
            os.makedirs(directory, exist_ok=True)
            descriptor, temporary_path = tempfile.mkstemp(
                prefix="favorites-",
                suffix=".tmp",
                dir=directory,
                text=True
            )
            with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
                json.dump(payload, file, indent=2)
                file.flush()
                os.fsync(file.fileno())

            if os.path.exists(self.filepath) and self._is_valid_favorites_file(self.filepath):
                shutil.copy2(self.filepath, self.backup_filepath)

            os.replace(temporary_path, self.filepath)
            temporary_path = None
            return True
        except OSError as error:
            self._warn_once("save-io", f"Errore nel salvataggio preferiti: {error}")
            return False
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)

    def _commit(self, favorites):
        if not self._save(favorites):
            return False

        self.favorites = favorites
        return True

    def add_to_favorites(self, player_id):
        """Aggiunge un giocatore ai preferiti."""
        candidate = set(self.favorites)
        candidate.add(self._to_json_native(player_id))
        return self._commit(candidate)

    def remove_from_favorites(self, player_id):
        """Rimuove un giocatore dai preferiti."""
        candidate = set(self.favorites)
        candidate.discard(self._to_json_native(player_id))
        return self._commit(candidate)

    def toggle_favorite(self, player_id):
        """Toggle stato preferito di un giocatore."""
        player_id = self._to_json_native(player_id)
        candidate = set(self.favorites)

        if player_id in candidate:
            candidate.remove(player_id)
        else:
            candidate.add(player_id)

        self._commit(candidate)
        return player_id in self.favorites

    def is_favorite(self, player_id):
        """Verifica se un giocatore è nei preferiti."""
        return self._to_json_native(player_id) in self.favorites

    def get_all_favorites(self):
        """Ottiene la lista di tutti gli ID preferiti."""
        return list(self.favorites)

    def get_favorites_count(self):
        """Ottiene il numero di giocatori preferiti."""
        return len(self.favorites)

    def clear_all(self):
        """Rimuove tutti i preferiti."""
        return self._commit(set())
