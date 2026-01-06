# database_models.py - SQLAlchemy Models for PostgreSQL

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")

class Pet(Base):
    __tablename__ = "pets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pet_id = Column(String, index=True, nullable=False)  # Custom pet ID like 'your_dog_buddy_id'
    
    # Composite unique constraint: pet_id should be unique per user
    __table_args__ = (
        UniqueConstraint('user_id', 'pet_id', name='uq_user_pet_id'),
    )
    
    # Profile data
    pet_name = Column(String)
    breed = Column(String)
    weight = Column(String)
    age = Column(String)
    gender = Column(String)
    season = Column(String)
    activity_level = Column(String)
    behavior_notes = Column(Text)
    medical_conditions = Column(JSON)  # Array stored as JSON
    goals = Column(JSON)  # Array stored as JSON
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="pets")
    chat_messages = relationship("ChatMessage", back_populates="pet", cascade="all, delete-orphan")
    uploaded_images = relationship("UploadedImage", back_populates="pet", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user_id' or 'ai_bot'
    text = Column(Text)
    image_url = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pet = relationship("Pet", back_populates="chat_messages")

class UploadedImage(Base):
    __tablename__ = "uploaded_images"
    
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    breed = Column(String)
    breed_confidence = Column(Float)
    brightness = Column(Float)
    clarity = Column(Float)
    color_balance = Column(JSON)
    summary = Column(Text)
    nutrition = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pet = relationship("Pet", back_populates="uploaded_images")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    analysis_result = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

