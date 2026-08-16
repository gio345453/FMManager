@echo off
chcp 65001 >nul
color 0A
title 🔄 Aggiornamento Dati Stagione - Eseguire il 15 Luglio

echo.
echo ════════════════════════════════════════════════════════════════
echo     ⚽ AGGIORNAMENTO DATI STAGIONE SERIE A
echo ════════════════════════════════════════════════════════════════
echo.
echo     📅 QUANDO ESEGUIRE: 15 Luglio (o dopo)
echo     ⏱️  TEMPO RICHIESTO: ~5 minuti
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM Controlla se siamo nella cartella corretta
if not exist "scripts\update_season_data.py" (
    echo ❌ ERRORE: File update_season_data.py non trovato!
    echo.
    echo Assicurati di eseguire questo file dalla cartella principale del progetto.
    echo.
    pause
    exit /b 1
)

echo ℹ️  Questo script farà:
echo.
echo    1. ✅ Backup automatico dei file esistenti
echo    2. ✅ Download classifica Serie A da FBref
echo    3. ✅ Download clean sheets portieri da FBref
echo    4. ✅ Validazione automatica dei dati
echo    5. ✅ Generazione codice Python pronto all'uso
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
echo     🚀 AVVIO SCRIPT
echo ════════════════════════════════════════════════════════════════
echo.

REM Esegui lo script
python scripts\update_season_data.py

REM Controlla se lo script è andato a buon fine
if errorlevel 1 (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo     ❌ ERRORE DURANTE L'ESECUZIONE
    echo ════════════════════════════════════════════════════════════════
    echo.
    echo Possibili cause:
    echo    - FBref non raggiungibile (connessione internet?)
    echo    - Struttura HTML di FBref cambiata
    echo    - Rate limiting (troppi tentativi)
    echo.
    echo Soluzioni:
    echo    1. Controlla connessione internet
    echo    2. Riprova tra 5-10 minuti
    echo    3. Aggiorna manualmente (vedi SCALABILITY_GUIDE.md)
    echo.
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════════════
echo     ✅ COMPLETATO!
echo ════════════════════════════════════════════════════════════════
echo.
echo 📁 File generati in: scripts\output\
echo.
echo 📝 PROSSIMI PASSI:
echo.
echo    1. Apri la cartella: scripts\output\
echo.
echo    2. Copia il contenuto di:
echo       • team_stats_generated_*.py
echo         → src\data\team_stats.py (cerca CLASSIFICA_REALE_CURRENT_SEASON)
echo.
echo       • clean_sheets_generated_*.py
echo         → src\data\clean_sheets_data.py (cerca CLEAN_SHEETS_CURRENT_SEASON)
echo.
echo    3. Verifica i nomi delle squadre
echo.
echo    4. Testa l'applicazione:
echo       python main_modern.py
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 💡 Suggerimento: I file .backup sono stati creati automaticamente
echo    in caso di problemi.
echo.
echo 📚 Per dubbi consulta: SCALABILITY_GUIDE.md
echo.

REM Chiedi se aprire la cartella output
echo.
choice /C SN /M "Vuoi aprire la cartella output"
if errorlevel 2 goto :fine
if errorlevel 1 goto :apri_cartella

:apri_cartella
start "" "scripts\output"
goto :fine

:fine
echo.
echo Premi un tasto per chiudere...
pause >nul
