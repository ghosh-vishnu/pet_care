# 🔍 Backend Server Not Starting? Check These:

## ✅ Step 1: Check if Server is Actually Running

Open browser and go to: **http://localhost:8000/health**

- ✅ If you see `{"status":"healthy"}` → Server IS running!
- ❌ If you see "This site can't be reached" → Server is NOT running

## ✅ Step 2: Start the Server

### Easiest Method:
1. Go to `backend` folder
2. Double-click `START_HERE.bat`
3. Keep the window OPEN
4. Wait for message: `INFO: Uvicorn running on http://127.0.0.1:8000`

### PowerShell Method:
```powershell
cd backend
.\start_server.ps1
```

## ✅ Step 3: Common Problems

### Problem 1: "ModuleNotFoundError"
**Solution:** Virtual environment not activated
```powershell
cd backend
.\dogai_venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Problem 2: "Port 8000 already in use"
**Solution:** Kill the process
```powershell
# Find process
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Kill it (replace PID)
Stop-Process -Id <PID> -Force
```

### Problem 3: "Database connection failed"
**Solution:** Make sure PostgreSQL is running
- Check PostgreSQL service in Windows Services
- Or start it manually

### Problem 4: Server starts but immediately crashes
**Solution:** Check the error message in the console
- Usually shows which import or connection is failing

## ✅ Step 4: Verify Server is Working

After starting, test in browser:
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## 📝 Important Notes:

1. **Server window MUST stay open** - Closing it stops the server
2. **Start server BEFORE logging in** - Frontend needs backend running
3. **Check console for errors** - If server doesn't start, read the error message

