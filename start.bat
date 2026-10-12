@echo off
setlocal enabledelayedexpansion
title ApplyPilot - Local AI Job Application Assistant

:: Always change directory to the project root folder
cd /d "%~dp0"

echo =====================================================================
echo                 ApplyPilot - Windows Launcher
echo       Local-First AI-Powered Job Application Assistant
echo =====================================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.12 or higher and check "Add Python to PATH".
    pause
    exit /b 1
)

REM 2. Check Node and npm
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js was not found in your PATH.
    echo Please install Node.js version 20 or higher.
    pause
    exit /b 1
)

REM 3. Free up ports 8000 and 5173 if previous instances are lingering
echo [*] Checking for lingering processes on ports 8000 and 5173...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 5173 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM 4. Check / Initialize Python virtual environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [*] Creating Python virtual environment in backend\venv...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Installing backend dependencies...
    backend\venv\Scripts\pip install -r backend\requirements.txt
    backend\venv\Scripts\playwright install chromium
)

REM 5. Check / Install frontend node_modules
if not exist "frontend\node_modules" (
    echo [*] Installing frontend packages...
    pushd frontend
    call npm install
    popd
)

REM 6. Create required local storage directories
if not exist "data\screenshots" mkdir data\screenshots
if not exist "data\browser_profile" mkdir data\browser_profile
if not exist "resumes" mkdir resumes
if not exist "logs" mkdir logs

REM 7. Launch Backend (FastAPI on 127.0.0.1:8000)
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000...
start "ApplyPilot Backend (FastAPI)" cmd /k "backend\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

REM 8. Launch Frontend (Vite on 127.0.0.1:5173)
echo [*] Starting Vite Frontend on http://127.0.0.1:5173...
start "ApplyPilot Frontend (Vite)" /D "%~dp0frontend" cmd /k "npm run dev"

REM 9. Wait for services to initialize
echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 4 >nul

REM 10. Open default browser to GUI
echo [*] Opening ApplyPilot Dashboard in your browser...
start "" "http://127.0.0.1:5173"

echo.
echo =====================================================================
echo ApplyPilot is running!
echo   Frontend GUI: http://127.0.0.1:5173
echo   API Docs:     http://127.0.0.1:8000/docs
echo.
echo Two service console windows are open for Backend and Frontend.
echo You may minimize them while using ApplyPilot.
echo =====================================================================
echo.
pause
