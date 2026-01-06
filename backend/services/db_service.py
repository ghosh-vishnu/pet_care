# db_service.py - PostgreSQL Database Service

from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.database_models import Pet
from models.database_models import User, Pet, ChatMessage, UploadedImage, Report
from typing import Optional, List, Dict
from datetime import datetime

# User operations
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password_hash: str) -> User:
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

# Pet operations
def get_pet_by_id(db: Session, user_id: int, pet_id: str) -> Optional[Pet]:
    return db.query(Pet).filter(
        and_(Pet.user_id == user_id, Pet.pet_id == pet_id)
    ).first()

def get_pet_profile(db: Session, user_id: int, pet_id: str) -> Optional[Dict]:
    pet = get_pet_by_id(db, user_id, pet_id)
    if not pet:
        return None
    
    # Return profile data even if some fields are missing
    # The frontend will handle displaying "Not specified" for empty fields
    return {
        "petName": pet.pet_name or "",
        "breed": pet.breed or "",
        "weight": pet.weight or "",
        "age": pet.age or "",
        "gender": pet.gender or "",
        "season": pet.season or "",
        "activityLevel": pet.activity_level or "",
        "behaviorNotes": pet.behavior_notes or "",
        "medicalConditions": pet.medical_conditions or [],
        "goals": pet.goals or []
    }

def create_or_update_pet_profile(db: Session, user_id: int, pet_id: str, profile_data: Dict) -> Pet:
    try:
        pet = get_pet_by_id(db, user_id, pet_id)
        
        if pet:
            # Update existing pet
            pet.pet_name = profile_data.get("petName")
            pet.breed = profile_data.get("breed")
            pet.weight = profile_data.get("weight")
            pet.age = profile_data.get("age")
            pet.gender = profile_data.get("gender")
            pet.season = profile_data.get("season")
            pet.activity_level = profile_data.get("activityLevel")
            pet.behavior_notes = profile_data.get("behaviorNotes")
            pet.medical_conditions = profile_data.get("medicalConditions", [])
            pet.goals = profile_data.get("goals", [])
        else:
            # Check if pet_id exists for another user (shouldn't happen with new constraint, but handle gracefully)
            existing_pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
            if existing_pet and existing_pet.user_id != user_id:
                # Pet ID exists for different user - this shouldn't happen with proper constraint
                # But if it does, we'll create with a modified pet_id
                import uuid
                pet_id = f"{pet_id}_{uuid.uuid4().hex[:8]}"
            
            # Create new pet
            pet = Pet(
                user_id=user_id,
                pet_id=pet_id,
                pet_name=profile_data.get("petName"),
                breed=profile_data.get("breed"),
                weight=profile_data.get("weight"),
                age=profile_data.get("age"),
                gender=profile_data.get("gender"),
                season=profile_data.get("season"),
                activity_level=profile_data.get("activityLevel"),
                behavior_notes=profile_data.get("behaviorNotes"),
                medical_conditions=profile_data.get("medicalConditions", []),
                goals=profile_data.get("goals", [])
            )
            db.add(pet)
        
        db.commit()
        db.refresh(pet)
        return pet
    except Exception as e:
        db.rollback()
        raise

# Chat message operations
def create_chat_message(db: Session, pet_id: int, sender: str, text: str, image_url: Optional[str] = None) -> ChatMessage:
    message = ChatMessage(
        pet_id=pet_id,
        sender=sender,
        text=text,
        image_url=image_url
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_chat_messages(db: Session, pet_id: int, limit: int = 100) -> List[ChatMessage]:
    return db.query(ChatMessage).filter(
        ChatMessage.pet_id == pet_id
    ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()

# Image operations
def create_uploaded_image(db: Session, pet_id: int, filename: str, file_path: str, 
                         breed: Optional[str] = None, breed_confidence: Optional[float] = None,
                         brightness: Optional[float] = None, clarity: Optional[float] = None,
                         color_balance: Optional[Dict] = None, summary: Optional[str] = None,
                         nutrition: Optional[str] = None) -> UploadedImage:
    image = UploadedImage(
        pet_id=pet_id,
        filename=filename,
        file_path=file_path,
        breed=breed,
        breed_confidence=breed_confidence,
        brightness=brightness,
        clarity=clarity,
        color_balance=color_balance,
        summary=summary,
        nutrition=nutrition
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image

def get_pet_images(db: Session, pet_id: int) -> List[UploadedImage]:
    return db.query(UploadedImage).filter(
        UploadedImage.pet_id == pet_id
    ).order_by(UploadedImage.uploaded_at.desc()).all()

# Report operations
def create_report(db: Session, user_id: int, pet_id: int, filename: str, 
                 file_path: str, analysis_result: Optional[str] = None) -> Report:
    report = Report(
        user_id=user_id,
        pet_id=pet_id,
        filename=filename,
        file_path=file_path,
        analysis_result=analysis_result
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_pet_reports(db: Session, pet_id: int) -> List[Report]:
    return db.query(Report).filter(
        Report.pet_id == pet_id
    ).order_by(Report.created_at.desc()).all()

