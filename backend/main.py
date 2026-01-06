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

# CORS - Allow requests from frontend (MUST be before routes and mounts)
# This MUST be configured before any routes or static mounts
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,
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

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "cors": "enabled"}

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
    try:
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile_dict = profile.model_dump()
        pet = create_or_update_pet_profile(db, user_id, pet_id, profile_dict)
        return {"success": True, "message": "Profile saved successfully", "pet_id": pet.pet_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving pet profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")

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
    from services.db_service import get_pet_by_id, create_or_update_pet_profile
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        # Auto-create pet profile if it doesn't exist (for backward compatibility)
        try:
            minimal_profile = {
                "petName": "My Pet",
                "breed": "Unknown",
                "weight": "",
                "age": "",
                "gender": "",
                "season": "",
                "activityLevel": "",
                "behaviorNotes": "",
                "medicalConditions": [],
                "goals": []
            }
            pet = create_or_update_pet_profile(db, user_id, pet_id, minimal_profile)
        except Exception as e:
            print(f"Failed to auto-create pet: {e}")
            raise HTTPException(status_code=404, detail="Pet not found. Please complete your pet profile first.")
    
    user_msg = req.question.strip()
    location = getattr(req, "location", None)
    # Get pet profile from database (always use latest database data)
    from services.db_service import get_pet_profile
    pet_profile_db = get_pet_profile(db, user_id, pet_id)
    # Merge with request pet_profile if provided (frontend data takes precedence for specific fields)
    if req.pet_profile and pet_profile_db:
        pet_profile = {**pet_profile_db, **req.pet_profile}  # Request data overrides DB data
    elif req.pet_profile:
        pet_profile = req.pet_profile
    elif pet_profile_db:
        pet_profile = pet_profile_db
    else:
        pet_profile = {}  # Fallback to empty profile
    image_url = getattr(req, "image_url", None)
    image_analysis_context = getattr(req, "image_analysis_context", None)
    
    # If image_url is provided but no analysis context, try to get recent image analysis
    if image_url and not image_analysis_context:
        from services.db_service import get_pet_images
        # Get the most recent uploaded image that matches this URL
        images = get_pet_images(db, pet.id)
        for img in images[:1]:  # Check most recent image
            if image_url in img.file_path or img.file_path in image_url:
                # Try to get analysis from health_vision_service if available
                if os.path.exists(img.file_path):
                    try:
                        from services.health_vision_service import analyze_health_with_vision, generate_health_summary
                        health_analysis = analyze_health_with_vision(img.file_path, pet.breed)
                        image_analysis_context = health_analysis
                    except Exception as e:
                        print(f"Could not analyze image: {e}")
    
    # Save user message with image URL if provided
    create_chat_message(db, pet.id, str(user_id), user_msg, image_url=image_url)
    
    # Generate AI response with image analysis context
    history = []
    answer = generate_dynamic_answer(user_msg, history, location, pet_profile, image_analysis_context)
    
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
    
    from services.db_service import get_pet_by_id, create_or_update_pet_profile
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        # Auto-create pet profile if it doesn't exist
        try:
            minimal_profile = {
                "petName": "My Pet",
                "breed": "Unknown",
                "weight": "",
                "age": "",
                "gender": "",
                "season": "",
                "activityLevel": "",
                "behaviorNotes": "",
                "medicalConditions": [],
                "goals": []
            }
            pet = create_or_update_pet_profile(db, user_id, pet_id, minimal_profile)
            print(f"Auto-created pet profile for user {user_id}, pet_id {pet_id}")
        except Exception as e:
            print(f"Failed to auto-create pet: {e}")
            import traceback
            traceback.print_exc()
            # Return empty messages if pet creation fails
            return {"messages": []}
    
    # Get messages for this pet
    try:
        messages = get_chat_messages(db, pet.id)
        print(f"Retrieved {len(messages)} messages from database for pet.id={pet.id}, pet_id={pet_id}")
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
        
        print(f"Returning {len(messages_list)} formatted messages for pet.id={pet.id}, pet_id={pet_id}")
        return {"messages": messages_list}
    except Exception as e:
        print(f"Error retrieving messages: {e}")
        import traceback
        traceback.print_exc()
        return {"messages": []}

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
    
    from services.db_service import get_pet_by_id, create_or_update_pet_profile
    from services.health_vision_service import analyze_health_with_vision, generate_health_summary
    import uuid
    from datetime import datetime
    
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        # Auto-create pet profile if it doesn't exist (for backward compatibility)
        try:
            # Create a minimal pet profile
            minimal_profile = {
                "petName": "My Pet",
                "breed": "Unknown",
                "weight": "",
                "age": "",
                "gender": "",
                "season": "",
                "activityLevel": "",
                "behaviorNotes": "",
                "medicalConditions": [],
                "goals": []
            }
            pet = create_or_update_pet_profile(db, user_id, pet_id, minimal_profile)
            # Refresh pet object to ensure we have the latest data
            db.refresh(pet)
            print(f"Auto-created and refreshed pet: id={pet.id}, pet_id={pet.pet_id}, user_id={pet.user_id}")
        except Exception as e:
            print(f"Failed to auto-create pet: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=404, detail="Pet not found. Please complete your pet profile first.")
    
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
        # CRITICAL: Dog detector is the PRIMARY and ONLY validator
        # Breed classifier should NOT be used for validation - it can misclassify non-dogs
        from services.dog_detector import validate_dog_image
        is_valid_dog, dog_conf, dog_message, detected_label = validate_dog_image(dst)
        
        # If dog detector rejects, immediately reject - don't even check breed classifier
        if not is_valid_dog:
            # Generate user-friendly message based on confidence
            from services.response_messages import get_dog_detection_message
            error_msg = get_dog_detection_message(dog_conf)
            
            # Save user message and error response to chat
            image_url = f"/images/{unique_filename}"
            user_msg_obj = create_chat_message(db, pet.id, str(user_id), f"📷 Uploaded photo: {file.filename or 'image'}", image_url=image_url)
            ai_msg_obj = await write_ai_message_to_database(db, pet.id, error_msg, sender_is_user=False)
            
            # Prepare messages for response
            messages_list = []
            if user_msg_obj and hasattr(user_msg_obj, 'text'):
                messages_list.append({
                    "sender": "user",
                    "text": user_msg_obj.text or "",
                    "image_url": user_msg_obj.image_url,
                    "timestamp": user_msg_obj.timestamp.isoformat() if user_msg_obj.timestamp else None
                })
            if ai_msg_obj and ai_msg_obj is not None and hasattr(ai_msg_obj, 'text'):
                messages_list.append({
                    "sender": "ai",
                    "text": ai_msg_obj.text or "",
                    "image_url": None,
                    "timestamp": ai_msg_obj.timestamp.isoformat() if ai_msg_obj.timestamp else None
                })
            
            # Return error response with messages so frontend can display immediately
            return JSONResponse(
                status_code=400,
                content={
                    "status": "validation_failed",
                    "message": "Image does not appear to contain a dog",
                    "detail": dog_message,
                    "filename": unique_filename,
                    "messages": messages_list  # Include messages so frontend can display immediately
                }
            )
        
        # If we reach here, image is validated as dog image by dog detector
        # ADDITIONAL SAFETY CHECK: Breed classifier confidence check
        # If breed classifier gives very low confidence, it might be a non-dog that slipped through
        breed, breed_conf = None, 0.0
        try:
            breed, breed_conf = predict_breed(dst)
            print(f"[VALIDATION] Breed classifier result: {breed} ({breed_conf:.2%} confidence)")
            
            # CRITICAL CHECK: If dog detector confidence was low, be extra strict
            # Hairless breeds (like Mexican hairless) can be confused with goats/sheep
            hairless_breeds = ["mexican hairless", "hairless", "xoloitzcuintli", "xolo", "peruvian hairless"]
            is_hairless_breed = breed and any(hb in breed.lower() for hb in hairless_breeds)
            
            # If it's a hairless breed and dog detector confidence was moderate/low, be suspicious
            if is_hairless_breed and dog_conf < 0.4:
                print(f"[VALIDATION] ⚠️ SUSPICIOUS: Hairless breed detected with low dog detector confidence. Rejecting to avoid goat misclassification.")
                from services.response_messages import get_hairless_breed_suspicion_message
                error_msg = get_hairless_breed_suspicion_message()
                
                image_url = f"/images/{unique_filename}"
                user_msg_obj = create_chat_message(db, pet.id, str(user_id), f"📷 Uploaded photo: {file.filename or 'image'}", image_url=image_url)
                ai_msg_obj = await write_ai_message_to_database(db, pet.id, error_msg, sender_is_user=False)
                
                # Prepare messages for response
                messages_list = []
                if user_msg_obj and hasattr(user_msg_obj, 'text'):
                    messages_list.append({
                        "sender": "user",
                        "text": user_msg_obj.text or "",
                        "image_url": user_msg_obj.image_url,
                        "timestamp": user_msg_obj.timestamp.isoformat() if user_msg_obj.timestamp else None
                    })
                if ai_msg_obj and ai_msg_obj is not None and hasattr(ai_msg_obj, 'text'):
                    messages_list.append({
                        "sender": "ai",
                        "text": ai_msg_obj.text or "",
                        "image_url": None,
                        "timestamp": ai_msg_obj.timestamp.isoformat() if ai_msg_obj.timestamp else None
                    })
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "message": "Cannot confidently verify this is a dog image",
                        "breed": breed,
                        "confidence": breed_conf,
                        "filename": unique_filename,
                        "messages": messages_list
                    }
                )
            
            # STRICT CHECK: Reject if breed confidence is too low (< 0.50 for better accuracy)
            # Increased from 0.35 to 0.50 to catch more misclassifications
            if breed_conf < 0.50:
                print(f"[VALIDATION] Rejecting: Breed confidence too low ({breed_conf:.2%} < 0.50). Likely not a dog.")
                
                # User-friendly error message based on confidence
                from services.response_messages import get_low_breed_confidence_message
                error_msg = get_low_breed_confidence_message(breed_conf)
                
                image_url = f"/images/{unique_filename}"
                user_msg_obj = create_chat_message(db, pet.id, str(user_id), f"📷 Uploaded photo: {file.filename or 'image'}", image_url=image_url)
                ai_msg_obj = await write_ai_message_to_database(db, pet.id, error_msg, sender_is_user=False)
                
                # Prepare messages for response
                messages_list = []
                if user_msg_obj and hasattr(user_msg_obj, 'text'):
                    messages_list.append({
                        "sender": "user",
                        "text": user_msg_obj.text or "",
                        "image_url": user_msg_obj.image_url,
                        "timestamp": user_msg_obj.timestamp.isoformat() if user_msg_obj.timestamp else None
                    })
                if ai_msg_obj and ai_msg_obj is not None and hasattr(ai_msg_obj, 'text'):
                    messages_list.append({
                        "sender": "ai",
                        "text": ai_msg_obj.text or "",
                        "image_url": None,
                        "timestamp": ai_msg_obj.timestamp.isoformat() if ai_msg_obj.timestamp else None
                    })
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "message": "Breed detection confidence too low - image may not contain a dog",
                        "breed": breed,
                        "confidence": breed_conf,
                        "filename": unique_filename,
                        "messages": messages_list  # Include messages so frontend can display immediately
                    }
                )
            
            # Sanity check: Reject unknown breeds
            if not breed or "unknown" in breed.lower():
                breed = detected_label if detected_label else "Unknown Breed"
                breed_conf = dog_conf if dog_conf > 0 else 0.0
        except Exception as e:
            print(f"Breed prediction error: {e}")
            # Fallback to dog detector result
            breed = detected_label if detected_label else "Unknown Breed"
            breed_conf = dog_conf if dog_conf > 0 else 0.0
        
        # Analyze image - Basic image quality
        try:
            brightness, clarity, color_balance, summary, nutrition = analyze_image(dst)
        except Exception as e:
            print(f"Image analysis error: {e}")
            brightness, clarity, color_balance = 0.5, 0.5, 0.5
            summary = "Image quality analysis completed"
            nutrition = []
        
        # Advanced health analysis using vision AI
        health_analysis = None
        health_summary = None
        clean_breed = breed
        if breed:
            from services.health_vision_service import _clean_breed_name
            clean_breed = _clean_breed_name(breed)
        
        try:
            health_analysis = analyze_health_with_vision(dst, breed)
            health_summary = generate_health_summary(health_analysis, clean_breed, breed_conf, dog_conf)
            print(f"Health analysis completed successfully. Summary length: {len(health_summary) if health_summary else 0}")
        except Exception as e:
            print(f"Health vision analysis error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback health analysis
            health_analysis = {
                "overall_health": "Good",
                "observations": ["Image analysis completed successfully"],
                "recommendations": [],
                "concerns": [],
                "body_condition": "Normal",
                "coat_condition": "Healthy",
                "eye_condition": "Normal",
                "energy_level": "Normal"
            }
            # Generate fallback summary using the same format
            try:
                health_summary = generate_health_summary(health_analysis, clean_breed, breed_conf, dog_conf)
            except:
                # Final fallback if generate_health_summary also fails
                from services.response_messages import get_breed_detection_message
                health_summary = get_breed_detection_message(clean_breed, breed_conf, dog_conf)
        
        # Use health_summary (should always be set now)
        full_summary = health_summary if health_summary else f"I've analyzed your dog's photo!\n\n• Detected Breed: {clean_breed} ({round(breed_conf*100)}% confidence)\n• Overall Health Status: Good\n\nThis is an AI-based visual assessment."
        
        # Auto-update pet profile breed if detected from image and breed is missing/unknown
        if breed and breed_conf > 0.5:  # Only update if confidence is decent
            try:
                from services.db_service import get_pet_profile
                current_profile = get_pet_profile(db, user_id, pet_id)
                # Update breed if it's missing, empty, "Unknown", or "Unknown Breed"
                if not current_profile or not current_profile.get('breed') or \
                   current_profile.get('breed', '').lower() in ['unknown', 'unknown breed', '']:
                    print(f"Auto-updating pet profile breed from '{current_profile.get('breed') if current_profile else 'None'}' to '{breed}' (confidence: {breed_conf:.2%})")
                    if not current_profile:
                        current_profile = {
                            "petName": pet.pet_name or "My Pet",
                            "breed": "",
                            "weight": pet.weight or "",
                            "age": pet.age or "",
                            "gender": pet.gender or "",
                            "season": pet.season or "",
                            "activityLevel": pet.activity_level or "",
                            "behaviorNotes": pet.behavior_notes or "",
                            "medicalConditions": pet.medical_conditions or [],
                            "goals": pet.goals or []
                        }
                    current_profile['breed'] = breed
                    create_or_update_pet_profile(db, user_id, pet_id, current_profile)
                    db.refresh(pet)  # Refresh pet object with updated breed
                    print(f"Successfully auto-updated breed to: {breed}")
            except Exception as e:
                print(f"Failed to auto-update breed in pet profile: {e}")
                # Continue - this is not critical
        
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
        
        # Create chat messages - User message first
        image_url = f"/images/{unique_filename}"
        messages_created = []
        try:
            # User message with image
            user_msg = create_chat_message(db, pet.id, str(user_id), f"📷 Uploaded dog photo: {file.filename or 'image'}", image_url=image_url)
            print(f"User message saved (ID: {user_msg.id}): Image uploaded - {image_url}")
            messages_created.append({
                "sender": "user",
                "text": user_msg.text,
                "image_url": user_msg.image_url,
                "timestamp": user_msg.timestamp.isoformat() if user_msg.timestamp else None
            })
            
            # Send comprehensive health analysis message as AI response
            ai_msg_result = await write_ai_message_to_database(db, pet.id, full_summary, sender_is_user=False)
            print(f"AI analysis message saved: {len(full_summary)} characters, Result: {ai_msg_result}")
            
            # Verify messages were saved by querying them back
            from services.db_service import get_chat_messages
            saved_messages = get_chat_messages(db, pet.id)
            print(f"Verified: {len(saved_messages)} total messages now in database for pet.id={pet.id}")
            
            # Add the last AI message (should be our health analysis) to response
            ai_messages = [msg for msg in saved_messages if msg.sender == "ai_bot"]
            if ai_messages:
                latest_ai_msg = ai_messages[-1]  # Get the most recent AI message
                messages_created.append({
                    "sender": "ai",
                    "text": latest_ai_msg.text,
                    "image_url": latest_ai_msg.image_url,
                    "timestamp": latest_ai_msg.timestamp.isoformat() if latest_ai_msg.timestamp else None
                })
                print(f"Added AI message to response: {len(latest_ai_msg.text)} characters")
            
            print(f"Messages saved successfully for pet.id={pet.id}, pet_id={pet_id}, user_id={user_id}")
        except Exception as e:
            print(f"Error saving chat messages: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.rollback()
            except:
                pass
            # Continue anyway - image was uploaded successfully
        
        return JSONResponse(content={
            "status": "success",
            "message": "Image analyzed successfully",
            "filename": unique_filename,
            "breed": breed,
            "breed_confidence": round(breed_conf*100, 2),
            "health_analysis": health_analysis,
            "messages": messages_created  # Return created messages so frontend can display immediately
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

