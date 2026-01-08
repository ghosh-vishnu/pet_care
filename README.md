# Dog Health AI - Complete Project Documentation

A comprehensive AI-powered dog health management application with intelligent chat, nutrition calculator, breed detection, and health report analysis.

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Project Architecture](#project-architecture)
5. [AI Models & How They Work](#ai-models--how-they-work)
6. [Setup Instructions](#setup-instructions)
7. [Configuration](#configuration)
8. [API Endpoints](#api-endpoints)
9. [FAQ System (RAG)](#faq-system-rag)
10. [Breed Detection Model](#breed-detection-model)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

Dog Health AI is a production-ready application that helps dog owners manage their pet's health through:

- **Intelligent Chat System**: FAQ-based RAG system with semantic search and GPT fallback
- **Image Analysis**: Breed detection and health analysis from dog photos
- **Nutrition Calculator**: AAFCO-compliant daily nutritional requirements
- **Health Reports**: Veterinary report analysis and insights
- **Pet Profile Management**: Comprehensive pet information storage

### Performance Metrics

- **Greetings**: ~10ms (instant static response) - 80-120x faster than previous
- **FAQ Queries**: ~100-300ms (single DB query) - 6x faster than previous
- **Cost Reduction**: ~90% reduction for greeting queries (no OpenAI calls)
- **Intent Routing**: Lightweight router (~1ms) before any AI/DB calls

---

## Features

### 1. **User Authentication**
- JWT-based authentication
- Secure user registration and login
- Session management

### 2. **Pet Profile Management**
- Create and manage multiple pet profiles
- Auto-update breed from image uploads
- Store weight, age, breed, medical conditions, and more

### 3. **AI-Powered Chat System**
- **Intent Router**: Lightweight classification (GREETING, IMAGE_QUERY, FAQ_QUESTION)
- **FAQ RAG System**: PostgreSQL + pgvector for semantic search
- **GPT Fallback**: Intelligent context-aware responses when FAQ doesn't match
- **Multi-language Support**: Handles Hinglish, informal English, and typos

### 4. **Image Analysis**
- **Dog Detection**: MobileNet V3-based validation
- **Breed Classification**: EfficientNet-B0 model (120 breeds)
- **Health Analysis**: GPT-4o-mini Vision API for comprehensive health insights
- **Auto-Profile Update**: Automatically updates breed in pet profile

### 5. **Nutrition Calculator**
- AAFCO-compliant calculations
- Breed-specific recommendations
- Daily calorie and macronutrient requirements
- Supplement suggestions

### 6. **Health Reports**
- Upload and analyze veterinary reports
- Extract key health metrics
- Generate actionable insights

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL 12+ with pgvector extension
- **ORM**: SQLAlchemy
- **AI/ML**: 
  - OpenAI API (GPT-3.5-turbo, GPT-4o-mini, text-embedding-3-small)
  - PyTorch (EfficientNet-B0, MobileNet V3)
- **Authentication**: JWT (python-jose, passlib, bcrypt)
- **File Processing**: PIL, OpenCV, pytesseract

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router
- **HTTP Client**: Axios
- **Styling**: CSS3

---

## Project Architecture

```
dog-health-ai/
├── backend/                    # FastAPI backend server
│   ├── main.py                # FastAPI application entry point
│   ├── database.py            # Database configuration
│   ├── models/                # Database models and Pydantic schemas
│   │   ├── database_models.py # SQLAlchemy models (User, Pet, FAQ, etc.)
│   │   └── schemas.py         # Pydantic request/response models
│   ├── services/              # Business logic services
│   │   ├── intent_router.py   # Lightweight intent classification
│   │   ├── faq_service_optimized.py  # FAQ RAG with pgvector
│   │   ├── llm_service.py     # GPT chat responses
│   │   ├── breed_classifier.py # EfficientNet-B0 breed detection
│   │   ├── dog_detector.py    # MobileNet V3 dog detection
│   │   ├── health_vision_service.py # GPT-4o-mini Vision health analysis
│   │   ├── nutrition_service.py # Nutrition calculations
│   │   └── ...
│   ├── routes/                # API route handlers
│   ├── scripts/               # Utility scripts
│   │   └── migrate_faqs_to_db.py # FAQ migration to database
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── pages/             # React pages (Login, Chat, Dashboard, etc.)
│   │   ├── services/          # API services
│   │   ├── contexts/          # React contexts (Auth)
│   │   └── config.js          # Frontend configuration
│   ├── package.json
│   └── vite.config.js
│
├── refined_faqs.json          # FAQ data (source file)
└── README.md                  # This file
```

---

## AI Models & How They Work

### 1. Intent Router (Lightweight Classification)

**Location**: `backend/services/intent_router.py`

**Purpose**: Classify user input before any AI/DB calls to optimize performance.

**How It Works**:
```
User Input
    ↓
1. Check for image (IMAGE_QUERY)
2. Check message length and patterns (GREETING)
3. Default to FAQ_QUESTION
```

**Output**: `GREETING` | `IMAGE_QUERY` | `FAQ_QUESTION`

**Performance**: ~1ms (regex-based, no AI calls)

---

### 2. FAQ RAG System (Retrieval-Augmented Generation)

**Location**: `backend/services/faq_service_optimized.py`

**Architecture**:
- **Database**: PostgreSQL with pgvector extension
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Vector Search**: pgvector cosine similarity search
- **Fallback**: Keyword-based search when embeddings unavailable

**Flow**:
```
User Question
    ↓
1. Generate embedding (ONCE) - OpenAI API
    ↓
2. Vector similarity search (pgvector) - Single DB query
    ├─ High confidence (≥0.85) → Return FAQ answer directly
    ├─ Medium confidence (≥0.70) → Return FAQ answer directly
    ├─ Low confidence (≥0.55) → GPT with FAQ context
    └─ No match (<0.55) → GPT with FAQ context
```

**Performance**:
- Embedding generation: ~100ms
- Vector search: ~50-200ms
- Total: ~100-300ms per query

**Features**:
- Handles spelling mistakes, Hinglish, informal English
- Keyword fallback when OpenAI quota exceeded
- Single query optimization (no loops)

---

### 3. GPT Chat Responses

**Location**: `backend/services/llm_service.py`

**Models Used**:
- **Chat**: GPT-3.5-turbo
- **Vision Analysis**: GPT-4o-mini
- **Nutrition**: GPT-4o-mini (JSON mode)

**System Prompt Structure**:
```python
system_prompt = f"""
You are a helpful AI assistant specialized in dog health and care.
Pet Profile: {pet_profile}
Location: {location}
FAQ Context: {faq_context}

Guidelines:
- 3-5 lines maximum
- Friendly, concise, chat-style
- No emojis
- No medical diagnosis
- Suggest veterinary consultation for health concerns
"""
```

**Context**:
- Pet profile (breed, age, weight, medical conditions)
- Chat history (last 5 messages)
- FAQ context (when available)
- Location-based advice

---

### 4. Dog Detection (MobileNet V3 Small)

**Location**: `backend/services/dog_detector.py`

**Technology**: PyTorch (ImageNet pre-trained MobileNet V3 Small)

**Method**:
1. Resize image to 224x224
2. Get top 5 ImageNet predictions
3. Match against 50+ dog-related keywords
4. Return validation result

**Output**: `(is_valid_dog: bool, confidence: float, message: str, detected_label: str)`

---

### 5. Breed Classification (EfficientNet-B0)

**Location**: `backend/services/breed_classifier.py`

**Technology**: PyTorch (Custom trained EfficientNet-B0)

**Architecture**:
- **Input**: 224x224 RGB image
- **Output**: 120 breed probabilities
- **Model File**: `backend/services/dog_breed_weights.pth`
- **Class List**: `backend/assets/dog_breeds_120.txt`

**Flow**:
```
Image Upload
    ↓
1. Preprocess (resize, normalize)
    ↓
2. Model forward pass
    ↓
3. Softmax (probabilities)
    ↓
4. Get top breed + confidence
    ↓
5. Auto-update pet profile (if confidence > 50%)
```

**Expected Accuracy** (after training):
- Top-1: ~70-80%
- Top-3: ~85-90%

**Training**: Run `python backend/train_classifier.py` (15-22 hours on CPU, faster on GPU)

---

### 6. Health Vision Analysis (GPT-4o-mini Vision)

**Location**: `backend/services/health_vision_service.py`

**Technology**: OpenAI GPT-4o-mini with Vision capabilities

**Analysis Focus**:
1. Body condition (underweight, normal, overweight)
2. Coat condition (healthy, dry, matted, skin issues)
3. Eye condition (clear, discharge, redness)
4. Overall posture and energy level
5. Visible health concerns
6. General appearance and vitality

**Output Structure**:
```python
{
    "body_condition": "Normal",
    "coat_condition": "Healthy",
    "eye_condition": "Normal",
    "energy_level": "Normal",
    "observations": "...",
    "recommendations": "...",
    "concerns": []
}
```

---

### 7. Nutrition Calculator

**Location**: `backend/services/nutrition_service.py`

**Technology**: GPT-4o-mini (JSON mode)

**Standards**: AAFCO (Association of American Feed Control Officials)

**Calculations**:
1. **RER** (Resting Energy Requirement): `70 * (Weight in kg)^0.75`
2. **MER** (Maintenance Energy Requirement): `RER * multiplier`
   - Multiplier based on age, activity level, neuter status
3. **Macronutrients**:
   - Protein: ≥18% (adult) / ≥22% (puppy)
   - Fat: ≥5% (adult) / ≥8% (puppy)
   - Carbs: Calculated from remainder

**Output**: JSON with calories, macros, distribution, and supplement suggestions

---

## Setup Instructions

### Prerequisites

1. **PostgreSQL 12+** - Install from [postgresql.org](https://www.postgresql.org/download/)
2. **Python 3.10+** - For backend
3. **Node.js 18+** - For frontend
4. **OpenAI API Key** - Get from [platform.openai.com](https://platform.openai.com)

### Step 1: Database Setup

#### Install PostgreSQL
- Download and install PostgreSQL
- Remember the `postgres` user password

#### Create Database
```sql
CREATE DATABASE dog_health_ai;
```

#### Install pgvector Extension
```sql
\c dog_health_ai
CREATE EXTENSION IF NOT EXISTS vector;
```

**Note**: If pgvector is not installed on your system:
- **Windows**: Download from [pgvector releases](https://github.com/pgvector/pgvector/releases)
- **Linux**: `sudo apt install postgresql-12-pgvector` (or appropriate version)
- **Mac**: `brew install pgvector`

### Step 2: Backend Setup

#### Navigate to Backend
```bash
cd backend
```

#### Create Virtual Environment
```bash
# Windows
python -m venv dogai_venv
dogai_venv\Scripts\activate

# Linux/Mac
python3 -m venv dogai_venv
source dogai_venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Create .env File
Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/dog_health_ai
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
OPENAI_API_KEY=your-openai-api-key-here
```

**Important**: Replace `your_password` with your PostgreSQL password and `your-secret-key` with a secure random string (minimum 32 characters).

#### Initialize Database
```bash
python -c "from database import Base, engine; from models.database_models import *; Base.metadata.create_all(bind=engine)"
```

#### Migrate FAQs to Database
```bash
python scripts/migrate_faqs_to_db.py
```

This will:
1. Load FAQs from `refined_faqs.json`
2. Generate OpenAI embeddings for each question
3. Store FAQs in database with vector embeddings
4. Create pgvector index for fast similarity search

**Note**: First run takes 30-60 seconds (embedding generation for all FAQs).

#### Start Backend Server
```bash
# Windows PowerShell
.\start_server.ps1

# Windows CMD
start_server.bat

# Linux/Mac
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Step 3: Frontend Setup

#### Navigate to Frontend
```bash
cd frontend
```

#### Install Dependencies
```bash
npm install
```

#### Update Configuration (if needed)
Edit `src/config.js`:
```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

#### Start Development Server
```bash
npm run dev
```

Frontend will run on: `http://localhost:3000`

### Step 4: Verify Setup

1. **Backend Health Check**: Visit `http://localhost:8000/health`
   - Should return: `{"status":"healthy"}`

2. **Database Verification**:
   ```sql
   SELECT COUNT(*) FROM faqs;
   SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;
   ```

3. **Test Intent Router**:
   ```python
   from services.intent_router import detect_intent
   print(detect_intent("hi"))  # Should return "GREETING"
   print(detect_intent("What should I feed my dog?"))  # Should return "FAQ_QUESTION"
   ```

---

## Configuration

### Environment Variables (Backend)

**File**: `backend/.env`

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/dog_health_ai

# Security
SECRET_KEY=your-secret-key-minimum-32-characters-long

# OpenAI API
OPENAI_API_KEY=sk-...

# FAQ Similarity Thresholds (optional, defaults shown)
FAQ_HIGH_THRESHOLD=0.85
FAQ_MEDIUM_THRESHOLD=0.70
FAQ_LOW_THRESHOLD=0.55
```

### Frontend Configuration

**File**: `frontend/src/config.js`

```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

### Intent Router Settings

**File**: `backend/services/intent_router.py`

```python
MIN_FAQ_LENGTH = 10      # Minimum length for FAQ question
MAX_GREETING_LENGTH = 50 # Max length for greeting detection
```

---

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

- `POST /auth/login` - Login user
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

### Pet Profile
- `GET /user/{user_id}/pet/{pet_id}/profile/status` - Get profile status
- `POST /user/{user_id}/pet/{pet_id}/profile` - Save/update profile

### Chat
- `POST /user/{user_id}/pet/{pet_id}/chat` - Send message
  ```json
  {
    "question": "What should I feed my dog?",
    "pet_profile": {...},
    "image_url": null
  }
  ```
  
  **Response**:
  ```json
  {
    "answer": "Answer text...",
    "matched_question": "Matching FAQ question",
    "score": 0.87,
    "source": "faq",
    "confidence": "high"
  }
  ```

- `GET /user/{user_id}/pet/{pet_id}/chat/messages` - Get chat history

### Image Upload
- `POST /user/{user_id}/pet/{pet_id}/upload/analyze` - Upload and analyze image
  - Returns: breed, health analysis, recommendations

- `POST /user/{user_id}/pet/{pet_id}/upload/analyze_document` - Upload and analyze document

### Nutrition
- `POST /user/{user_id}/pet/{pet_id}/nutrition/calculate` - Calculate nutrition requirements

### Reports
- `GET /user/{user_id}/pet/{pet_id}/reports` - Get health reports

**Note**: All endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

---

## FAQ System (RAG)

### Architecture

The FAQ system uses a production-ready RAG (Retrieval-Augmented Generation) approach:

1. **Intent Router**: Lightweight classification before any AI/DB calls
2. **Vector Search**: PostgreSQL + pgvector for fast semantic search
3. **GPT Fallback**: Context-aware responses when FAQ doesn't match

### Request Flow

```
User Message
    ↓
Intent Router (1ms)
    ↓
┌─────────────────────────────────────┐
│ Intent?                             │
├─────────────────────────────────────┤
│ GREETING → Instant static response │ ← NO AI/DB calls (~10ms)
│ IMAGE_QUERY → Image analysis flow  │
│ FAQ_QUESTION → FAQ vector search   │ ← Single query (~200ms)
└─────────────────────────────────────┘
```

### FAQ Search Flow

```
FAQ Question
    ↓
Generate embedding (ONCE) - OpenAI (~100ms)
    ↓
Single DB query (pgvector) - PostgreSQL (~50-200ms)
    ├─ High confidence (≥0.85) → Return FAQ answer directly
    ├─ Medium confidence (≥0.70) → Return FAQ answer directly
    ├─ Low confidence (≥0.55) → GPT with FAQ context
    └─ No match (<0.55) → GPT with FAQ context
```

### Features

- **Semantic Search**: Handles spelling mistakes, Hinglish, informal English
- **Keyword Fallback**: Works when OpenAI quota exceeded
- **Single Query Optimization**: No loops, one embedding + one DB query
- **Confidence Levels**: High, Medium, Low, None

### Adding New FAQs

1. **Add to JSON** (optional, for backup):
   ```json
   {
     "question": "Why does my dog...?",
     "answer": "Answer here...",
     "category": "Dog Health"
   }
   ```

2. **Migrate to Database**:
   ```bash
   python scripts/migrate_faqs_to_db.py
   ```

3. **Or Add Directly** (remember to generate embedding):
   ```sql
   INSERT INTO faqs (question, answer, category, embedding)
   VALUES ('Question?', 'Answer', 'Category', <embedding_vector>);
   ```

### Monitoring

```sql
-- Count FAQs
SELECT COUNT(*) FROM faqs;

-- Check embeddings
SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;

-- FAQs by category
SELECT category, COUNT(*) FROM faqs GROUP BY category;
```

---

## Breed Detection Model

### Training the Model

1. **Prepare Dataset**:
   ```
   backend/data/Images/
     ├── breed_1_name/
     │   ├── image1.jpg
     │   └── ...
     ├── breed_2_name/
     └── ...
   ```

2. **Update Class List** (if adding new breeds):
   Edit `backend/assets/dog_breeds_120.txt`:
   ```
   Afghan Hound
   Beagle
   Border Collie
   ...
   ```

3. **Train Model**:
   ```bash
   cd backend
   python train_classifier.py
   ```

   **Training Settings** (edit in `train_classifier.py`):
   ```python
   NUM_EPOCHS = 40      # Training iterations
   BATCH_SIZE = 16      # Images per batch
   LEARNING_RATE = 0.001
   ```

4. **Training Time**:
   - CPU: Several hours/days (depends on dataset size)
   - GPU: Much faster (recommended)

5. **Verify Model**:
   ```python
   from services.breed_classifier import predict_breed
   breed, confidence = predict_breed("path/to/test/image.jpg")
   print(f"Breed: {breed}, Confidence: {confidence*100:.2f}%")
   ```

### Tips for Better Accuracy

1. **Image Quality**: High resolution, clear, well-lit photos
2. **Dataset Size**: Minimum 50 images per breed, 200+ for excellent accuracy
3. **Variety**: Different angles, lighting, ages
4. **Data Augmentation**: Automatically applied during training

---

## Troubleshooting

### Database Connection Error

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
1. Check PostgreSQL is running
2. Verify `DATABASE_URL` in `.env` is correct
3. Check username/password
4. Ensure database `dog_health_ai` exists

### pgvector Extension Not Found

**Error**: `extension "vector" does not exist`

**Solutions**:
1. Install pgvector extension on PostgreSQL server
2. Run: `CREATE EXTENSION vector;` in your database
3. Verify: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### OpenAI API Quota Exceeded

**Problem**: FAQ search returns errors or uses keyword fallback

**Solutions**:
1. Check OpenAI API quota at [platform.openai.com/usage](https://platform.openai.com/usage)
2. System automatically falls back to keyword search
3. Once quota restored, re-run migration: `python scripts/migrate_faqs_to_db.py --force`

### Server Not Starting

**Problem**: Backend server fails to start

**Solutions**:
1. Check if port 8000 is free: `netstat -ano | findstr :8000` (Windows)
2. Ensure virtual environment is activated
3. Check dependencies installed: `pip install -r requirements.txt`
4. Verify `.env` file exists and has correct values

### CORS Errors

**Problem**: Frontend cannot connect to backend

**Solutions**:
1. Ensure backend is running on port 8000
2. Check CORS middleware in `main.py` allows `localhost:3000`
3. Clear browser cache and refresh

### FAQ Embeddings Not Generated

**Problem**: FAQ search returns no results

**Solutions**:
1. Check OpenAI API key is set in `.env`
2. Verify FAQs have embeddings: `SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;`
3. Re-run migration: `python scripts/migrate_faqs_to_db.py --force`

### Slow Performance

**If greetings are slow**:
- Check intent router is running first (before any DB/AI calls)
- Verify no OpenAI calls for "hi", "hello", etc.

**If FAQ search is slow**:
- Ensure pgvector extension is installed
- Check pgvector index: `\d faqs` should show vector index
- Verify single query (check logs for multiple queries)

### Module Not Found

**Problem**: Python import errors

**Solutions**:
1. Ensure virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.10+)

---

## Performance Benchmarks

### Before Optimization
- Greeting "hi": ~800ms (OpenAI call)
- FAQ query: ~1200ms (loop over all FAQs)
- Cost: ~$0.001 per greeting

### After Optimization
- Greeting "hi": ~10ms (instant response) - **80-120x faster**
- FAQ query: ~200ms (single DB query) - **6x faster**
- Cost: $0.00 per greeting - **90% reduction**

---

## Safety & Guidelines

### Response Rules
- **Length**: 3-5 lines maximum
- **Tone**: Friendly, concise, chat-style
- **Emojis**: Not used
- **Medical Diagnosis**: Never provided
- **Veterinary Consultation**: Always suggested for health concerns

### Safety Features
- No medical diagnosis or treatment
- Advisory language for health questions
- Professional tone maintained
- Limitations clearly stated

---

## License

This project is for educational purposes.

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review error logs in backend terminal
3. Verify configuration in `.env` files

---

**Built with ❤️ for dog health and care**
