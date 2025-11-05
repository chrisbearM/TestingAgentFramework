@echo off
echo ========================================
echo   AI Tester Framework v3.0 - Web UI
echo ========================================
echo.
echo Starting backend and frontend servers...
echo.

REM Start backend server
echo [1/2] Starting FastAPI backend on port 8000...
start "AI Tester Backend" cmd /k "cd src\ai_tester\api && python -m uvicorn main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend server
echo [2/2] Starting React frontend on port 3000...
start "AI Tester Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Servers starting...
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend UI:  http://localhost:3000
echo.
echo Press any key to open the UI in your browser...
pause >nul

start http://localhost:3000

echo.
echo To stop servers, close both terminal windows.
echo.
