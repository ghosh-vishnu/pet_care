@echo off
title Dog Health AI - Backend Server (KEEP THIS WINDOW OPEN!)
color 0A
echo.
echo ========================================
echo   BACKEND SERVER
echo   KEEP THIS WINDOW OPEN!
echo ========================================
echo.
cd /d "%~dp0"
call dogai_venv\Scripts\activate.bat
echo Server starting...
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000
echo.
echo Server stopped!
pause


