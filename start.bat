@echo off
setlocal enabledelayedexpansion
title ApplyPilot - Local AI Job Application Assistant

echo =====================================================================
echo                 ApplyPilot - Windows Launcher
echo       Local-First AI-Powered Job Application Assistant
echo =====================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12+ was not found in your PATH.
    echo Please install Python 3.12 or higher and check "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Check Node & npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js and npm were not found in your PATH.
    echo Please install Node.js (v20+ recommended).
    pause
    exit /b 1
)

:: 3. Check / Initialize Python virtual environment
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

:: 4. Check / Install frontend node_modules
if not exist "frontend\node_modules" (
    echo [*] Installing frontend packages...
    pushd frontend
    call npm install
    popd
)

:: 5. Create required local storage directories
if not exist "data\screenshots" mkdir data\screenshots
if not exist "data\browser_profile" mkdir data\browser_profile
if not exist "resumes" mkdir resumes
if not exist "logs" mkdir logs

:: 6. Launch Backend in background
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000...
start "ApplyPilot Backend (FastAPI)" /min cmd /c "backend\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

:: 7. Launch Frontend in background
echo [*] Starting Vite Frontend on http://127.0.0.1:5173...
start "ApplyPilot Frontend (Vite)" /min cmd /c "cd frontend && npm run dev"

:: 8. Wait for services to initialize
echo [*] Waiting for services to become ready...
timeout /t 3 /nobreak >nul

:: 9. Open Chrome to GUI
echo [*] Opening ApplyPilot Dashboard in Google Chrome...
start chrome "http://127.0.0.1:5173" || start http://127.0.0.1:5173

echo.
echo =====================================================================
echo ApplyPilot is running!
echo   Frontend GUI: http://127.0.0.1:5173
echo   API & Docs:   http://127.0.0.1:8000/docs
echo.
echo Leave this window open. Press any key to close the launcher.
echo =====================================================================
pause
