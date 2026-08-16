import json
import os
import re
import requests
from bs4 import BeautifulSoup


def scarica_squadre_e_moduli():
    url = "https://www.fantacalcio.it/probabili-formazioni-serie-a"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore durante il recupero della pagina: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    risultati = []

    # Regex per riconoscere moduli calcistici tipo: 3-5-2, 4-2-3-1, 3-4-1-2, 4-3-3, ecc.
    regex_modulo = re.compile(r"\b\d-\d(?:-\d){1,2}\b")

    # Trova i blocchi contenitori delle partite / squadre
    match_cards = soup.select(".card, .match-card, [class*='match']")

    for card in match_cards:
        # Trova i singoli box di ciascuna squadra all'interno del match
        team_boxes = card.select(
            ".team-card, .team-box, .team, [class*='team-']"
        )
        if not team_boxes:
            team_boxes = [card]

        for team_box in team_boxes:
            # Trova l'intestazione col nome della squadra e il modulo
            header_elem = team_box.select_one(
                ".team-name, .name, h2, h3, .header"
            )
            if not header_elem:
                continue

            testo_completo = " ".join(header_elem.get_text().split())

            # Cerca il modulo usando la Regex
            match_mod = regex_modulo.search(testo_completo)

            if match_mod:
                modulo = match_mod.group(0)
                # Pulisce il nome della squadra rimuovendo il modulo dal testo
                nome_squadra = re.sub(
                    regex_modulo, "", testo_completo
                ).strip()
            else:
                # Se il modulo non è nel titolo principale, cerca in elementi figli o vicini
                sub_mod_elem = team_box.find(string=regex_modulo)
                if sub_mod_elem:
                    modulo = regex_modulo.search(sub_mod_elem).group(0)
                    nome_squadra = testo_completo.strip()
                else:
                    continue

            # Filtro sicurezza: ignora abbreviazioni del menu o diciture non valide
            if len(nome_squadra) <= 3 or "PROBABILI" in nome_squadra.upper():
                continue

            # Evita duplicati
            if not any(
                item["squadra"].lower() == nome_squadra.lower()
                for item in risultati
            ):
                risultati.append({"squadra": nome_squadra, "modulo": modulo})

    # Salvataggio nel file modulo.json
    percorso_output = os.path.join(os.getcwd(), "modulo.json")

    with open(percorso_output, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, indent=4)

    print(
        f"Scraping completato con successo! Salvate {len(risultati)} squadre in '{percorso_output}'"
    )


if __name__ == "__main__":
    scarica_squadre_e_moduli()