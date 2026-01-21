@echo off
title AI Tester - Stopping Servers
echo ============================================
echo    AI Tester Framework - Stopping Servers
echo ============================================
echo.

echo Stopping Python processes (backend)...
taskkill /F /IM python.exe 2>nul
if %errorlevel%==0 (
    echo    Backend stopped.
) else (
    echo    No backend process found.
)

echo.
echo Stopping Node processes (frontend)...
taskkill /F /IM node.exe 2>nul
if %errorlevel%==0 (
    echo    Frontend stopped.
) else (
    echo    No frontend process found.
)

echo.
echo ============================================
echo    All servers stopped.
echo ============================================
echo.
pause
