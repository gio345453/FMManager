import os
import json
import re
import requests
from bs4 import BeautifulSoup

def scrape_probabili_formazioni():
    url = "https://www.fantacalcio.it/probabili-formazioni-serie-a"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
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

    # 1. Selezioniamo solo le card delle partite principali
    match_cards = soup.find_all("div", class_=lambda c: c and "match-card" in c)
    if not match_cards:
        # Fallback se le classi cambiano leggermente
        match_cards = soup.select(".card-match, .match, article")

    for card in match_cards:
        # Ignoriamo banner pubblicitari o blocchi sconosciuti
        teams_in_card = card.find_all("div", class_=lambda c: c and "team" in c and "name" not in c)
        if not teams_in_card:
            teams_in_card = [card]

        for team_box in teams_in_card:
            # Estrazione del nome della squadra
            header = team_box.find(["h2", "h3", "div", "span"], class_=lambda c: c and ("team-name" in c or "name" in c))
            if not header:
                continue

            raw_name = header.get_text(strip=True)
            # Rimuoviamo eventuali moduli tattici (es. 3-5-2) o stringhe brevi errate
            nome_squadra = re.sub(r'\d-\d(-\d)?(-\d)?', '', raw_name).strip()

            # Filtriamo via il menu in alto con i trilettera ('INT', 'MON', 'UDI', ecc.)
            if len(nome_squadra) <= 3 or "PROBABILI" in nome_squadra.upper():
                continue

            # Evitiamo di duplicare la stessa squadra
            if any(s["squadra"].lower() == nome_squadra.lower() for s in dati_squadre):
                continue

            giocatori = []

            # 2. Estrazione Titolari e Panchina
            # Fantacalcio raggruppa le sezioni con apposite classi o liste
            player_items = team_box.find_all(["li", "div"], class_=lambda c: c and ("player" in c or "item" in c or "titolar" in c))

            for item in player_items:
                # Estrazione del Nome Giocatore
                name_elem = item.find(["span", "a", "div", "p"], class_=lambda c: c and ("name" in c or "player" in c))
                if not name_elem:
                    # Se non c'è una classe specifica, prendiamo il link o il primo span libero
                    name_elem = item.find("a") or item.find("span")

                if not name_elem:
                    continue

                nome_giocatore = name_elem.get_text(strip=True)

                # Pulizia del nome da eventuali rumori di testo
                nome_giocatore = re.sub(r'\d+%', '', nome_giocatore).strip()
                if not nome_giocatore or len(nome_giocatore) < 3 or nome_giocatore.lower() in [nome_squadra.lower(), "panchina", "squalificati", "infortunati"]:
                    continue

                # Estrazione della Percentuale (cerca in text, data attribute o tag dedicati)
                percentuale = "N/D"
                
                # Cerca in attributi data-percent / data-value
                if item.has_attr("data-percent"):
                    percentuale = f"{item['data-percent']}%"
                else:
                    perc_elem = item.find(["span", "div", "small"], class_=lambda c: c and ("percent" in c or "ballottaggio" in c or "badge" in c))
                    if perc_elem:
                        perc_text = perc_elem.get_text(strip=True)
                        match_p = re.search(r'\d{1,3}%?', perc_text)
                        if match_p:
                            val = match_p.group(0).replace("%", "")
                            percentuale = f"{val}%"
                    else:
                        # Fallback: cerca qualsiasi stringa col simbolo % nel blocco del giocatore
                        match_p = re.search(r'(\d{1,3})\s*%', item.get_text())
                        if match_p:
                            percentuale = f"{match_p.group(1)}%"

                # Determinazione dello Status
                # Di default se è tra i primi 11 o ha percentuale alta è titolare
                status = "Titolare"
                parent_text = item.parent.get_text().lower() if item.parent else ""
                
                if "panchina" in parent_text or "bench" in str(item.parent.get('class', [])):
                    status = "Panchina"
                elif percentuale != "N/D":
                    p_val = int(percentuale.replace("%", ""))
                    if p_val < 60:
                        status = "Panchina / Ballottaggio"

                if not any(g["nome"].lower() == nome_giocatore.lower() for g in giocatori):
                    giocatori.append({
                        "nome": nome_giocatore,
                        "percentuale_titolarita": percentuale,
                        "status": status
                    })

            # 3. Estrazione Squalificati / Infortunati
            for status_type in ["squalificati", "infortunati"]:
                sec = team_box.find("div", class_=lambda c: c and status_type in c)
                if sec:
                    for tag in sec.find_all(["a", "span", "p"]):
                        nome_extra = tag.get_text(strip=True)
                        if nome_extra and len(nome_extra) > 2 and nome_extra.lower() not in ["nessun calciatore", "nessun", nome_squadra.lower()]:
                            if not any(g["nome"].lower() == nome_extra.lower() for g in giocatori):
                                giocatori.append({
                                    "nome": nome_extra,
                                    "percentuale_titolarita": "0%",
                                    "status": status_type.capitalize()
                                })

            if giocatori:
                dati_squadre.append({
                    "squadra": nome_squadra,
                    "totale_giocatori": len(giocatori),
                    "giocatori": giocatori
                })

    # Salvataggio su file JSON nella cartella corrente (data/Titolarita/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "Titolarita.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dati_squadre, f, ensure_ascii=False, indent=4)

    print(f"Completato! Generate {len(dati_squadre)} squadre corrette in: {output_path}")

if __name__ == "__main__":
    scrape_probabili_formazioni()