import os
import json
import requests
from bs4 import BeautifulSoup

def scrape_tiratori():
    url = "https://www.fantacalcio.it/rigoristi-serie-a"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore durante la richiesta HTTP: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    dati_squadre = []

    # Trova tutte le card delle squadre (con id="team-X")
    team_cards = soup.find_all('div', class_='team-card')

    print(f"Trovate {len(team_cards)} card di squadre\n")

    # Processa ogni card di squadra
    for card in team_cards:
        # Trova il nome della squadra
        team_elem = card.find('span', class_='team-name')
        if not team_elem:
            continue

        nome_squadra = team_elem.text.strip()

        # Trova le due sezioni (Rigori e Calci piazzati)
        sections = card.find_all('div', class_='col')

        rigoristi = []
        tiratori_piazzati = []

        for section in sections:
            header = section.find('header')
            if not header:
                continue

            section_name = header.text.strip().lower()

            # Trova i giocatori in questa sezione
            player_links = section.find_all('a', class_='player-link')

            players_in_section = []
            for link in player_links:
                span = link.find('span')
                if span:
                    nome_giocatore = span.text.strip()
                    if nome_giocatore:
                        players_in_section.append(nome_giocatore)

            # Determina se è la sezione rigoristi o tiratori
            if 'rigori' in section_name:
                rigoristi = players_in_section
            elif 'piazzati' in section_name or 'angolo' in section_name or 'calci' in section_name:
                tiratori_piazzati = players_in_section

        # Deve avere almeno 1 rigorista e 1 tiratore
        if len(rigoristi) >= 1 and len(tiratori_piazzati) >= 1:
            # Crea l'oggetto con i dati disponibili
            dati = {
                "squadra": nome_squadra,
                "rigoristi": {},
                "piazzati_e_angoli": {}
            }

            # Aggiungi rigoristi (fino a 3)
            for i, rig in enumerate(rigoristi[:3], 1):
                dati["rigoristi"][f"{i}_rigorista"] = rig

            # Aggiungi tiratori piazzati (fino a 3)
            for i, tir in enumerate(tiratori_piazzati[:3], 1):
                dati["piazzati_e_angoli"][f"{i}_tiratore"] = tir

            dati_squadre.append(dati)

            # Mostra cosa è stato estratto
            rig_str = ", ".join(rigoristi[:3])
            tir_str = ", ".join(tiratori_piazzati[:3])
            print(f"✓ {nome_squadra:15} → Rig: {rig_str:40} | Tir: {tir_str}")
        else:
            print(f"✗ {nome_squadra:15} → Rig: {len(rigoristi)}, Tir: {len(tiratori_piazzati)} - DATI INSUFFICIENTI")

    # Filtra solo squadre presenti nei dati dei giocatori
    # (invece di una lista hardcoded, usa le squadre reali dell'app)
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.data_processor import FantaCalcioDataProcessor

        processor = FantaCalcioDataProcessor()
        df = processor.calculate_weighted_stats()
        if df is not None:
            squadre_nel_db = df['Squadra'].unique().tolist()

            # Debug: mostra confronto
            print(f"\n🔍 Debug filtraggio:")
            print(f"   Squadre nel DB: {len(squadre_nel_db)}")
            print(f"   Squadre scraped: {len(dati_squadre)}")

            dati_squadre_filtrati = []
            for sq in dati_squadre:
                if sq['squadra'] in squadre_nel_db:
                    dati_squadre_filtrati.append(sq)
                else:
                    print(f"   ✗ '{sq['squadra']}' non trovata nel DB")

            print(f"   Squadre dopo filtro: {len(dati_squadre_filtrati)}")
        else:
            # Fallback: prendi tutte
            dati_squadre_filtrati = dati_squadre
            print(f"\n⚠️  Impossibile filtrare, salvate tutte le {len(dati_squadre)} squadre")
    except Exception as e:
        print(f"\n⚠️  Errore nel filtraggio: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: prendi tutte
        dati_squadre_filtrati = dati_squadre

    # Salvataggio su file JSON nella cartella corrente (data/Tiratori/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "tiratori.json")

    print(f"\n💾 Salvataggio...")
    print(f"   Dati da salvare: {len(dati_squadre_filtrati)} squadre")
    print(f"   Squadre: {[sq['squadra'] for sq in dati_squadre_filtrati]}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dati_squadre_filtrati, f, ensure_ascii=False, indent=4)

    # Verifica immediata dopo salvataggio
    with open(output_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    print(f"\n✅ Salvate {len(saved_data)} squadre (verifica post-salvataggio)")

    squadre_salvate = [sq['squadra'] for sq in saved_data]
    print(f"   File: {output_path}")
    print(f"   Squadre nel file: {', '.join(sorted(squadre_salvate))}")

    # Verifica se ci sono squadre nel DB senza dati tiratori
    if 'squadre_nel_db' in locals():
        squadre_mancanti = [sq for sq in squadre_nel_db if sq not in squadre_salvate]
        if squadre_mancanti:
            print(f"\n⚠️  Squadre nel DB ma NON salvate ({len(squadre_mancanti)}): {', '.join(sorted(squadre_mancanti))}")

if __name__ == "__main__":
    scrape_tiratori()
