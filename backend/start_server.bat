@echo off
echo ========================================
echo Starting Dog Health AI Backend Server...
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "dogai_venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call dogai_venv\Scripts\activate.bat
    echo Virtual environment activated!
) else (
    echo WARNING: Virtual environment not found!
    echo Please create it with: python -m venv dogai_venv
    echo.
    pause
    exit /b 1
)

echo.
echo Checking if uvicorn is installed...
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo ERROR: uvicorn is not installed!
    echo Installing uvicorn...
    pip install uvicorn[standard]
)

echo.
echo ========================================
echo Starting server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Press CTRL+C to stop the server
echo ========================================
echo.

REM Start uvicorn server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

