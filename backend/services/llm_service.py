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
    Returns the created ChatMessage object.
    """
    from services.db_service import create_chat_message
    
    sender_id = str(user_id) if sender_is_user and user_id else "ai_bot"
    
    if isinstance(content, dict):
        text = content.get("text", "")
        image_url = content.get("image_url")
        message = create_chat_message(db, pet_id, sender_id, text, image_url=image_url)
    elif isinstance(content, str):
        message = create_chat_message(db, pet_id, sender_id, content)
    else:
        print(f"Warning: Invalid content type ({type(content)}) for database message.")
        return None
    
    return message

def get_breed_specific_advice(breed: str, category: str) -> str:
    """
    Get breed-specific advice for common dog breeds.
    Returns empty string if no specific advice available.
    """
    if not breed:
        return ""
    
    breed_lower = breed.lower()
    
    # Breed-specific nutrition advice
    if category == "nutrition":
        if "labrador" in breed_lower or "retriever" in breed_lower:
            return "Labradors/Retrievers tend to gain weight easily, so portion control is important. They benefit from high-protein, low-fat diets."
        elif "poodle" in breed_lower:
            return "Poodles do well on high-quality protein and omega-3 fatty acids for their curly coat health."
        elif "beagle" in breed_lower:
            return "Beagles are food-motivated and prone to overeating. Use measured portions and consider puzzle feeders."
        elif "bulldog" in breed_lower or "pug" in breed_lower:
            return "Brachycephalic breeds (flat-faced) may need smaller kibble and should eat slowly to prevent choking."
        elif "husky" in breed_lower or "malamute" in breed_lower:
            return "Northern breeds have high energy needs. Feed high-quality, high-protein food suitable for active dogs."
        elif "chihuahua" in breed_lower:
            return "Small breeds like Chihuahuas need nutrient-dense food in smaller portions. Consider small-breed formulas."
        elif "great dane" in breed_lower or "mastiff" in breed_lower:
            return "Large/giant breeds need controlled growth diets to prevent joint issues. Look for large-breed puppy formulas if young."
    
    # Breed-specific exercise advice
    elif category == "exercise":
        if "labrador" in breed_lower or "retriever" in breed_lower:
            return "These active breeds need 60-90 minutes of exercise daily, including swimming and fetch."
        elif "husky" in breed_lower or "malamute" in breed_lower:
            return "Northern breeds require extensive exercise (90+ minutes). They excel at running, hiking, and pulling activities."
        elif "border collie" in breed_lower or "australian shepherd" in breed_lower:
            return "Herding breeds need both physical and mental exercise. Include training, puzzles, and agility work."
        elif "bulldog" in breed_lower or "pug" in breed_lower:
            return "Brachycephalic breeds should avoid intense exercise, especially in heat. Short, gentle walks are best."
        elif "chihuahua" in breed_lower:
            return "Small breeds need moderate exercise. Indoor play and short walks (15-30 min) are usually sufficient."
        elif "basset hound" in breed_lower or "dachshund" in breed_lower:
            return "Low-energy breeds need moderate exercise. Avoid activities that stress their long backs."
    
    # Breed-specific health advice
    elif category == "health":
        if "bulldog" in breed_lower or "pug" in breed_lower:
            return "Watch for breathing issues, skin fold infections, and eye problems common in brachycephalic breeds."
        elif "labrador" in breed_lower:
            return "Monitor for hip dysplasia, obesity, and ear infections. Regular exercise and weight management are crucial."
        elif "german shepherd" in breed_lower:
            return "Prone to hip dysplasia and joint issues. Maintain healthy weight and provide joint supplements as recommended."
        elif "dachshund" in breed_lower:
            return "IVDD (intervertebral disc disease) is a major concern. Avoid jumping and support their back when lifting."
        elif "golden retriever" in breed_lower:
            return "Common issues include hip dysplasia, cancer, and skin allergies. Regular vet checkups are essential."
    
    # Breed-specific grooming advice
    elif category == "grooming":
        if "poodle" in breed_lower or "bichon" in breed_lower:
            return "Curly-coated breeds need regular brushing (daily) and professional grooming every 4-6 weeks."
        elif "husky" in breed_lower or "malamute" in breed_lower:
            return "Double-coated breeds shed heavily seasonally. Regular brushing (2-3 times/week) helps manage shedding."
        elif "smooth coat" in breed_lower or "beagle" in breed_lower:
            return "Short-haired breeds need minimal grooming - weekly brushing is usually sufficient."
        elif "golden retriever" in breed_lower:
            return "Long, dense coats need regular brushing (3-4 times/week) to prevent matting and reduce shedding."
    
    return ""

def check_faq_match(question: str, pet_profile: dict) -> Optional[str]:
    """
    Check if the question matches common FAQ patterns and return personalized response.
    Uses pet profile data and breed-specific advice when available.
    Returns None if no match found, otherwise returns the response.
    """
    question_lower = question.lower().strip()
    
    # Extract pet profile context
    pet_name = pet_profile.get('petName', 'your dog') if pet_profile else 'your dog'
    breed = pet_profile.get('breed', '') if pet_profile else ''
    weight = pet_profile.get('weight', '') if pet_profile else ''
    age = pet_profile.get('age', '') if pet_profile else ''
    gender = pet_profile.get('gender', '') if pet_profile else ''
    activity = pet_profile.get('activityLevel', 'Moderate') if pet_profile else 'Moderate'
    medical_conditions = pet_profile.get('medicalConditions', []) if pet_profile else []
    goals = pet_profile.get('goals', []) if pet_profile else []
    
    # Helper to format pet context
    def get_pet_context():
        context_parts = []
        if breed and breed.lower() not in ['unknown', 'unknown breed', '']:
            context_parts.append(f"Breed: {breed}")
        if age:
            context_parts.append(f"Age: {age}")
        if weight:
            context_parts.append(f"Weight: {weight}")
        if gender:
            context_parts.append(f"Gender: {gender}")
        if medical_conditions:
            context_parts.append(f"Medical Conditions: {', '.join(medical_conditions)}")
        return " | ".join(context_parts) if context_parts else None
    
    pet_context = get_pet_context()
    context_note = f"\n\n*Based on {pet_name}'s profile: {pet_context}*" if pet_context else ""
    
    # Greeting responses
    if any(word in question_lower for word in ['hi', 'hello', 'hey', 'namaste']):
        intro = f"Hello! I'm here to help you with {pet_name}'s health and care."
        if breed and breed.lower() not in ['unknown', 'unknown breed', '']:
            intro += f" I see {pet_name} is a {breed}."
        intro += " How can I assist you today?"
        return intro
    
    # Health questions - highly personalized
    if any(word in question_lower for word in ['health', 'sick', 'ill', 'problem', 'issue', 'symptom', 'veterinarian', 'vet']):
        response = f"Regarding {pet_name}'s health:\n\n"
        
        # Add breed-specific health advice
        breed_health = get_breed_specific_advice(breed, "health")
        if breed_health:
            response += f"🔸 Breed-specific considerations: {breed_health}\n\n"
        
        response += "General Health Recommendations:\n"
        response += "1. Regular vet checkups every 6-12 months\n"
        response += "2. Monitor eating and drinking habits daily\n"
        response += "3. Watch for changes in behavior or energy levels\n"
        response += "4. Keep vaccinations and preventatives up to date\n"
        
        # Add medical condition-specific note
        if medical_conditions:
            response += f"\n📋 Important: Since {pet_name} has {', '.join(medical_conditions)}, "
            response += "please follow your veterinarian's specific care instructions and monitor these conditions closely.\n"
        
        response += "\n⚠️ If you notice concerning symptoms, please consult with a veterinarian immediately."
        return response + context_note
    
    # Nutrition questions - highly personalized
    if any(word in question_lower for word in ['food', 'diet', 'eat', 'nutrition', 'meal', 'feed', 'feeding', 'portion']):
        response = f"Nutrition advice for {pet_name}:\n\n"
        
        # Add breed-specific nutrition advice
        breed_nutrition = get_breed_specific_advice(breed, "nutrition")
        if breed_nutrition:
            response += f"🔸 Breed-specific guidance: {breed_nutrition}\n\n"
        
        response += "General Nutrition Guidelines:\n"
        
        # Age-specific advice
        if age:
            if any(term in age.lower() for term in ['puppy', 'young', 'baby']):
                response += f"1. {pet_name} is a puppy - feed high-quality puppy formula for proper growth\n"
            elif any(term in age.lower() for term in ['senior', 'old', 'elder']):
                response += f"1. {pet_name} is a senior - consider senior formulas with joint support and lower calories\n"
            else:
                response += "1. Feed high-quality adult dog food appropriate for their size\n"
        else:
            response += "1. Feed high-quality dog food appropriate for their age and size\n"
        
        # Weight-specific advice
        if weight:
            response += f"2. Current weight: {weight} - adjust portions to maintain healthy weight\n"
        else:
            response += "2. Follow feeding guidelines on the food package based on ideal weight\n"
        
        response += "3. Provide fresh water at all times\n"
        response += "4. Avoid toxic human foods (chocolate, grapes, onions, xylitol, etc.)\n"
        
        # Activity level-based portion advice
        if activity:
            activity_lower = activity.lower()
            if activity_lower in ['high', 'very high', 'active']:
                response += f"5. {pet_name} has high activity level - may need more calories\n"
            elif activity_lower in ['low', 'sedentary']:
                response += f"5. {pet_name} has low activity level - monitor portions to prevent weight gain\n"
            else:
                response += f"5. Adjust portions based on {pet_name}'s {activity.lower()} activity level\n"
        
        # Medical conditions affecting diet
        if medical_conditions:
            diet_conditions = [mc for mc in medical_conditions if any(term in mc.lower() for term in ['kidney', 'diabetes', 'allergy', 'obesity', 'weight'])]
            if diet_conditions:
                response += f"\n⚠️ Special dietary considerations: {pet_name} has {', '.join(diet_conditions)}. "
                response += "Please follow your veterinarian's dietary recommendations.\n"
        
        response += "\n💡 For specific nutritional calculations, use the Nutrient Calculator feature in the app."
        return response + context_note
    
    # Exercise questions - highly personalized
    if any(word in question_lower for word in ['exercise', 'walk', 'play', 'activity', 'fitness', 'workout']):
        response = f"Exercise recommendations for {pet_name}:\n\n"
        
        # Add breed-specific exercise advice
        breed_exercise = get_breed_specific_advice(breed, "exercise")
        if breed_exercise:
            response += f"🔸 Breed-specific activity needs: {breed_exercise}\n\n"
        
        # Age-based exercise
        if age:
            if any(term in age.lower() for term in ['puppy', 'young']):
                response += f"1. {pet_name} is a puppy - short, frequent play sessions (5-10 min, multiple times/day)\n"
                response += "   Avoid excessive exercise to protect growing joints\n"
            elif any(term in age.lower() for term in ['senior', 'old']):
                response += f"1. {pet_name} is a senior - gentle, low-impact exercise (20-30 min/day)\n"
                response += "   Swimming and short walks are ideal\n"
            else:
                response += "1. Daily walks (30-60 minutes depending on breed and size)\n"
        else:
            response += "1. Daily walks (30-60 minutes depending on breed and age)\n"
        
        response += "2. Interactive playtime and games (fetch, tug-of-war)\n"
        response += "3. Mental stimulation through training or puzzle toys\n"
        
        # Activity level adjustment
        if activity:
            response += f"4. Adjust intensity based on {pet_name}'s {activity.lower()} activity level\n"
        else:
            response += "4. Adjust activity based on weather and your dog's activity level\n"
        
        response += "5. Watch for signs of fatigue, overheating, or limping\n"
        
        # Medical condition considerations
        if medical_conditions:
            exercise_conditions = [mc for mc in medical_conditions if any(term in mc.lower() for term in ['joint', 'hip', 'arthritis', 'heart', 'respiratory'])]
            if exercise_conditions:
                response += f"\n⚠️ Exercise restrictions: {pet_name} has {', '.join(exercise_conditions)}. "
                response += "Consult your veterinarian for appropriate exercise guidelines.\n"
        
        return response + context_note
    
    # Behavior questions
    if any(word in question_lower for word in ['behavior', 'behave', 'training', 'train', 'obey', 'discipline']):
        response = f"Behavior and training tips for {pet_name}:\n\n"
        
        # Breed-specific behavior notes
        if breed and breed.lower() not in ['unknown', 'unknown breed', '']:
            if any(b in breed.lower() for b in ['husky', 'malamute', 'shiba']):
                response += f"🔸 {breed} breeds can be independent - be patient and consistent\n"
            elif any(b in breed.lower() for b in ['border collie', 'australian shepherd', 'german shepherd']):
                response += f"🔸 {breed} breeds are highly intelligent - provide mental challenges\n"
            elif any(b in breed.lower() for b in ['retriever', 'labrador', 'golden']):
                response += f"🔸 {breed} breeds respond well to positive reinforcement and treats\n"
        
        response += "General Training Guidelines:\n"
        response += "1. Use positive reinforcement (treats, praise) - works best for all dogs\n"
        response += "2. Be consistent with commands and rules across all family members\n"
        response += "3. Socialize early and regularly (especially important for puppies)\n"
        response += "4. Provide mental stimulation to prevent boredom and destructive behavior\n"
        response += "5. Consider professional training classes if needed\n"
        response += "6. Keep training sessions short (5-15 minutes) and fun\n"
        response += "\n💡 Remember: Patience and consistency are key to successful training!"
        return response + context_note
    
    # General care/grooming - highly personalized
    if any(word in question_lower for word in ['care', 'grooming', 'bath', 'clean', 'brush', 'nail']):
        response = f"General care tips for {pet_name}:\n\n"
        
        # Add breed-specific grooming advice
        breed_grooming = get_breed_specific_advice(breed, "grooming")
        if breed_grooming:
            response += f"🔸 Breed-specific grooming: {breed_grooming}\n\n"
        
        response += "General Care Checklist:\n"
        response += "1. Regular grooming based on coat type (weekly to daily brushing)\n"
        response += "2. Brush teeth regularly (daily ideal, minimum 2-3 times/week) to prevent dental issues\n"
        response += "3. Trim nails when they click on the floor (every 2-4 weeks typically)\n"
        response += "4. Check ears weekly for signs of infection (redness, odor, discharge)\n"
        response += "5. Keep living area clean and comfortable\n"
        response += "6. Provide a safe, secure environment\n"
        response += "7. Regular baths (monthly or as needed based on activity and coat type)\n"
        
        return response + context_note
    
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


def generate_dynamic_answer_with_faq_context(
    question: str,
    history: list,
    location: Optional[str],
    pet_profile: dict,
    faq_context: str = ""
) -> str:
    """
    Generates an AI response using OpenAI with FAQ context.
    Used when FAQ match is weak or when GPT fallback is needed.
    """
    # Step 1: If no OpenAI client, use fallback
    if client is None:
        print(f"No OpenAI client available, using fallback response")
        return generate_fallback_response(question, pet_profile)
    
    # Step 2: Use OpenAI with FAQ context
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
        
        # Build system prompt with FAQ context
        faq_context_section = f"\n\n{faq_context}" if faq_context else ""
        
        system_prompt = f"""You are a helpful AI assistant specialized in dog health and care. 
You provide expert advice on dog nutrition, health, behavior, and general care.
{profile_context}{location_context}{faq_context_section}

Guidelines:
- Provide helpful, accurate, and caring responses about dog health and wellness.
- If FAQ context is provided, you may reference it but provide your own comprehensive answer.
- Keep responses concise (3-5 lines), friendly, and chat-style.
- Never provide medical diagnoses - always recommend consulting a veterinarian for health concerns.
- Use a warm, supportive tone.

Safety rules:
- No medical diagnosis
- Suggest veterinary consultation for serious health questions
- Be honest about limitations"""
        
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
        print(f"Error generating AI response with FAQ context: {e}")
        
        # Check for specific error types
        if "insufficient_quota" in error_str or "429" in error_str:
            return "⚠️ Your OpenAI API quota has been exceeded. Please add credits to your OpenAI account at https://platform.openai.com/account/billing. Until then, I'll provide helpful responses based on your pet's profile."
        elif "invalid_api_key" in error_str or "401" in error_str:
            return "⚠️ OpenAI API key is invalid. Please check your API key in the .env file."
        else:
            # Fallback to intelligent responses when API fails
            return generate_fallback_response(question, pet_profile)

