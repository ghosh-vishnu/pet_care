# ✅ FIXED: Server Timeout Issue

## Problem:
Server starts but frontend gets timeout error.

## Solution:

### Step 1: Use the NEW startup script
Double-click: `FIXED_START.bat`

**OR** Run manually:
```powershell
cd backend
.\dogai_venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Step 2: Wait for this message
You should see:
```
INFO: Application startup complete.
```

### Step 3: DON'T close the window!
The server MUST stay running.

### Step 4: Test in browser
Open: http://127.0.0.1:8000/health

Should show: `{"status":"healthy","cors":"enabled"}`

### Step 5: Login in frontend
Now try login - it should work!

## ⚠️ Important:
- Server window MUST stay open
- Use `127.0.0.1` instead of `0.0.0.0` (more reliable on Windows)
- If still timeout, check Windows Firewall

