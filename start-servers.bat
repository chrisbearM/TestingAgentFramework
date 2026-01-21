@echo off
title AI Tester - Starting Servers
echo ============================================
echo    AI Tester Framework - Server Startup
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Backend API Server (port 8000)...
start "AI Tester Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate && python -m uvicorn src.ai_tester.api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend Dev Server (port 3000)...
start "AI Tester Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ============================================
echo    Servers Starting...
echo ============================================
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo.
echo    (This window will close in 5 seconds)
echo    (Server windows will remain open)
echo ============================================

timeout /t 5 /nobreak > nul
