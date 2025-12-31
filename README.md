# Dog Health AI Project

A comprehensive dog health management application with AI-powered chat, nutrition calculator, and health report analysis.

## 📁 Project Structure

```
dog-health-ai/
├── frontend/          # React + Vite frontend application
│   ├── src/
│   │   ├── pages/     # React pages (Login, Chat, Dashboard, etc.)
│   │   ├── services/  # API services
│   │   └── contexts/  # React contexts (Auth)
│   ├── package.json
│   └── vite.config.js
├── backend/           # FastAPI Python backend server
│   ├── services/      # Business logic services
│   ├── models/        # Database models and schemas
│   ├── routes/        # API routes
│   ├── main.py        # FastAPI application entry point
│   ├── database.py    # Database configuration
│   └── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (for backend)
- Node.js 16+ and npm (for frontend)
- PostgreSQL database

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   # Windows
   python -m venv dogai_venv
   dogai_venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv dogai_venv
   source dogai_venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL database:
   - Create database: `dog_health_ai`
   - Update `.env` file with database credentials:
     ```
     DATABASE_URL=postgresql://postgres:root@localhost:5432/dog_health_ai
     SECRET_KEY=your-secret-key-here
     OPENAI_API_KEY=your-openai-api-key-here
     ```

5. Initialize database:
   ```bash
   python setup_database.py
   ```

6. Start the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API documentation will be available at: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update API URL in `src/config.js` if needed:
   ```javascript
   export const API_BASE_URL = 'http://localhost:8000';
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to: `http://localhost:3000`

## 📝 Features

- **User Authentication**: JWT-based authentication
- **Pet Profile Management**: Create and manage pet profiles
- **AI Chat**: Chat with AI about your dog's health
- **Nutrition Calculator**: Calculate daily nutritional requirements
- **Health Reports**: Upload and analyze veterinary reports
- **Image Analysis**: Upload dog images for breed detection and health analysis

## 🔧 Configuration

### Environment Variables (Backend)

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://postgres:root@localhost:5432/dog_health_ai
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Frontend Configuration

Update `frontend/src/config.js` with your backend API URL:

```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

## 📚 API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /user/{user_id}/pet/{pet_id}/profile/status` - Get pet profile status
- `POST /user/{user_id}/pet/{pet_id}/profile` - Save pet profile
- `POST /user/{user_id}/pet/{pet_id}/chat` - Send chat message
- `GET /user/{user_id}/pet/{pet_id}/chat/messages` - Get chat messages
- `POST /user/{user_id}/pet/{pet_id}/upload/analyze` - Upload and analyze image
- `POST /user/{user_id}/pet/{pet_id}/upload/analyze_document` - Upload and analyze document
- `POST /user/{user_id}/pet/{pet_id}/nutrition/calculate` - Calculate nutrition
- `GET /user/{user_id}/pet/{pet_id}/reports` - Get reports

## 🛠️ Technology Stack

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- OpenAI API
- JWT Authentication

### Frontend
- React
- Vite
- React Router
- Axios

## 📄 License

This project is for educational purposes.
