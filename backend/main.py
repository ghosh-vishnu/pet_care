# main.py - FastAPI Backend with PostgreSQL

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from services import report_reader
import os, io, json
from PIL import Image
from typing import Optional
from pydantic import BaseModel
from models.schemas import ChatRequest, ChatAnswer, ImageAnalysis
from models.database_models import Pet
from database import get_db, Base, engine
from services.db_service import (
    get_pet_profile, create_or_update_pet_profile, create_chat_message,
    get_chat_messages, create_uploaded_image, create_report, get_pet_reports
)
from services.auth_service import (
    authenticate_user, register_user, create_access_token, verify_token
)
from services.dog_detector import is_dog_image
from services.breed_classifier import predict_breed
from services.image_service import analyze_image
from services.storage import ensure_dirs, UPLOAD_DIR, REPORT_DIR, register_image
from services.llm_service import generate_dynamic_answer, write_ai_message_to_database
from services.nutrition_service import calculate_and_suggest_nutrition, NutritionResult

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dog Health AI Backend", version="2.0.0")
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static folders
ensure_dirs()
app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

# Pydantic Models
class PetProfileData(BaseModel):
    petName: str
    breed: str
    weight: str
    age: str
    gender: str
    season: str
    activityLevel: str
    behaviorNotes: str
    medicalConditions: list[str]
    goals: list[str]

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(user_id)

# Routes
@app.get("/")
def root():
    return {"status": "ok", "message": "Dog Health AI API running with PostgreSQL"}

# Authentication endpoints
@app.post("/auth/register")
async def register(req: SignupRequest, db: Session = Depends(get_db)):
    user = register_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@app.post("/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

# Pet profile endpoints
@app.get("/user/{user_id}/pet/{pet_id}/profile/status")
async def check_pet_profile_status(
    user_id: int,
    pet_id: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    profile_data = get_pet_profile(db, user_id, pet_id)
    
    if profile_data:
        return {
            "status": "EXISTS",
            "message": "Pet profile found.",
            "profile_data": profile_data
        }
    else:
        return {
            "status": "MISSING",
            "message": "Pet profile not found. Must fill details.",
            "profile_data": None
        }

@app.post("/user/{user_id}/pet/{pet_id}/profile")
async def save_pet_profile(
    user_id: int,
    pet_id: str,
    profile: PetProfileData,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    profile_dict = profile.model_dump()
    pet = create_or_update_pet_profile(db, user_id, pet_id, profile_dict)
    return {"success": True, "message": "Profile saved successfully"}

# Chat endpoints
@app.post("/user/{user_id}/pet/{pet_id}/chat", response_model=ChatAnswer)
async def chat_in_session(
    user_id: int,
    pet_id: str,
    req: ChatRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get pet for database operations
    from services.db_service import get_pet_by_id
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    user_msg = req.question.strip()
    location = getattr(req, "location", None)
    pet_profile = req.pet_profile
    
    # Save user message
    create_chat_message(db, pet.id, str(user_id), user_msg)
    
    # Generate AI response
    history = []
    answer = generate_dynamic_answer(user_msg, history, location, pet_profile)
    
    # Save AI response using the new function
    await write_ai_message_to_database(db, pet.id, answer, sender_is_user=False)
    
    return ChatAnswer(answer=answer, matched_question=None, score=1.0)

@app.get("/user/{user_id}/pet/{pet_id}/chat/messages")
async def get_chat_messages_endpoint(
    user_id: int,
    pet_id: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from services.db_service import get_pet_by_id
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    messages = get_chat_messages(db, pet.id)
    return [{
        "sender": msg.sender,
        "text": msg.text,
        "image_url": msg.image_url,
        "timestamp": msg.timestamp.isoformat()
    } for msg in messages]

# Upload endpoints
@app.post("/user/{user_id}/pet/{pet_id}/upload/analyze")
async def combined_upload_and_analyze(
    user_id: int,
    pet_id: str,
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from services.db_service import get_pet_by_id
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    raw = await file.read()
    file_type = file.content_type.lower()
    
    if 'image' in file_type:
        try:
            pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Save file
        dst = os.path.join(UPLOAD_DIR, file.filename)
        with open(dst, "wb") as f:
            f.write(raw)
        
        # Analyze image
        breed, breed_conf = predict_breed(dst)
        brightness, clarity, color_balance, summary, nutrition = analyze_image(dst)
        
        # Save to database
        create_uploaded_image(
            db, pet.id, file.filename, dst,
            breed=breed, breed_confidence=breed_conf,
            brightness=brightness, clarity=clarity,
            color_balance=color_balance, summary=summary, nutrition=nutrition
        )
        
        # Create chat messages
        image_url = f"/images/{file.filename}"
        create_chat_message(db, pet.id, str(user_id), f"Dog photo uploaded: {file.filename}.", image_url=image_url)
        breed_message = f"✅ Image analyzed! I detect a **{breed}** with {round(breed_conf*100)}% confidence. Summary: {summary}"
        await write_ai_message_to_database(db, pet.id, breed_message, sender_is_user=False)
        
        return JSONResponse(content={"status": "Image analyzed", "message": "Results sent to chat."})
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

@app.post("/user/{user_id}/pet/{pet_id}/upload/analyze_document")
async def analyze_vet_report(
    user_id: int,
    pet_id: str,
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from services.db_service import get_pet_by_id
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    dst = os.path.join(REPORT_DIR, file.filename)
    raw = await file.read()
    with open(dst, "wb") as f:
        f.write(raw)
    file_type = file.content_type.lower()
    
    if 'pdf' in file_type or 'image' in file_type:
        report_results = report_reader.analyze_health_report(raw, file_type)
        
        if "error" in report_results:
            raise HTTPException(status_code=400, detail=report_results["detail"])
        
        # Save report
        create_report(db, user_id, pet.id, file.filename, dst, report_results.get("analysis_result"))
        
        # Create chat messages
        create_chat_message(db, pet.id, str(user_id), f"Vet Report uploaded: {file.filename}.")
        await write_ai_message_to_database(db, pet.id, report_results["analysis_result"], sender_is_user=False)
        
        return JSONResponse(content={"status": "Report analyzed", "message": "Results sent to chat."})
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

# Nutrition endpoint
@app.post("/user/{user_id}/pet/{pet_id}/nutrition/calculate", response_model=NutritionResult)
async def get_nutrition_recommendations(
    user_id: int,
    pet_id: str,
    profile: PetProfileData,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pet_profile_dict = profile.model_dump()
    result = await calculate_and_suggest_nutrition(pet_profile_dict)
    return result

# Reports endpoint
@app.get("/user/{user_id}/pet/{pet_id}/reports")
async def get_reports(
    user_id: int,
    pet_id: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from services.db_service import get_pet_by_id
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    reports = get_pet_reports(db, pet.id)
    return [
        {
            "id": report.id,
            "filename": report.filename,
            "file_path": report.file_path,
            "analysis_result": report.analysis_result,
            "created_at": report.created_at.isoformat() if report.created_at else None
        }
        for report in reports
    ]

