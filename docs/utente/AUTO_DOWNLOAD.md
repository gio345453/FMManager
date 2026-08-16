# Sistema di Aggiornamento Automatico

## 🚀 Cosa fa l'app all'avvio

Ogni volta che avvii l'applicazione FantaCalcio Manager, il sistema esegue automaticamente queste operazioni **prima** di mostrare l'interfaccia:

### 1. 📥 Download Dati Aggiornati
L'app scarica automaticamente da internet:
- **Rigoristi e tiratori di piazzati** di tutte le squadre
- **Probabili formazioni** con percentuali di titolarità

### 2. 🏷️ Assegnazione Tag Automatici
Ai giocatori vengono assegnati automaticamente questi tag:
- **rigorista** → Al primo rigorista di ogni squadra
- **tiratore piazzati** → Al primo tiratore di calci piazzati di ogni squadra

### 3. 📝 Assegnazione Note Titolarità
A tutti i giocatori viene aggiunta una nota con:
- Percentuale di titolarità (es. 95%, 50%, 0%)
- Status (Titolare, Panchina, Ballottaggio, Squalificato, Infortunato)

Esempio nota: `Titolarità: 95% (Titolare)`

## ⏱️ Controllo Intelligente

Per evitare di sovraccaricare i server e velocizzare l'avvio, il sistema:
- ✅ Scarica i dati **massimo 1 volta all'ora**
- ⏭️ Se hai già scaricato i dati meno di 1 ora fa, li riutilizza
- 🔄 Dopo 1 ora, al prossimo avvio scaricherà dati aggiornati

## 📊 Come Usare i Dati

### Tag
1. Nella tabella principale, guarda la colonna **"Tag"**
2. I giocatori con tag **rigorista** o **tiratore piazzati** sono evidenziati
3. Puoi filtrare i giocatori per tag usando il menu a tendina dei filtri

### Note Titolarità
1. **Doppio click** su un giocatore per aprire i dettagli
2. Nella sezione **Note** vedrai la percentuale di titolarità
3. Usa queste info per valutare quanto è probabile che giochi

## 🎯 Vantaggi

✨ **Completamente Automatico**
- Non devi fare nulla, l'app si aggiorna da sola

⚡ **Veloce**
- Dopo il primo download, l'avvio è istantaneo

📈 **Sempre Aggiornato**
- Dati freschi ogni ora se disponibili

🎨 **Interfaccia Pulita**
- Nessun pulsante da premere, tutto funziona in background

## 🛠️ Dettagli Tecnici

### File di Cache
L'app mantiene una cache in `data/last_download.json` che contiene:
- Data e ora dell'ultimo download tiratori
- Data e ora dell'ultimo download titolarità

### File Dati
I dati scaricati vengono salvati in:
- `data/Tiratori/Tiratori.json` - Rigoristi e tiratori piazzati
- `data/Titolarita/Titolarita.json` - Probabili formazioni e percentuali

### Comportamento in Caso di Errore
Se il download fallisce (es. nessuna connessione internet):
- ✅ L'app si avvia comunque normalmente
- 📂 Usa i dati scaricati precedentemente se disponibili
- 🔔 Mostra un messaggio nella console (non blocca l'utente)

## ❓ Domande Frequenti

**Q: Posso forzare un aggiornamento anche se non è passata 1 ora?**
A: Sì, cancella il file `data/last_download.json` e riavvia l'app.

**Q: Cosa succede se non ho connessione internet?**
A: L'app userà i dati scaricati precedentemente. Se è il primo avvio senza connessione, partirà senza tag automatici.

**Q: Posso disattivare questa funzionalità?**
A: Al momento no, ma se vuoi solo evitare i download frequenti, non riavviare l'app (tienila aperta).

**Q: I tag e le note vengono sovrascritti ogni volta?**
A: 
- **Tag**: Vengono aggiunti solo se non già presenti
- **Note titolarità**: Vengono aggiornate, ma le altre note personali vengono mantenute

**Q: Perché il pulsante "Assegna Tag Automatici" è stato rimosso?**
A: Non è più necessario! L'operazione avviene automaticamente all'avvio.

## 🔍 Verifica Funzionamento

Per verificare che il sistema funzioni correttamente:
1. Chiudi completamente l'app
2. Apri una console/terminale nella cartella dell'app
3. Esegui: `python test_auto_download.py`
4. Vedrai un report completo delle operazioni eseguite

## 📞 Supporto

Se riscontri problemi con il download automatico:
1. Verifica la connessione internet
2. Controlla la console per eventuali messaggi di errore
3. Prova a cancellare `data/last_download.json` e riavviare
