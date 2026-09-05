# FMManager

FMManager è un'applicazione web per la gestione del Fantacalcio, con frontend React/Vite e backend FastAPI.

L'app viene eseguita localmente sul PC e può essere utilizzata anche da altri dispositivi sulla stessa rete oppure da remoto tramite Tailscale.

## Requisiti

- Windows 10/11
- Python 3.10+
- Node.js + npm
- Connessione Internet per gli aggiornamenti automatici dei dati quando richiesti dal progetto

Le dipendenze Python del progetto web sono definite in `requirements-web.txt` e includono, tra le altre, pandas, matplotlib, FastAPI, Uvicorn, Pydantic, python-multipart, google-genai e python-dotenv.

## 1. Installazione iniziale

Aprire un terminale nella cartella principale del progetto:

```text
App\
```

Installare le dipendenze Python:

```bash
pip install -r requirements-web.txt
```

Installare le dipendenze frontend:

```bash
cd web/frontend
npm install
```

Poi tornare alla root:

```bash
cd ../..
```


Configuare apikey per aggiornamento automatico calendario
1) https://www.football-data.org/client/register
2) creare account
3) APIKEY arriva per mail
4) inserirla in APICALENDARIOLEGGEREREADME.example.txt contenuto in data\Calendario\
5) rinominare file in "API_KEY.txt"

## 2. Avvio dell'app

### Metodo consigliato: launcher Windows

Il progetto dispone del launcher:

```text
launchers/avvia_app.bat
```

Questo è il metodo consigliato per l'avvio quotidiano.

Il backend utilizza `web/backend/startup.py`. Lo startup esegue le operazioni iniziali necessarie prima di avviare il server, tra cui:

1. controllo/aggiornamento del calendario;
2. aggiornamento dei dati di titolarità e tiratori;
3. caricamento/calcolo dei dati dei giocatori;
4. assegnazione dei tag automatici.

## 3. Avvio manuale

Se è necessario avviare i componenti separatamente, usare due terminali.

### Backend

Dalla cartella principale:

```bash
python web/backend/startup.py
```

Il backend FastAPI usa la porta `8000` e ascolta su `0.0.0.0`.

La documentazione FastAPI è disponibile localmente su:

```text
http://localhost:8000/docs
```

### Frontend

In un secondo terminale:

```bash
cd web/frontend
npm run dev
```

Il frontend Vite usa la porta `3000`.

In locale:

```text
http://localhost:3000
```

## 4. Collegamento frontend/backend

Il frontend usa richieste relative del tipo:

```text
/api/...
```

Vite inoltra queste richieste al backend FastAPI:

```text
Frontend
http://<host>:3000
       |
       | /api
       v
Backend
http://127.0.0.1:8000
```

Questa configurazione permette di usare la stessa app dal PC, dalla LAN e tramite Tailscale.

## 5. Utilizzo da telefono sulla stessa Wi-Fi

PC e telefono devono essere collegati alla stessa rete.

Quando il frontend è avviato, Vite mostra un indirizzo simile a:

```text
Network: http://192.168.1.100:3000/
```

Dal telefono aprire:

```text
http://192.168.1.100:3000
```

sostituendo l'indirizzo di esempio con quello mostrato da Vite.

Il PC deve rimanere acceso e frontend/backend devono essere avviati.

Windows Firewall potrebbe richiedere di consentire l'accesso alla rete.

## 6. Utilizzo da fuori casa con Tailscale

FMManager può essere utilizzato anche quando il telefono non è sulla Wi-Fi di casa.

Configurazione:

1. installare Tailscale sul PC;
2. accedere con il proprio account;
3. installare Tailscale sul telefono;
4. accedere con lo stesso account;
5. verificare che entrambi i dispositivi risultino connessi.

Sul PC:

```text
Avviare FMManager normalmente
```

Sul telefono:

```text
Aprire Tailscale
→ verificare che sia connesso
→ aprire il browser
```

Usare l'indirizzo Tailscale del PC:

```text
http://100.x.x.x:3000
```

dove `100.x.x.x` è l'IP Tailscale del PC.

Per questo metodo il PC deve rimanere acceso, FMManager deve essere avviato e Tailscale deve essere connesso su entrambi i dispositivi.

Non è necessario aprire porte sul router.

## 7. Struttura principale

```text
App/
├── launchers/
│   └── avvia_app.bat
│
├── web/
│   ├── backend/
│   │   ├── main.py
│   │   └── startup.py
│   │
│   └── frontend/
│       ├── src/
│       ├── vite.config.js
│       └── package.json
│
├── requirements-web.txt
└── ...
```

## 8. Configurazione Vite per rete locale

Il frontend utilizza:

```text
host: 0.0.0.0
port: 3000
```

e un proxy API verso:

```text
http://127.0.0.1:8000
```

Schema:

```text
LAN / Tailscale
      |
      v
Frontend Vite :3000
      |
      | /api
      v
Backend FastAPI :8000
```

## 9. Aggiornamento del progetto

Dopo aver scaricato una nuova versione:

```bash
git pull
```

Se cambiano le dipendenze frontend:

```bash
cd web/frontend
npm install
```

Se cambiano le dipendenze Python:

```bash
cd ../..
pip install -r requirements-web.txt
```

Poi riavviare FMManager.

## 10. Problemi comuni

### Il frontend non si apre

Controllare che Vite sia avviato:

```bash
cd web/frontend
npm run dev
```

Verificare la porta `3000`.

### Il frontend si apre ma i dati non vengono caricati

Controllare che il backend sia avviato:

```bash
python web/backend/startup.py
```

Verificare:

```text
http://localhost:8000/docs
```

### Funziona sul PC ma non sul telefono

Controllare:

- telefono e PC sulla stessa rete;
- Vite configurato su `0.0.0.0`;
- Windows Firewall;
- uso dell'indirizzo `Network` mostrato da Vite.

### Funziona in Wi-Fi ma non fuori casa

Controllare:

- Tailscale connesso sul PC;
- Tailscale connesso sul telefono;
- PC acceso;
- FMManager avviato;
- uso dell'IP Tailscale `100.x.x.x`.

## 11. Flusso rapido per l'uso quotidiano

### A casa

```text
1. Avviare FMManager
2. Controllare l'indirizzo Network di Vite
3. Aprire l'indirizzo dal telefono
```

### Fuori casa

```text
1. Avviare FMManager sul PC di casa
2. Lasciare il PC acceso
3. Aprire Tailscale sul telefono
4. Verificare "Connected"
5. Aprire http://100.x.x.x:3000
```

## Stato della configurazione

La configurazione attuale è predisposta per:

- utilizzo locale su PC;
- accesso da smartphone sulla LAN;
- accesso remoto tramite Tailscale;
- frontend React/Vite;
- backend FastAPI;
- proxy `/api` tra frontend e backend.
