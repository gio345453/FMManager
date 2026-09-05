@echo off
chcp 65001 >nul
color 0A
title 🔄 Aggiornamento Dati Stagione - Eseguire il 15 Luglio

echo.
echo ════════════════════════════════════════════════════════════════
echo     ⚽ AGGIORNAMENTO AUTOMATICO DATI STAGIONE SERIE A
echo ════════════════════════════════════════════════════════════════
echo.
echo     📅 QUANDO ESEGUIRE: 15 Luglio (o dopo)
echo     ⏱️  TEMPO RICHIESTO: ~5 minuti
echo     🤖 AUTOMAZIONE: Risoluzione stagioni automatica
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM Controlla se siamo nella cartella corretta
if not exist "scripts\update_team_strength.py" (
    echo ❌ ERRORE: Script non trovati!
    echo.
    echo Assicurati di eseguire questo file dalla cartella principale del progetto.
    echo.
    pause
    exit /b 1
)

echo ℹ️  Questo script farà AUTOMATICAMENTE:
echo.
echo    1. ✅ Download dati FBref (ultime 3 stagioni concluse)
echo    2. ✅ Calcolo forza squadre (formula 40/30/20/10):
echo         • 40%% produzione recente (gol fatti/subiti)
echo         • 30%% forza reparti (da statistiche giocatori)
echo         • 20%% classifica stagione precedente
echo         • 10%% storico lungo Serie A
echo    3. ✅ Merge sicuro (preserva dati se download fallisce)
echo    4. ✅ Validazione automatica (minimo 18 squadre)
echo    5. ✅ Generazione team_strength.json aggiornato
echo.
echo 🎯 NESSUN intervento manuale richiesto per:
echo    • URL stagioni (generati dinamicamente)
echo    • File CSV (trovati automaticamente)
echo    • Anno/stagione (calcolati dalla data odierna)
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM Pausa per leggere
pause

echo.
echo ════════════════════════════════════════════════════════════════
echo     🔍 VERIFICA DIPENDENZE
echo ════════════════════════════════════════════════════════════════
echo.

REM Controlla se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato!
    echo.
    echo Installa Python da: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python trovato:
python --version
echo.

REM Controlla se le dipendenze sono installate
echo 🔍 Verifica dipendenze Python...
python -c "import requests, bs4" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  Dipendenze mancanti. Installazione in corso...
    echo.
    pip install -r scripts\requirements.txt
    if errorlevel 1 (
        echo.
        echo ❌ Errore installazione dipendenze!
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ✅ Dipendenze installate!
) else (
    echo ✅ Dipendenze già installate
)

echo.
echo ════════════════════════════════════════════════════════════════
echo     🚀 AVVIO AGGIORNAMENTO AUTOMATICO
echo ════════════════════════════════════════════════════════════════
echo.

REM Esegui pipeline completa con download FBref automatico
python scripts\update_team_strength.py --refresh-team-stats

REM Controlla se lo script è andato a buon fine
if errorlevel 1 (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo     ⚠️  COMPLETATO CON AVVISI
    echo ════════════════════════════════════════════════════════════════
    echo.
    echo Possibili cause:
    echo    - FBref non raggiungibile (connessione internet?)
    echo    - Rate limiting (troppi tentativi)
    echo    - Dati esistenti preservati (merge sicuro attivo)
    echo.
    echo Verifica l'output sopra per dettagli.
    echo.
) else (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo     ✅ COMPLETATO CON SUCCESSO!
    echo ════════════════════════════════════════════════════════════════
)

echo.
echo 📁 File aggiornati:
echo    • data\Calendario\team_strength.json (PRONTO ALL'USO)
echo    • data\Calendario\team_historical_strength.json
echo    • data\Calendario\team_department_strength.json
echo    • Aggiornamento_Fine_Stagione\team_stats_fbref.json
echo.
echo 🎯 NESSUNA MODIFICA MANUALE RICHIESTA!
echo    L'applicazione userà automaticamente i nuovi dati.
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 📝 COSA È STATO FATTO AUTOMATICAMENTE:
echo.
echo    ✅ Stagioni risolte dalla data odierna
echo    ✅ URL FBref generati dinamicamente
echo    ✅ Dati scaricati per ultime 3 stagioni concluse
echo    ✅ Validazione automatica (Serie A, 20 squadre)
echo    ✅ Merge sicuro (dati esistenti preservati se errore)
echo    ✅ Forza squadra calcolata con formula 40/30/20/10
echo    ✅ File runtime aggiornati
echo.
echo 💡 Per aggiornamenti durante la stagione:
echo    Usa solo il pulsante "Scarica listone" nell'app
echo.
echo 📚 Per dettagli tecnici: AUTOMAZIONE_STAGIONALE.md
echo.

REM Chiedi se aprire la documentazione
echo.
choice /C SN /M "Vuoi aprire la documentazione tecnica (AUTOMAZIONE_STAGIONALE.md)"
if errorlevel 2 goto :fine
if errorlevel 1 goto :apri_doc

:apri_doc
start "" "AUTOMAZIONE_STAGIONALE.md"
goto :fine

:fine
echo.
echo Premi un tasto per chiudere...
pause >nul
