@echo off
title Dog Health AI - Backend Server
color 0A
echo ========================================
echo   Dog Health AI - Backend Server
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment
echo [1/4] Activating virtual environment...
if not exist "dogai_venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv dogai_venv
    pause
    exit /b 1
)
call dogai_venv\Scripts\activate.bat
echo OK: Virtual environment activated
echo.

REM Check Python
echo [2/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo.

REM Test imports
echo [3/4] Testing imports...
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo WARNING: uvicorn not found, installing...
    pip install uvicorn[standard]
)

python -c "import main" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot import main.py!
    echo.
    echo Testing import...
    python -c "import main" 2>&1
    echo.
    pause
    exit /b 1
)
echo OK: All imports successful
echo.

REM Start server
echo [4/4] Starting server...
echo.
echo ========================================
echo   Server will start on:
echo   http://localhost:8000
echo.
echo   Health Check: http://localhost:8000/health
echo   API Docs: http://localhost:8000/docs
echo.
echo   Press CTRL+C to stop the server
echo ========================================
echo.
echo Starting now...
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

