@echo off
cls
color 0A
echo.
echo ========================================
echo   BACKEND SERVER START - FOLLOW THESE STEPS
echo ========================================
echo.
echo STEP 1: Make sure you are in backend folder
cd /d "%~dp0"
echo Current folder: %CD%
echo.
echo STEP 2: Activating virtual environment...
if exist "dogai_venv\Scripts\activate.bat" (
    call dogai_venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [ERROR] Virtual environment NOT found!
    echo Please create it: python -m venv dogai_venv
    pause
    exit /b 1
)
echo.
echo STEP 3: Starting server...
echo.
echo ========================================
echo   IMPORTANT: Keep this window open!
echo   Server will start on port 8000
echo ========================================
echo.
echo Press CTRL+C to stop server when done
echo.
timeout /t 2 /nobreak >nul
echo Starting now...
echo.
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo Server stopped.
pause


