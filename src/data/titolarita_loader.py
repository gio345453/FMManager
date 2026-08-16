"""
Modulo condiviso per il caricamento dei dati di titolarità.
Centralizza la logica già usata in player_table.py per evitare duplicazioni
e permettere di mostrare la percentuale di titolarità anche in altre schermate
(confronto giocatori, dettaglio giocatore).
"""
import json
import os

_titolarita_cache = None

TITOLARITA_FILE = os.path.join('data', 'Titolarita', 'Titolarita.json')


def load_titolarita_map():
    """
    Carica (con cache in memoria) la mappa nome_giocatore -> percentuale_titolarita.
    Salva sia il nome esatto che la variante con asterisco (' *') per il matching
    con i nomi presenti nel database giocatori.
    """
    global _titolarita_cache
    if _titolarita_cache is not None:
        return _titolarita_cache

    titolarita_map = {}

    if not os.path.exists(TITOLARITA_FILE):
        _titolarita_cache = titolarita_map
        return titolarita_map

    try:
        with open(TITOLARITA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

            for team_data in data:
                for player in team_data.get('giocatori', []):
                    nome = player.get('nome', '').strip()
                    percentuale = player.get('percentuale_titolarita', '')
                    if nome and percentuale:
                        titolarita_map[nome] = percentuale
                        titolarita_map[nome + ' *'] = percentuale
    except Exception as e:
        print(f"Errore nel caricamento titolarità: {e}")

    _titolarita_cache = titolarita_map
    return titolarita_map


_status_cache = None


def load_status_map():
    """
    Carica (con cache in memoria) la mappa nome_giocatore -> status
    (es. 'Titolare', 'Panchina / Ballottaggio').
    Salva sia il nome esatto che la variante con asterisco (' *') per il matching
    con i nomi presenti nel database giocatori.
    """
    global _status_cache
    if _status_cache is not None:
        return _status_cache

    status_map = {}

    if not os.path.exists(TITOLARITA_FILE):
        _status_cache = status_map
        return status_map

    try:
        with open(TITOLARITA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

            for team_data in data:
                for player in team_data.get('giocatori', []):
                    nome = player.get('nome', '').strip()
                    status = player.get('status', '')
                    if nome and status:
                        status_map[nome] = status
                        status_map[nome + ' *'] = status
    except Exception as e:
        print(f"Errore nel caricamento status titolarità: {e}")

    _status_cache = status_map
    return status_map


def get_titolarita(player_name):
    """
    Restituisce la percentuale di titolarità per un giocatore (es. '85%')
    o '-' se non trovata.
    """
    if not player_name:
        return '-'
    titolarita_map = load_titolarita_map()
    return titolarita_map.get(player_name, '-')


def get_status(player_name):
    """
    Restituisce lo status di titolarità per un giocatore
    (es. 'Titolare', 'Panchina / Ballottaggio') o '-' se non trovato.
    """
    if not player_name:
        return '-'
    status_map = load_status_map()
    return status_map.get(player_name, '-')


def reset_cache():
    """Resetta la cache in memoria (da chiamare dopo un nuovo download dei dati)"""
    global _titolarita_cache, _status_cache
    _titolarita_cache = None
    _status_cache = None
