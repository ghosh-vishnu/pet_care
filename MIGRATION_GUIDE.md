# Migration Guide: Firebase to PostgreSQL

## Overview
This project has been migrated from Firebase to PostgreSQL database with JWT authentication.

## Backend Changes

### 1. Database Setup

#### Install PostgreSQL
```bash
# Windows (using Chocolatey)
choco install postgresql

# Or download from: https://www.postgresql.org/download/windows/
```

#### Create Database
```sql
CREATE DATABASE dog_health_ai;
CREATE USER doguser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dog_health_ai TO doguser;
```

#### Update Environment Variables
Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:root@localhost:5432/dog_health_ai
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key
```

**Note:** Database name is `dog_health_ai` and password is `root`.

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
cd backend
python -c "from database import Base, engine; from models.database_models import *; Base.metadata.create_all(bind=engine)"
```

### 4. Update main.py
Replace `backend/main.py` with `backend/main_new.py`:
```bash
cd backend
mv main.py main_old.py
mv main_new.py main.py
```

### 5. Update llm_service.py
Replace `backend/services/llm_service.py` with `backend/services/llm_service_new.py`:
```bash
cd backend/services
mv llm_service.py llm_service_old.py
mv llm_service_new.py llm_service.py
```

## Frontend Changes

### 1. Install Dependencies
```bash
cd frontend-vite
npm install
```

### 2. Environment Variables
Create `frontend-vite/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run Frontend
```bash
cd frontend-vite
npm run dev
```

## Running the Application

### Backend
```bash
cd backend
python -m venv dogai_venv
dogai_venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend-vite
npm run dev
```

## API Changes

### Authentication
- **Old**: Firebase Auth
- **New**: JWT tokens

**Login:**
```bash
POST /auth/login
Body: { "email": "user@example.com", "password": "password123" }
Response: { "access_token": "...", "user_id": 1 }
```

**Register:**
```bash
POST /auth/register
Body: { "email": "user@example.com", "password": "password123" }
Response: { "access_token": "...", "user_id": 1 }
```

### API Endpoints
All endpoints now require JWT authentication:
```
Authorization: Bearer <token>
```

Endpoints changed from:
- `/user/{uid}/pet/{pet_id}/...` (uid was Firebase UID string)

To:
- `/user/{user_id}/pet/{pet_id}/...` (user_id is integer from database)

## Database Schema

### Tables
- `users` - User accounts
- `pets` - Pet profiles
- `chat_messages` - Chat messages
- `uploaded_images` - Image uploads
- `reports` - Health reports

## Migration Notes

1. **User IDs**: Changed from Firebase UID strings to integer IDs
2. **Authentication**: JWT tokens instead of Firebase tokens
3. **Real-time**: Removed Firebase real-time listeners (can be added with WebSockets if needed)
4. **File Storage**: Still uses local file system for images/reports

## Next Steps

1. Complete remaining page components in `frontend-vite/src/pages/`
2. Migrate remaining screens from old frontend
3. Add WebSocket support for real-time chat (optional)
4. Add file upload to cloud storage (optional)

