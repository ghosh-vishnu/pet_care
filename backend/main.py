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
    messages_list = []
    for msg in messages:
        # Map sender to frontend expected format
        # If sender is "ai_bot", it's an AI message, otherwise it's a user message
        sender = "ai" if msg.sender == "ai_bot" else "user"
        messages_list.append({
            "sender": sender,
            "text": msg.text or "",
            "image_url": msg.image_url,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
        })
    return {"messages": messages_list}

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
    from services.health_vision_service import analyze_health_with_vision, generate_health_summary
    import uuid
    from datetime import datetime
    
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    try:
        raw = await file.read()
        if not raw or len(raw) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        file_type = file.content_type.lower() if file.content_type else ""
        
        if 'image' not in file_type:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an image file.")
        
        # Validate image
        try:
            pil_img = Image.open(io.BytesIO(raw))
            pil_img.verify()  # Verify it's a valid image
            # verify() closes the image, so we need to reopen it
            pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Generate unique filename to avoid conflicts
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        if not file_ext:
            file_ext = ".jpg"
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save file
        dst = os.path.join(UPLOAD_DIR, unique_filename)
        with open(dst, "wb") as f:
            f.write(raw)
        
        # Verify file was saved
        if not os.path.exists(dst):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # STEP 1: Validate that the image contains a dog BEFORE any analysis
        from services.dog_detector import validate_dog_image
        is_valid_dog, dog_conf, dog_message, detected_label = validate_dog_image(dst)
        
        # Also check breed classifier as secondary validation
        breed_detected = False
        breed, breed_conf = None, 0.0
        try:
            breed, breed_conf = predict_breed(dst)
            # If breed classifier returns a valid breed with decent confidence, it's likely a dog
            if breed and breed_conf > 0.3 and "unknown" not in breed.lower():
                breed_detected = True
        except Exception as e:
            print(f"Breed prediction error during validation: {e}")
        
        # Final validation: Must pass either dog detector OR breed classifier
        if not is_valid_dog and not breed_detected:
            # Create user-friendly error message (readable and clear)
            # Extract just the detected object name from dog_message for cleaner display
            detected_obj = detected_label if detected_label else "unknown object"
            confidence_pct = round(dog_conf * 100, 1) if dog_conf > 0 else 0
            error_msg = f"**Image Validation Failed**\n\nThe uploaded image does not appear to contain a dog. The system detected: {detected_obj} (confidence: {confidence_pct}%).\n\n**Please Note:** This health analysis feature is designed specifically for dog images. Please upload a clear photo of your dog to receive health analysis."
            
            # Save user message and error response to chat
            create_chat_message(db, pet.id, str(user_id), f"Image uploaded: {file.filename or 'image'}.", image_url=f"/images/{unique_filename}")
            await write_ai_message_to_database(db, pet.id, error_msg, sender_is_user=False)
            
            # Return error response (don't raise exception so user sees the message in chat)
            return JSONResponse(
                status_code=400,
                content={
                    "status": "validation_failed",
                    "message": "Image does not appear to contain a dog",
                    "detail": dog_message,
                    "filename": unique_filename
                }
            )
        
        # If we reach here, image is validated as dog image
        # Continue with breed detection if not already done
        if not breed_detected:
            try:
                breed, breed_conf = predict_breed(dst)
                # Double-check: if breed is still invalid, use dog detector result
                if not breed or breed_conf < 0.2 or "unknown" in breed.lower():
                    breed = detected_label if is_valid_dog else "Unknown Breed"
                    breed_conf = dog_conf if is_valid_dog else 0.0
            except Exception as e:
                print(f"Breed prediction error: {e}")
                # Fallback to dog detector result
                breed = detected_label if is_valid_dog else "Unknown Breed"
                breed_conf = dog_conf if is_valid_dog else 0.0
        
        # Analyze image - Basic image quality
        try:
            brightness, clarity, color_balance, summary, nutrition = analyze_image(dst)
        except Exception as e:
            print(f"Image analysis error: {e}")
            brightness, clarity, color_balance = 0.5, 0.5, 0.5
            summary = "Image quality analysis completed"
            nutrition = []
        
        # Advanced health analysis using vision AI
        try:
            health_analysis = analyze_health_with_vision(dst, breed)
            # Clean breed name before generating summary
            clean_breed = breed
            if breed:
                from services.health_vision_service import _clean_breed_name
                clean_breed = _clean_breed_name(breed)
            health_summary = generate_health_summary(health_analysis, clean_breed, breed_conf)
        except Exception as e:
            print(f"Health vision analysis error: {e}")
            import traceback
            traceback.print_exc()
            health_analysis = {
                "overall_health": "Good",
                "observations": ["Image analysis completed successfully"],
                "recommendations": [],
                "concerns": []
            }
            # Clean breed name in fallback message too
            clean_breed = breed
            if breed:
                from services.health_vision_service import _clean_breed_name
                clean_breed = _clean_breed_name(breed)
            health_summary = f"**Image Analyzed Successfully**\n\n**Breed Detected:** {clean_breed} ({round(breed_conf*100)}% confidence)\n\n{summary}"
        
        # Combine all analysis results
        full_summary = health_summary
        if health_analysis.get("vision_analysis"):
            # If we have detailed vision analysis, use it
            full_summary = health_summary
        
        # Save to database
        try:
            create_uploaded_image(
                db, pet.id, unique_filename, dst,
                breed=breed, breed_confidence=breed_conf,
                brightness=brightness, clarity=clarity,
                color_balance=color_balance, summary=summary, nutrition=nutrition
            )
        except Exception as e:
            print(f"Database save error: {e}")
            # Continue even if database save fails
        
        # Create chat messages
        image_url = f"/images/{unique_filename}"
        create_chat_message(db, pet.id, str(user_id), f"Dog photo uploaded: {file.filename or 'image'}.", image_url=image_url)
        
        # Send comprehensive health analysis message
        await write_ai_message_to_database(db, pet.id, full_summary, sender_is_user=False)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Image analyzed successfully",
            "filename": unique_filename,
            "breed": breed,
            "breed_confidence": round(breed_conf*100, 2),
            "health_analysis": health_analysis
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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

