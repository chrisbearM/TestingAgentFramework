@echo off
REM Local Security Scanning Script for Windows
REM Run this before committing code to catch security issues early

echo ==================================
echo AI Tester Security Scan
echo ==================================
echo.

set FAILED=0

REM 1. Bandit - Python code security scanner
echo 1/5: Bandit (Python Code Security)
where bandit >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    bandit -r src/ -ll
    if %ERRORLEVEL% NEQ 0 set FAILED=1
) else (
    echo [WARNING] Bandit not installed. Install with: pip install bandit
)
echo.

REM 2. Safety - Python dependency vulnerability checker
echo 2/5: Safety (Python Dependencies)
where safety >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    safety check -r requirements.txt
    if %ERRORLEVEL% NEQ 0 set FAILED=1
) else (
    echo [WARNING] Safety not installed. Install with: pip install safety
)
echo.

REM 3. Snyk - Multi-language vulnerability scanner
echo 3/5: Snyk (Python Dependencies)
where snyk >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    snyk test --file=requirements.txt --severity-threshold=high
    if %ERRORLEVEL% NEQ 0 set FAILED=1
) else (
    echo [WARNING] Snyk not installed. Install with: npm install -g snyk
)
echo.

REM 4. NPM Audit - Frontend dependencies
echo 4/5: NPM Audit (Frontend Dependencies)
if exist frontend (
    cd frontend
    npm audit --audit-level=high
    if %ERRORLEVEL% NEQ 0 set FAILED=1
    cd ..
) else (
    echo [WARNING] Frontend directory not found
)
echo.

REM 5. Snyk Frontend
echo 5/5: Snyk (Frontend Dependencies)
where snyk >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    if exist frontend (
        cd frontend
        snyk test --severity-threshold=high
        if %ERRORLEVEL% NEQ 0 set FAILED=1
        cd ..
    )
) else (
    echo [WARNING] Snyk not installed
)
echo.

REM Summary
echo ==================================
if %FAILED% EQU 0 (
    echo [SUCCESS] All security scans passed!
    exit /b 0
) else (
    echo [FAILED] Some security scans found issues
    echo Review the output above and fix issues before committing
    exit /b 1
)
