# database_models.py - SQLAlchemy Models for PostgreSQL

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, UniqueConstraint, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Try to import pgvector, fallback if not available
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Create a placeholder Vector class for when pgvector is not installed
    from sqlalchemy import TypeDecorator
    class Vector(TypeDecorator):
        impl = ARRAY(Float)
        cache_ok = True

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

class FAQ(Base):
    """
    FAQ table with vector embeddings for semantic search.
    Uses pgvector for fast similarity search in PostgreSQL.
    """
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, unique=True)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True, index=True)
    embedding = Column(Vector(1536), nullable=True) if PGVECTOR_AVAILABLE else Column(ARRAY(Float), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, question={self.question[:50]}...)>"

