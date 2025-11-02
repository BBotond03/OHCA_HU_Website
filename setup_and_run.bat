@echo off
setlocal enabledelayedexpansion
title 🚀 OHCA Hungary Dashboard Setup

:: Enable ANSI colors (Windows 10+)
for /f "tokens=2 delims=:." %%i in ('chcp') do set "_chcp=%%i"
chcp 65001 >nul

set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set RESET=[0m

echo %CYAN%======================================%RESET%
echo %GREEN%🚀 OHCA HUNGARY DASHBOARD SETUP%RESET%
echo %CYAN%======================================%RESET%

:: --- Check Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo %RED%[❌] Python not found. Please install Python 3.10+ and try again.%RESET%
    pause
    exit /b
)

:: --- Paths ---
set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%ohca_backend
set FRONTEND_DIR=%ROOT_DIR%ohca_frontend
set BACKEND_VENV=%BACKEND_DIR%\venv
set FRONTEND_VENV=%FRONTEND_DIR%\venv

:: ===============================
:: BACKEND SETUP
:: ===============================
echo.
echo %CYAN%[1/4] Setting up backend environment...%RESET%

if not exist "%BACKEND_VENV%" (
    echo %YELLOW%[+] Creating backend virtual environment...%RESET%
    python -m venv "%BACKEND_VENV%"
)

if not exist "%BACKEND_VENV%\.deps_installed" (
    echo %YELLOW%[+] Installing backend dependencies...%RESET%
    call "%BACKEND_VENV%\Scripts\python.exe" -m pip install --upgrade pip >nul
    if exist "%BACKEND_DIR%\requirements.txt" (
        call "%BACKEND_VENV%\Scripts\python.exe" -m pip install -r "%BACKEND_DIR%\requirements.txt"
    ) else (
        echo %YELLOW%⚠️ No backend requirements.txt found — skipping dependency install.%RESET%
    )
    echo done > "%BACKEND_VENV%\.deps_installed"
    echo %GREEN%[✓] Backend dependencies installed successfully.%RESET%
) else (
    echo %GREEN%[✓] Backend environment ready.%RESET%
)

:: ===============================
:: FRONTEND SETUP
:: ===============================
echo.
echo %CYAN%[2/4] Setting up frontend environment...%RESET%

if not exist "%FRONTEND_VENV%" (
    echo %YELLOW%[+] Creating frontend virtual environment...%RESET%
    python -m venv "%FRONTEND_VENV%"
)

if not exist "%FRONTEND_VENV%\.deps_installed" (
    echo %YELLOW%[+] Installing frontend dependencies...%RESET%
    call "%FRONTEND_VENV%\Scripts\python.exe" -m pip install --upgrade pip >nul
    if exist "%FRONTEND_DIR%\requirements.txt" (
        call "%FRONTEND_VENV%\Scripts\python.exe" -m pip install -r "%FRONTEND_DIR%\requirements.txt"
    ) else (
        echo %YELLOW%⚠️ No frontend requirements.txt found — skipping dependency install.%RESET%
    )
    echo done > "%FRONTEND_VENV%\.deps_installed"
    echo %GREEN%[✓] Frontend dependencies installed successfully.%RESET%
) else (
    echo %GREEN%[✓] Frontend environment ready.%RESET%
)

:: ===============================
:: START BACKEND
:: ===============================
echo.
echo %CYAN%[3/4] Starting FastAPI backend...%RESET%
start "FastAPI Backend" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate && python -m uvicorn main:app --reload"
echo %YELLOW%⏳ Waiting for backend to initialize (5s)...%RESET%
timeout /t 5 >nul
echo %GREEN%[✓] Backend started successfully.%RESET%

:: ===============================
:: START FRONTEND
:: ===============================
echo.
echo %CYAN%[4/4] Launching Streamlit frontend...%RESET%
cd /d "%FRONTEND_DIR%"
call "%FRONTEND_VENV%\Scripts\activate.bat"
python -m streamlit run app.py
deactivate

:: ===============================
:: CLEANUP WHEN FRONTEND CLOSES
:: ===============================
echo.
echo %CYAN%[🧹] Stopping backend...%RESET%
taskkill /FI "WINDOWTITLE eq FastAPI Backend" /T /F >nul 2>&1
echo %GREEN%✅ Backend stopped. All done!%RESET%
echo.
pause
exit /b
