@echo off
echo ========================================
echo   FantaCalcio Manager - Avvio App Web
echo ========================================
echo.

echo [1/2] Avvio Backend FastAPI...
cd /d "%~dp0.."
start "Backend FastAPI" cmd /k "python web\backend\startup.py"
timeout /t 3 /nobreak >nul

echo [2/2] Avvio Frontend React...
cd web\frontend
start "Frontend React" cmd /k "npm run dev"

echo.
echo ========================================
echo   App avviata con successo!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo.
echo Premi un tasto per chiudere questo prompt...
echo (I server rimarranno attivi nelle finestre separate)
pause >nul
