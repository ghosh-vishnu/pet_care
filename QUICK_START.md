# 🚀 Quick Start Guide - Dog Health AI

## Backend Server Setup (IMPORTANT!)

### Option 1: Complete Setup (Recommended) ✅

**Windows Command Prompt (CMD):**
```cmd
cd backend
setup_and_start.bat
```

**Windows PowerShell:**
```powershell
cd backend
.\setup_and_start.bat
```

यह script automatically:
- Virtual environment create/activate करेगी
- Dependencies install करेगी
- Database check करेगी
- Server start करेगी

### Option 2: Manual Start (अगर पहले से setup है)

**Windows Command Prompt (CMD):**
```cmd
cd backend
start_server.bat
```

**Windows PowerShell:**
```powershell
cd backend
.\start_server.bat
```

## Verify Server is Running

1. Browser में खोलें: `http://localhost:8000/docs`
   - API documentation दिखनी चाहिए

2. या check करें:
```cmd
cd backend
python check_server.py
```

## CORS Fix Applied ✅

- ✅ CORS middleware configured
- ✅ All origins allowed (localhost:3000, localhost:3001)
- ✅ All methods and headers allowed
- ✅ Error handling improved

## Important Notes

⚠️ **Backend server MUST be running before using frontend!**

1. Backend server start करें (port 8000 पर)
2. Frontend start करें (port 3000 पर)
3. Browser में test करें

## Database Constraint Fix

अगर आपको **UniqueViolation** error आ रहा है (duplicate key on pet_id):

```cmd
cd backend
python fix_database_constraint.py
```

यह script:
- Old unique constraint को remove करेगी
- New composite unique constraint add करेगी (user_id + pet_id)
- अब हर user अपना own pet create कर सकता है same pet_id के साथ

## Troubleshooting

### CORS Error still showing?
1. Backend server को **restart** करें (Ctrl+C फिर फिर से start)
2. Browser cache clear करें (Ctrl+Shift+Delete)
3. Browser को refresh करें (F5)

### 500 Internal Server Error - UniqueViolation?
**Fix करें:**
```cmd
cd backend
python fix_database_constraint.py
```
फिर server को restart करें।

### 500 Internal Server Error - Other?
- Database connection check करें
- Check backend terminal में error messages
- `.env` file verify करें

### Server not starting?
- Check if port 8000 is free
- Make sure PostgreSQL is running
- Check virtual environment is activated

