# 🚀 Quick Start - Backend Server

## Problem: Login Timeout / Backend Not Responding

If you see "Request timeout" error, the backend server is not running.

## ✅ Solution: Start Backend Server

### Method 1: PowerShell Script (Recommended)

Open PowerShell in `backend` folder and run:

```powershell
.\start_server.ps1
```

### Method 2: Batch File (Windows)

Double-click or run in CMD:

```cmd
start_server.bat
```

### Method 3: Manual Start

```powershell
# 1. Navigate to backend folder
cd backend

# 2. Activate virtual environment
.\dogai_venv\Scripts\Activate.ps1

# 3. Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Verify Server is Running

After starting, you should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Test in browser:
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

## 🔧 Troubleshooting

### Port 8000 Already in Use
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Kill process (replace PID with actual process ID)
Stop-Process -Id <PID> -Force
```

### Virtual Environment Not Found
```powershell
cd backend
python -m venv dogai_venv
.\dogai_venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Import Errors
```powershell
# Test imports
python -c "import main"
```

## 📝 Notes

- Server must be running BEFORE you try to login
- Keep the server terminal window open while using the app
- Use CTRL+C to stop the server


