# intent_router.py - Lightweight Intent Router
"""
Lightweight intent router that runs BEFORE any AI or DB calls.
Detects input type to route requests efficiently.
"""

from typing import Literal
import re

# Intent types
IntentType = Literal["GREETING", "IMAGE_QUERY", "FAQ_QUESTION"]

# Greeting patterns (case-insensitive)
GREETING_PATTERNS = [
    r'^\s*(hi|hello|hey|namaste|namaskar|hii|hiii|hiiii)\s*[!.]*\s*$',
    r'^\s*(hi|hello|hey)\s+(there|everyone|guys|all|folks)\s*[!.]*\s*$',
    r'^\s*(good\s+)?(morning|afternoon|evening|night|day)\s*[!.]*\s*$',
    r'^\s*howdy\s*[!.]*\s*$',
    r'^\s*(what\'?s?\s+up|sup|wassup)\s*[!?.]*\s*$',
]

# Minimum length for FAQ questions (very short = likely greeting)
MIN_FAQ_LENGTH = 10
MAX_GREETING_LENGTH = 50  # If longer, likely not a greeting


def detect_intent(
    user_message: str,
    has_image: bool = False,
    min_faq_length: int = MIN_FAQ_LENGTH
) -> IntentType:
    """
    Detect user intent BEFORE any AI or DB calls.
    
    Args:
        user_message: User's input text (cleaned/stripped)
        has_image: Whether an image is attached
        min_faq_length: Minimum length to consider as FAQ question
    
    Returns:
        IntentType: "GREETING", "IMAGE_QUERY", or "FAQ_QUESTION"
    
    Logic:
    1. If image present → IMAGE_QUERY (route to image analysis)
    2. If very short text → GREETING (instant response)
    3. If matches greeting pattern → GREETING
    4. Otherwise → FAQ_QUESTION (route to FAQ search)
    """
    # Step 1: Image routing (highest priority)
    if has_image:
        return "IMAGE_QUERY"
    
    # Step 2: Clean and check message
    msg = user_message.strip()
    
    # Empty or whitespace only
    if not msg or not msg.strip():
        return "GREETING"  # Treat as greeting for safety
    
    # Step 3: Length-based detection (very short = greeting)
    if len(msg) < min_faq_length or len(msg) > MAX_GREETING_LENGTH:
        # Check if it matches greeting pattern
        msg_lower = msg.lower()
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, msg_lower, re.IGNORECASE):
                return "GREETING"
        
        # Very short but not a greeting pattern → still likely greeting
        if len(msg) < min_faq_length:
            return "GREETING"
    
    # Step 4: Pattern matching for greetings
    msg_lower = msg.lower()
    for pattern in GREETING_PATTERNS:
        if re.match(pattern, msg_lower, re.IGNORECASE):
            return "GREETING"
    
    # Step 5: Default to FAQ question
    return "FAQ_QUESTION"


def get_greeting_response(pet_name: str = None) -> str:
    """
    Return instant static greeting response.
    NO AI calls, NO embeddings, NO database queries.
    
    Args:
        pet_name: Optional pet name for personalization
    
    Returns:
        Friendly greeting message
    """
    if pet_name:
        return f"Hello! I'm here to help you with {pet_name}'s health and care. How can I assist you today?"
    else:
        return "Hello! I'm here to help you with your dog's health and care. How can I assist you today?"


def should_skip_ai_processing(user_message: str, has_image: bool = False) -> bool:
    """
    Quick check: Should we skip AI/DB processing?
    Returns True for greetings (instant response only).
    
    This is a performance optimization to avoid unnecessary API calls.
    """
    intent = detect_intent(user_message, has_image)
    return intent == "GREETING"

