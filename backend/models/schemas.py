from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    pet_profile: Optional[Dict[str, Any]] = None

class ChatAnswer(BaseModel):
    answer: str
    matched_question: Optional[str] = None
    score: float

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