import os
import json
import re
import requests
from bs4 import BeautifulSoup

def scrape_griglia_portieri():
    url = "https://www.fantacalcio.it/griglia-portieri"
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
    griglia_json = {}

    # METODO 1: Cerca la matrice nei dati dello script JS (window.__NUXT__ o oggetti dati)
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and ("griglia" in script.string.lower() or "matrix" in script.string.lower()):
            # Estraiamo l'oggetto JSON formattato se presente
            json_match = re.search(r'\{.*"Atalanta".*\}', script.string)
            if json_match:
                try:
                    griglia_json = json.loads(json_match.group(0))
                    break
                except json.JSONDecodeError:
                    pass

    # METODO 2: Parsing della tabella HTML strutturata
    if not griglia_json:
        table = soup.find("table")
        if table:
            headers_squadre = []
            
            # 1. Estrazione intestazioni (nomi delle squadre)
            header_cells = table.find_all(["th", "td"])
            for cell in header_cells:
                text = cell.get_text(strip=True)
                # Filtra diciture vuote o la cella d'angolo
                if text and len(text) > 2 and text.lower() not in ["squadra", "squadre", "griglia"]:
                    if text not in headers_squadre:
                        headers_squadre.append(text)

            # 2. Estrazione delle righe con incroci reali
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue

                # La prima cella è la squadra di riga
                squadra_riga = cells[0].get_text(strip=True)
                
                # Ignoriamo le righe d'intestazione o spurie
                if not squadra_riga or squadra_riga in ["Squadra", ""] or len(squadra_riga) <= 2:
                    continue

                incroci_squadra = {}
                data_cells = cells[1:]

                for idx, cell in enumerate(data_cells):
                    if idx < len(headers_squadre):
                        squadra_col = headers_squadre[idx]
                        raw_val = cell.get_text(strip=True)

                        # Cerchiamo cifre nell'HTML interno della cella (es. dentro span/div/attr)
                        match_num = re.search(r'\d+', raw_val)
                        if match_num:
                            val = int(match_num.group(0))
                        else:
                            # Controlla se la cella ha un attributo data-* con il valore
                            attr_val = cell.get('data-value') or cell.get('data-val')
                            val = int(attr_val) if attr_val and attr_val.isdigit() else 0

                        incroci_squadra[squadra_col] = val

                if incroci_squadra:
                    griglia_json[squadra_riga] = incroci_squadra

    if not griglia_json:
        print("❌ Impossibile estrarre la griglia portieri.")
        return

    # Salvataggio su file JSON nella stessa cartella del file
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    output_path = os.path.join(script_dir, "griglia_portieri.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(griglia_json, f, ensure_ascii=False, indent=4)

    print(f"✅ Completato! Griglia salvata con successo ({len(griglia_json)} squadre) in:\n{output_path}")

if __name__ == "__main__":
    scrape_griglia_portieri()