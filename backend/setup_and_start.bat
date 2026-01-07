@echo off
echo ========================================
echo Dog Health AI - Complete Setup & Start
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "dogai_venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv dogai_venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created!
)

echo.
echo Activating virtual environment...
call dogai_venv\Scripts\activate.bat

echo.
echo Checking/Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed to install
)

echo.
echo Checking database connection...
python -c "from database import engine; engine.connect(); print('Database connection OK')" 2>nul
if errorlevel 1 (
    echo WARNING: Database connection failed. Make sure PostgreSQL is running.
    echo Continuing anyway...
)

echo.
echo ========================================
echo Starting Backend Server...
echo ========================================
echo Server will run on: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Press CTRL+C to stop
echo ========================================
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause




