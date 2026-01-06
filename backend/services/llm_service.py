# llm_service.py - LLM Service (PostgreSQL version, no Firebase)

from openai import OpenAI
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from typing import Optional
from services.db_service import create_chat_message
from datetime import datetime, timezone
import random

load_dotenv()

def generate_fallback_response(question: str, pet_profile: dict) -> str:
    """
    Generates a simple fallback response when OpenAI API is not available.
    This allows the app to work for testing without API key.
    """
    question_lower = question.lower()
    
    # Pet profile context
    pet_name = pet_profile.get('petName', 'your dog') if pet_profile else 'your dog'
    breed = pet_profile.get('breed', '') if pet_profile else ''
    
    # Greeting responses
    if any(word in question_lower for word in ['hi', 'hello', 'hey', 'namaste']):
        return f"Hello! I'm here to help you with {pet_name}'s health and care. How can I assist you today?"
    
    # Health questions
    if any(word in question_lower for word in ['health', 'sick', 'ill', 'problem', 'issue']):
        return f"Regarding {pet_name}'s health, I recommend:\n\n1. Regular vet checkups every 6-12 months\n2. Monitor eating and drinking habits\n3. Watch for changes in behavior\n4. Keep vaccinations up to date\n\nIf you notice any concerning symptoms, please consult with a veterinarian immediately."
    
    # Nutrition questions
    if any(word in question_lower for word in ['food', 'diet', 'eat', 'nutrition', 'meal', 'feed']):
        breed_info = f" For {breed} breeds," if breed else ""
        return f"Nutrition advice for {pet_name}:{breed_info}\n\n1. Feed high-quality dog food appropriate for their age and size\n2. Follow feeding guidelines on the food package\n3. Provide fresh water at all times\n4. Avoid human foods that can be toxic (chocolate, grapes, onions, etc.)\n5. Consider your dog's activity level when determining portion sizes\n\nFor specific nutritional needs, use the Nutrient Calculator feature in the app."
    
    # Exercise questions
    if any(word in question_lower for word in ['exercise', 'walk', 'play', 'activity', 'fitness']):
        activity = pet_profile.get('activityLevel', 'Moderate') if pet_profile else 'Moderate'
        return f"Exercise recommendations for {pet_name}:\n\n1. Daily walks (30-60 minutes depending on breed and age)\n2. Playtime and interactive games\n3. Mental stimulation through training or puzzle toys\n4. Adjust activity based on weather and your dog's {activity.lower()} activity level\n5. Watch for signs of fatigue or overheating"
    
    # Behavior questions
    if any(word in question_lower for word in ['behavior', 'behave', 'training', 'train', 'obey']):
        return f"Behavior and training tips for {pet_name}:\n\n1. Positive reinforcement works best\n2. Be consistent with commands and rules\n3. Socialize your dog from an early age\n4. Provide mental stimulation to prevent boredom\n5. Consider professional training if needed\n\nRemember, patience and consistency are key to successful training."
    
    # General care
    if any(word in question_lower for word in ['care', 'grooming', 'bath', 'clean']):
        return f"General care tips for {pet_name}:\n\n1. Regular grooming based on coat type\n2. Brush teeth regularly to prevent dental issues\n3. Trim nails when needed\n4. Check ears for signs of infection\n5. Keep living area clean and comfortable\n6. Provide a safe and secure environment"
    
    # Default response
    responses = [
        f"Thank you for your question about {pet_name}. I'm here to help with dog health and care advice. Could you provide more details about what you'd like to know?",
        f"That's a great question! For {pet_name}, I'd recommend consulting the specific features in this app:\n\n- Use the Chat feature for detailed health questions\n- Check the Dashboard for your pet's profile\n- Use Nutrient Calculator for dietary needs\n\nFeel free to ask more specific questions!",
        f"I understand you're asking about {pet_name}. For the best advice, please:\n\n1. Ensure your pet's profile is complete\n2. Use specific questions (e.g., 'What should I feed my dog?')\n3. Check the Reports section for previous health information\n\nHow else can I help you today?"
    ]
    
    return random.choice(responses)

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client only if API key is set
if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    print("WARNING: OpenAI API key not set. AI responses will not work.")

async def write_ai_message_to_database(
    db: Session,
    pet_id: int,
    content: str | dict,
    sender_is_user: bool = False,
    user_id: Optional[str] = None
):
    """
    Writes a message to the database.
    'content' can be a string (AI message) or a dict (User upload message with image_url).
    """
    sender_id = str(user_id) if sender_is_user and user_id else "ai_bot"
    
    if isinstance(content, dict):
        text = content.get("text", "")
        image_url = content.get("image_url")
        create_chat_message(db, pet_id, sender_id, text, image_url=image_url)
    elif isinstance(content, str):
        create_chat_message(db, pet_id, sender_id, content)
    else:
        print(f"Warning: Invalid content type ({type(content)}) for database message.")
        return False
    
    return True

def check_faq_match(question: str, pet_profile: dict) -> Optional[str]:
    """
    Check if the question matches common FAQ patterns and return appropriate response.
    Uses the same logic as generate_fallback_response but returns early if match found.
    Returns None if no match found, otherwise returns the response.
    """
    question_lower = question.lower().strip()
    
    # Pet profile context
    pet_name = pet_profile.get('petName', 'your dog') if pet_profile else 'your dog'
    breed = pet_profile.get('breed', '') if pet_profile else ''
    activity = pet_profile.get('activityLevel', 'Moderate') if pet_profile else 'Moderate'
    
    # Use the same patterns as generate_fallback_response
    # Greeting responses
    if any(word in question_lower for word in ['hi', 'hello', 'hey', 'namaste']):
        return f"Hello! I'm here to help you with {pet_name}'s health and care. How can I assist you today?"
    
    # Health questions
    if any(word in question_lower for word in ['health', 'sick', 'ill', 'problem', 'issue']):
        return f"Regarding {pet_name}'s health, I recommend:\n\n1. Regular vet checkups every 6-12 months\n2. Monitor eating and drinking habits\n3. Watch for changes in behavior\n4. Keep vaccinations up to date\n\nIf you notice any concerning symptoms, please consult with a veterinarian immediately."
    
    # Nutrition questions
    if any(word in question_lower for word in ['food', 'diet', 'eat', 'nutrition', 'meal', 'feed']):
        breed_info = f" For {breed} breeds," if breed else ""
        return f"Nutrition advice for {pet_name}:{breed_info}\n\n1. Feed high-quality dog food appropriate for their age and size\n2. Follow feeding guidelines on the food package\n3. Provide fresh water at all times\n4. Avoid human foods that can be toxic (chocolate, grapes, onions, etc.)\n5. Consider your dog's activity level when determining portion sizes\n\nFor specific nutritional needs, use the Nutrient Calculator feature in the app."
    
    # Exercise questions
    if any(word in question_lower for word in ['exercise', 'walk', 'play', 'activity', 'fitness']):
        return f"Exercise recommendations for {pet_name}:\n\n1. Daily walks (30-60 minutes depending on breed and age)\n2. Playtime and interactive games\n3. Mental stimulation through training or puzzle toys\n4. Adjust activity based on weather and your dog's {activity.lower()} activity level\n5. Watch for signs of fatigue or overheating"
    
    # Behavior questions
    if any(word in question_lower for word in ['behavior', 'behave', 'training', 'train', 'obey']):
        return f"Behavior and training tips for {pet_name}:\n\n1. Positive reinforcement works best\n2. Be consistent with commands and rules\n3. Socialize your dog from an early age\n4. Provide mental stimulation to prevent boredom\n5. Consider professional training if needed\n\nRemember, patience and consistency are key to successful training."
    
    # General care
    if any(word in question_lower for word in ['care', 'grooming', 'bath', 'clean']):
        return f"General care tips for {pet_name}:\n\n1. Regular grooming based on coat type\n2. Brush teeth regularly to prevent dental issues\n3. Trim nails when needed\n4. Check ears for signs of infection\n5. Keep living area clean and comfortable\n6. Provide a safe and secure environment"
    
    # If no match found, return None to proceed to OpenAI
    return None

def generate_dynamic_answer(question: str, history: list, location: Optional[str], pet_profile: dict, image_analysis_context: Optional[dict] = None) -> str:
    """
    Generates an AI response using OpenAI based on the question and pet profile.
    First checks FAQ, then uses OpenAI if no match found.
    """
    # Step 1: Check FAQ first
    faq_response = check_faq_match(question, pet_profile)
    if faq_response:
        print(f"FAQ match found for question: {question[:50]}...")
        return faq_response
    
    # Step 2: If no FAQ match and OpenAI client is not available, use fallback
    if client is None:
        print(f"No FAQ match and OpenAI not available, using fallback response")
        return generate_fallback_response(question, pet_profile)
    
    # Step 3: Use OpenAI for complex questions not in FAQ
    try:
        # Build context from pet profile
        profile_context = ""
        if pet_profile:
            profile_context = f"""
Pet Profile:
- Name: {pet_profile.get('petName', 'Unknown')}
- Breed: {pet_profile.get('breed', 'Unknown')}
- Age: {pet_profile.get('age', 'Unknown')}
- Weight: {pet_profile.get('weight', 'Unknown')}
- Gender: {pet_profile.get('gender', 'Unknown')}
- Activity Level: {pet_profile.get('activityLevel', 'Unknown')}
- Medical Conditions: {', '.join(pet_profile.get('medicalConditions', []))}
- Goals: {', '.join(pet_profile.get('goals', []))}
"""
        
        location_context = f"\nLocation: {location}" if location else ""
        
        # Add image analysis context if available
        image_context = ""
        if image_analysis_context:
            image_context = f"""
Recent Image Analysis:
- Overall Health: {image_analysis_context.get('overall_health', 'Unknown')}
- Body Condition: {image_analysis_context.get('body_condition', 'Unknown')}
- Coat Condition: {image_analysis_context.get('coat_condition', 'Unknown')}
- Eye Condition: {image_analysis_context.get('eye_condition', 'Unknown')}
- Energy Level: {image_analysis_context.get('energy_level', 'Unknown')}
- Observations: {', '.join(image_analysis_context.get('observations', [])) if isinstance(image_analysis_context.get('observations'), list) else str(image_analysis_context.get('observations', ''))}
- Concerns: {', '.join(image_analysis_context.get('concerns', [])) if isinstance(image_analysis_context.get('concerns'), list) else ''}
- Recommendations: {', '.join(image_analysis_context.get('recommendations', [])) if isinstance(image_analysis_context.get('recommendations'), list) else ''}
"""
            if image_analysis_context.get('vision_analysis'):
                image_context += f"\nDetailed Vision Analysis: {image_analysis_context.get('vision_analysis')}\n"
        
        system_prompt = f"""You are a helpful AI assistant specialized in dog health and care. 
You provide expert advice on dog nutrition, health, behavior, and general care.
{profile_context}{location_context}{image_context}

Provide helpful, accurate, and caring responses about dog health and wellness.
When image analysis is provided, incorporate those observations into your response."""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history if available
        for msg in history[-5:]:  # Last 5 messages for context
            messages.append({"role": "user", "content": msg.get("question", "")})
            messages.append({"role": "assistant", "content": msg.get("answer", "")})
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_str = str(e)
        print(f"Error generating AI response: {e}")
        
        # Check for specific error types
        if "insufficient_quota" in error_str or "429" in error_str:
            return "⚠️ Your OpenAI API quota has been exceeded. Please add credits to your OpenAI account at https://platform.openai.com/account/billing. Until then, I'll provide helpful responses based on your pet's profile."
        elif "invalid_api_key" in error_str or "401" in error_str:
            return "⚠️ OpenAI API key is invalid. Please check your API key in the .env file."
        else:
            # Fallback to intelligent responses when API fails
            return generate_fallback_response(question, pet_profile)

