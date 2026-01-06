# response_messages.py - User-friendly, trust-building AI response messages

def get_dog_detection_message(dog_conf: float) -> str:
    """
    Generate user-friendly message based on dog detection confidence.
    Never blames user or image. AI takes responsibility.
    
    Args:
        dog_conf: Confidence score from dog detector (0.0 to 1.0)
    
    Returns:
        Friendly, supportive message
    """
    confidence_pct = round(dog_conf * 100, 1)
    
    # 🔴 Confidence < 30%: Very unclear image
    if dog_conf < 0.30:
        return (
            "⚠️ I couldn't confidently analyze this image yet.\n\n"
            "The photo appears to be a very close-up or partial view, so I wasn't able to clearly recognize your dog this time.\n\n"
            "👉 Please try uploading:\n"
            "• A photo where your dog's body or face is visible\n"
            "• Good lighting\n"
            "• Minimal blur or extreme zoom\n\n"
            "Once I can clearly see your dog, I'll be happy to provide insights."
        )
    
    # 🟡 Confidence 30-60%: Possible dog but unclear
    elif dog_conf < 0.60:
        return (
            "🐾 I might need a clearer photo to continue.\n\n"
            "I can see something that might be your dog, but I couldn't fully confirm with high confidence.\n\n"
            "For best results:\n"
            "• Upload one clear photo of your dog\n"
            "• Then upload a close-up of any specific area you'd like me to look at\n\n"
            "This helps me give more accurate and helpful insights."
        )
    
    # 🟢 Confidence > 60%: Should not reach here (would proceed normally)
    else:
        return (
            "✅ I can see your dog!\n\n"
            "I'm processing the image now to identify the breed and provide insights."
        )


def get_breed_detection_message(breed: str, breed_conf: float, dog_conf: float = None) -> str:
    """
    Generate user-friendly breed detection message.
    
    Args:
        breed: Detected breed name
        breed_conf: Breed classification confidence (0.0 to 1.0)
        dog_conf: Original dog detection confidence (optional)
    
    Returns:
        Friendly breed identification message
    """
    clean_breed = breed
    if breed:
        # Remove ImageNet class prefix if present
        parts = breed.split(' ', 1)
        if len(parts) > 1 and parts[0].startswith('n') and parts[0][1:].isdigit():
            clean_breed = parts[1]
    
    breed_pct = round(breed_conf * 100) if breed_conf > 0 else 0
    
    if breed_pct >= 60:
        return (
            "✅ Dog detected successfully!\n\n"
            f"🐶 **Breed identified:** {clean_breed} ({breed_pct}% confidence)\n\n"
            "You can now upload a photo of any skin or health concern, and I'll take a closer look."
        )
    elif breed_pct >= 30:
        return (
            "✅ I can see your dog!\n\n"
            f"🐶 **Possible breed:** {clean_breed} ({breed_pct}% confidence)\n\n"
            "For more accurate breed identification, try uploading a clearer photo where your dog's full body or face is visible."
        )
    else:
        return (
            "✅ I can see your dog!\n\n"
            "However, I couldn't identify the breed with high confidence from this photo.\n\n"
            "👉 For better results, please upload:\n"
            "• A clearer photo with good lighting\n"
            "• Your dog's full body or face visible\n\n"
            "Once I can see your dog more clearly, I'll be able to identify the breed."
        )


def get_hairless_breed_suspicion_message() -> str:
    """
    Message when hairless breed is detected but confidence is low (possible goat/sheep).
    """
    return (
        "⚠️ I couldn't confidently analyze this image yet.\n\n"
        "The photo appears to be unclear or shows only a partial view. I wasn't able to confidently verify this is a dog.\n\n"
        "👉 Please try uploading:\n"
        "• A clear, full photo of your dog\n"
        "• Good lighting\n"
        "• Your dog's full body or face visible\n\n"
        "Once I can clearly see your dog, I'll be happy to help with breed identification and health insights."
    )


def get_low_breed_confidence_message(breed_conf: float) -> str:
    """
    Message when breed is detected but confidence is too low (< 50%).
    """
    breed_pct = round(breed_conf * 100, 1)
    
    if breed_conf < 0.30:
        return (
            "⚠️ I couldn't confidently analyze this image yet.\n\n"
            "The photo appears to be a very close-up or partial view, so I wasn't able to clearly recognize your dog this time.\n\n"
            "👉 Please try uploading:\n"
            "• A photo where your dog's body or face is visible\n"
            "• Good lighting\n"
            "• Minimal blur or extreme zoom\n\n"
            "Once I can clearly see your dog, I'll be happy to provide insights."
        )
    else:
        return (
            "🐾 I might need a clearer photo to continue.\n\n"
            f"I can see something that might be your dog, but the image quality makes it difficult to identify with confidence (detected at {breed_pct}% confidence).\n\n"
            "For best results:\n"
            "• Upload one clear photo of your dog\n"
            "• Then upload a close-up of any specific area you'd like me to look at\n\n"
            "This helps me give more accurate and helpful insights."
        )

