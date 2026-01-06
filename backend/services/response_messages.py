# response_messages.py - User-friendly, trust-building AI response messages with anti-repetition

# Message type constants for tracking
LOW_CONFIDENCE_WARNING = "LOW_CONFIDENCE_WARNING"
MEDIUM_CONFIDENCE_GUIDANCE = "MEDIUM_CONFIDENCE_GUIDANCE"
SUCCESS_CONFIRMATION = "SUCCESS_CONFIRMATION"
NON_DOG_MESSAGE = "NON_DOG_MESSAGE"


def _detect_message_type(text: str) -> str:
    """
    Detect message type from AI response text for repetition tracking.
    """
    text_lower = text.lower()
    
    if "couldn't confidently analyze" in text_lower or "couldn't clearly recognize" in text_lower:
        return LOW_CONFIDENCE_WARNING
    elif "might need a clearer photo" in text_lower or "can see something that might be" in text_lower:
        return MEDIUM_CONFIDENCE_GUIDANCE
    elif "detected successfully" in text_lower or "breed identified" in text_lower:
        return SUCCESS_CONFIRMATION
    elif "couldn't clearly recognize a dog" in text_lower:
        return NON_DOG_MESSAGE
    else:
        return LOW_CONFIDENCE_WARNING  # Default


def _count_recent_message_type(messages: list, message_type: str, lookback: int = 3) -> int:
    """
    Count how many times the same message type appeared in recent AI messages.
    
    Args:
        messages: List of recent chat messages (should be AI messages only)
        message_type: Message type to count
        lookback: Number of recent messages to check
    
    Returns:
        Count of consecutive occurrences (0, 1, 2, 3+)
    """
    if not messages:
        return 0
    
    # Get last N AI messages (reverse order, most recent first)
    ai_messages = [msg for msg in messages if msg.get('sender') == 'ai' or 'ai' in str(msg.get('sender', '')).lower()][-lookback:]
    
    if not ai_messages:
        return 0
    
    count = 0
    # Count backwards from most recent
    for msg in reversed(ai_messages):
        msg_text = msg.get('text', '') or ''
        if _detect_message_type(msg_text) == message_type:
            count += 1
        else:
            break  # Stop counting if type changes
    
    return count


def get_dog_detection_message(dog_conf: float, recent_messages: list = None) -> str:
    """
    Generate user-friendly message based on dog detection confidence.
    Never blames user or image. AI takes responsibility.
    Adaptive length based on repetition.
    
    Args:
        dog_conf: Confidence score from dog detector (0.0 to 1.0)
        recent_messages: List of recent chat messages for repetition tracking
    
    Returns:
        Friendly, supportive message (adaptive length)
    """
    recent_messages = recent_messages or []
    
    # 🔴 Confidence < 30%: Very unclear image
    if dog_conf < 0.30:
        message_type = LOW_CONFIDENCE_WARNING
        repetition_count = _count_recent_message_type(recent_messages, message_type)
        
        if repetition_count == 0:
            # First occurrence - full message
            return (
                "⚠️ I couldn't confidently analyze this image yet.\n\n"
                "The photo appears to be a close-up or partial view, so I wasn't able to clearly recognize your dog.\n\n"
                "👉 Please upload a clear photo where your dog's face or body is visible."
            )
        elif repetition_count == 1:
            # Second occurrence - shorter
            return (
                "I still need one clear photo of your dog to continue the analysis."
            )
        else:
            # Third+ occurrence - ultra-short
            return "Please upload a clear photo of your dog."
    
    # 🟡 Confidence 30-60%: Possible dog but unclear
    elif dog_conf < 0.60:
        message_type = MEDIUM_CONFIDENCE_GUIDANCE
        repetition_count = _count_recent_message_type(recent_messages, message_type)
        
        if repetition_count == 0:
            return (
                "🐾 I can see something that might be your dog, but I need a clearer image to be sure.\n\n"
                "For best results:\n"
                "• Upload one clear photo of your dog\n"
                "• Then upload a close-up of the specific area you're concerned about"
            )
        else:
            # Shorter on repetition
            return (
                "I need a clearer photo of your dog to continue."
            )
    
    # 🟢 Confidence > 60%: Should not reach here (would proceed normally)
    else:
        return (
            "✅ I can see your dog!\n\n"
            "I'm processing the image now to identify the breed and provide insights."
        )


def get_breed_detection_message(breed: str, breed_conf: float, dog_conf: float = None, recent_messages: list = None) -> str:
    """
    Generate user-friendly breed detection message.
    Hides confidence below 60%.
    
    Args:
        breed: Detected breed name
        breed_conf: Breed classification confidence (0.0 to 1.0)
        dog_conf: Original dog detection confidence (optional)
        recent_messages: List of recent chat messages for repetition tracking
    
    Returns:
        Friendly breed identification message
    """
    recent_messages = recent_messages or []
    clean_breed = breed
    if breed:
        # Remove ImageNet class prefix if present
        parts = breed.split(' ', 1)
        if len(parts) > 1 and parts[0].startswith('n') and parts[0][1:].isdigit():
            clean_breed = parts[1]
    
    breed_pct = round(breed_conf * 100) if breed_conf > 0 else 0
    
    # 🟢 High confidence - show percentage
    if breed_pct >= 60:
        return (
            "✅ Dog detected successfully!\n\n"
            f"🐶 **Breed identified:** {clean_breed} ({breed_pct}% confidence)\n\n"
            "You can now upload a photo of any skin or health concern, and I'll take a closer look."
        )
    # 🟡 Medium confidence - hide percentage, shorter message
    elif breed_pct >= 30:
        return (
            "✅ I can see your dog!\n\n"
            f"🐶 **Possible breed:** {clean_breed}\n\n"
            "For more accurate breed identification, try uploading a clearer photo where your dog's full body or face is visible."
        )
    # 🔴 Low confidence - no percentage, guidance message
    else:
        message_type = LOW_CONFIDENCE_WARNING
        repetition_count = _count_recent_message_type(recent_messages, message_type)
        
        if repetition_count == 0:
            return (
                "✅ I can see your dog!\n\n"
                "However, I couldn't identify the breed with high confidence from this photo.\n\n"
                "👉 Please upload a clearer photo where your dog's full body or face is visible."
            )
        elif repetition_count == 1:
            return "I still need a clearer photo of your dog to identify the breed."
        else:
            return "Please upload a clear photo of your dog."


def get_hairless_breed_suspicion_message(recent_messages: list = None) -> str:
    """
    Message when hairless breed is detected but confidence is low (possible goat/sheep).
    Adaptive length based on repetition.
    """
    recent_messages = recent_messages or []
    message_type = LOW_CONFIDENCE_WARNING
    repetition_count = _count_recent_message_type(recent_messages, message_type)
    
    if repetition_count == 0:
        return (
            "⚠️ I couldn't confidently analyze this image yet.\n\n"
            "The photo appears to be unclear or shows only a partial view.\n\n"
            "👉 Please upload a clear photo where your dog's face or body is visible."
        )
    elif repetition_count == 1:
        return "I still need one clear photo of your dog to continue the analysis."
    else:
        return "Please upload a clear photo of your dog."


def get_low_breed_confidence_message(breed_conf: float, recent_messages: list = None) -> str:
    """
    Message when breed is detected but confidence is too low (< 50%).
    Hides confidence percentage. Adaptive length.
    """
    recent_messages = recent_messages or []
    
    if breed_conf < 0.30:
        message_type = LOW_CONFIDENCE_WARNING
        repetition_count = _count_recent_message_type(recent_messages, message_type)
        
        if repetition_count == 0:
            return (
                "⚠️ I couldn't confidently analyze this image yet.\n\n"
                "The photo appears to be a close-up or partial view, so I wasn't able to clearly recognize your dog.\n\n"
                "👉 Please upload a clear photo where your dog's face or body is visible."
            )
        elif repetition_count == 1:
            return "I still need one clear photo of your dog to continue the analysis."
        else:
            return "Please upload a clear photo of your dog."
    else:
        message_type = MEDIUM_CONFIDENCE_GUIDANCE
        repetition_count = _count_recent_message_type(recent_messages, message_type)
        
        if repetition_count == 0:
            return (
                "🐾 I can see something that might be your dog, but I need a clearer image to be sure.\n\n"
                "For best results:\n"
                "• Upload one clear photo of your dog\n"
                "• Then upload a close-up of the specific area you're concerned about"
            )
        else:
            return "I need a clearer photo of your dog to continue."


def get_non_dog_message(recent_messages: list = None) -> str:
    """
    Message for non-dog images (goat, wolf, objects, etc.).
    Never mentions detected object name. Adaptive length.
    """
    recent_messages = recent_messages or []
    message_type = NON_DOG_MESSAGE
    repetition_count = _count_recent_message_type(recent_messages, message_type)
    
    if repetition_count == 0:
        return (
            "I couldn't clearly recognize a dog in this image yet.\n\n"
            "This tool works best with clear photos of dogs. Please upload a photo of your dog to continue."
        )
    elif repetition_count == 1:
        return "I need a photo of your dog to continue. Please upload a clear photo of your dog."
    else:
        return "Please upload a photo of your dog."

