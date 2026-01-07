@echo off
title BACKEND SERVER - DO NOT CLOSE THIS WINDOW!
color 0A
cls
echo.
echo ========================================
echo   BACKEND SERVER STARTING...
echo   DO NOT CLOSE THIS WINDOW!
echo ========================================
echo.

cd /d "%~dp0"
call dogai_venv\Scripts\activate.bat

echo Starting server on http://127.0.0.1:8000
echo.
echo Once you see "Application startup complete"
echo The server is READY to accept requests!
echo.
echo Keep this window open while using the app.
echo Press CTRL+C to stop the server.
echo.
echo ========================================
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8000

pause


