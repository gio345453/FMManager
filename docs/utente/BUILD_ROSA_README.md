# 🏗️ Build Rosa - Documentazione

## Panoramica
La funzionalità **Build Rosa** è stata aggiunta all'applicazione FantaCalcio Manager per aiutare l'utente a costruire una rosa personalizzata partendo da giocatori selezionati manualmente o tramite generazione automatica.

## Accesso alla Funzionalità
Nella schermata principale dell'applicazione, è stato aggiunto un nuovo bottone **viola** chiamato "🏗️ Build Rosa" posizionato tra:
- ⚖️ Confronta Giocatori
- 📊 Dashboard Squadre

## Caratteristiche Principali

### 1. Composizione Rosa Personalizzabile
L'utente può configurare la composizione della rosa tramite menu a tendina per ogni reparto:
- **Portieri (P)**: da 1 a 4 giocatori (default: 3)
- **Difensori (D)**: da 6 a 10 giocatori (default: 8)
- **Centrocampisti (C)**: da 6 a 10 giocatori (default: 8)
- **Attaccanti (A)**: da 4 a 8 giocatori (default: 6)

La lista dei giocatori si adatta dinamicamente in base alla composizione selezionata.

### 2. Selezione Manuale Giocatori
Per ogni posizione nella rosa, l'utente può:
- Selezionare un giocatore tramite menu a tendina
- Le informazioni visualizzate per ogni giocatore sono:
  - **Nome**: Nome completo del giocatore
  - **R**: Ruolo (es. P, D, Dc, C, A, Pc, ecc.)
  - **Squadra**: Squadra di appartenenza
  - **Overall**: Punteggio Overall del giocatore
  - **Prezzo Max**: Prezzo massimo in base al budget
- Rimuovere un giocatore selezionato tramite bottone 🗑️
- Le righe con giocatori selezionati vengono evidenziate visivamente

### 3. Statistiche Real-time
In alto nella finestra vengono mostrate due statistiche che si aggiornano automaticamente:
- **💰 % Prezzo Max Totale**: Somma delle percentuali di prezzo max di tutti i giocatori selezionati
  - Verde se ≤ 100%
  - Giallo/Arancione se > 100%
- **⭐ Overall Medio**: Media dell'Overall di tutti i giocatori selezionati

### 4. Generazione Automatica Rosa
L'utente può completare automaticamente gli slot vuoti tramite il bottone "✨ Genera Rosa".

#### Filtri Disponibili:
- **💰 Range Prezzo Max**: Definisce il budget target
  - 80%-90%
  - 90%-100%
  - 100%-110%
  - 110%-120%
  - 120%-130%
  - 130%-140%
  
  ⚠️ **Nota**: Selezionando oltre il 100% l'utente dovrà rinunciare a qualche giocatore o cercare di ottenerli a prezzi minori all'asta.

- **📊 Valore Prioritario**: Definisce quale statistica privilegiare nella selezione
  - **FM** (Fantamedia)
  - **MV** (Media Voto)
  - **PV** (Punti Valore)

#### Algoritmo di Generazione:
1. **Rispetta le scelte dell'utente**: I giocatori già selezionati NON vengono rimossi o sostituiti
2. **Criterio di riempimento**:
   - 60% peso al valore scelto dall'utente (FM, MV o PV)
   - 20% peso a ciascuno degli altri due valori
3. **Vincoli**:
   - Non sfora la % prezzo max selezionata
   - Massimo 2 giocatori per reparto con prezzo max dell'1%
   - Rosa competitiva e bilanciata
4. **Selezione intelligente**: Cerca i migliori giocatori disponibili che rispettano i vincoli di budget

### 5. Evidenziazione Giocatori Generati
I giocatori aggiunti dall'algoritmo vengono evidenziati con sfondo **verde** per distinguerli da quelli selezionati manualmente.

## Struttura File Creati/Modificati

### File Creati:
- `src/ui/build_rosa_window.py`: Nuova finestra con tutta la logica per la costruzione della rosa

### File Modificati:
- `src/ui/components/footer_actions.py`: Aggiunto parametro `on_build_rosa` per gestire il bottone
- `src/ui/app_modern.py`: 
  - Importato `BuildRosaWindow`
  - Aggiunto metodo `open_build_rosa()`
  - Collegato il bottone al metodo

## Flusso di Utilizzo

1. **Apri Build Rosa**: Clicca sul bottone viola "🏗️ Build Rosa" nella schermata principale
2. **Configura Composizione** (opzionale): Modifica il numero di giocatori per reparto
3. **Seleziona Giocatori** (opzionale): Scegli manualmente alcuni giocatori strategici
4. **Imposta Filtri**: Configura range prezzo e valore prioritario
5. **Genera Rosa**: Clicca su "✨ Genera Rosa" per completare automaticamente
6. **Modifica**: Rimuovi e sostituisci giocatori secondo necessità
7. **Monitora Statistiche**: Controlla % prezzo max e overall medio in tempo reale

## Tecnologie Utilizzate
- **CustomTkinter**: Framework UI moderno per Python
- **Pandas**: Gestione e analisi dati giocatori
- **PriceCalculator**: Calcolo prezzi basato su statistiche e budget

## Note Tecniche
- La finestra è responsive e scrollabile per gestire rose di qualsiasi dimensione
- I dati vengono aggiornati in tempo reale ad ogni modifica
- L'algoritmo di generazione ottimizza per performance e correttezza
- Separatori visivi tra i reparti migliorano la leggibilità
