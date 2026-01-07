from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    pet_profile: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None  # URL to previously uploaded image for context
    image_analysis_context: Optional[Dict[str, Any]] = None  # Pre-analyzed image data

class ChatAnswer(BaseModel):
    answer: str
    matched_question: Optional[str] = None
    score: float
    source: Optional[str] = "gpt"  # "faq" or "gpt"
    confidence: Optional[str] = "medium"  # "high", "medium", "low", "none"

class ImageAnalysis(BaseModel):
    image_id: str
    breed: str
    breed_confidence: float
    brightness: float
    clarity: float
    color_balance: float
    summary: str
    nutrition_tips: List[str]

class ReportCreateRequest(BaseModel):
    image_id: Optional[str] = None
    last_n_messages: int = 5

class ReportInfo(BaseModel):
    report_id: str
    url: str