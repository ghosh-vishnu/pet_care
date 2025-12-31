# Setup Instructions - Dog Health AI (PostgreSQL Version)

## Prerequisites

1. **PostgreSQL** - Install from https://www.postgresql.org/download/
2. **Python 3.10+** - For backend
3. **Node.js 18+** - For frontend
4. **OpenAI API Key** - For AI features

## Step 1: Database Setup

### Install PostgreSQL
- Download and install PostgreSQL
- Remember the password you set for the `postgres` user

### Create Database
Open PostgreSQL command line or pgAdmin and run:

```sql
CREATE DATABASE dog_health_ai;
```

## Step 2: Backend Setup

### Navigate to backend
```bash
cd backend
```

### Create virtual environment
```bash
python -m venv dogai_venv
dogai_venv\Scripts\activate  # Windows
# or
source dogai_venv/bin/activate  # Linux/Mac
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Create .env file
Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:root@localhost:5432/dog_health_ai
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
OPENAI_API_KEY=your-openai-api-key-here
```

**Note:** Database name is `dog_health_ai` and password is `root` (as configured).

### Initialize Database
```bash
python -c "from database import Base, engine; from models.database_models import *; Base.metadata.create_all(bind=engine)"
```

### Replace old files
```bash
# Backup old files
mv main.py main_old.py
mv main_new.py main.py

mv services/llm_service.py services/llm_service_old.py
mv services/llm_service_new.py services/llm_service.py
```

### Start Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: http://localhost:8000
API Docs: http://localhost:8000/docs

## Step 3: Frontend Setup

### Navigate to frontend
```bash
cd frontend-vite
```

### Install dependencies
```bash
npm install
```

### Create .env file
Create `frontend-vite/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Start Frontend
```bash
npm run dev
```

Frontend will run on: http://localhost:3000

## Step 4: Test the Application

1. Open http://localhost:3000
2. Click "Sign Up" to create an account
3. Fill in pet profile
4. Start using the app!

## Troubleshooting

### Database Connection Error
- Check PostgreSQL is running
- Verify DATABASE_URL in .env is correct
- Check username/password

### Port Already in Use
- Backend: Change port in uvicorn command
- Frontend: Change port in vite.config.js

### Module Not Found
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Pet Profile
- `GET /user/{user_id}/pet/{pet_id}/profile/status` - Check profile status
- `POST /user/{user_id}/pet/{pet_id}/profile` - Save/update profile

### Chat
- `POST /user/{user_id}/pet/{pet_id}/chat` - Send message
- `GET /user/{user_id}/pet/{pet_id}/chat/messages` - Get messages

### Uploads
- `POST /user/{user_id}/pet/{pet_id}/upload/analyze` - Upload image
- `POST /user/{user_id}/pet/{pet_id}/upload/analyze_document` - Upload report

All endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

