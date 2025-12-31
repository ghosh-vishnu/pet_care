# services/nutrition_service.py

from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel
from typing import Optional

# Setup OpenAI Client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define a Pydantic model for the structured output from the AI
class NutritionResult(BaseModel):
    """Defines the expected output structure for the nutrition calculation."""
    required_calories_kcal_day: float
    protein_grams_day: float
    fat_grams_day: float
    carbs_grams_day: float
    macro_distribution: str
    supplement_suggestions: str # Structured text from AI
    calculation_reference: str = "AAFCO/FEDIAF Standards (BalanceIT methodology)"

async def calculate_and_suggest_nutrition(pet_profile: dict) -> NutritionResult:
    """
    Uses GPT-4o-mini with structured JSON output to perform nutrition calculations 
    and suggest supplements based on AAFCO standards.
    """
    json_schema = NutritionResult.model_json_schema()
    profile_summary = json.dumps(pet_profile)
    
    # 🛑 Detailed system prompt for accurate, vet-like calculation
    system_prompt = (
        "You are an expert Certified Veterinary Nutritionist. Your primary reference for calculation "
        "MUST be the **AAFCO Nutrient Profiles for Dogs** and general **Veterinary Nutrition guidelines** "
        "(similar to BalanceIT methodology). Your task is to accurately calculate the dog's daily "
        "nutritional requirements based on the provided profile. "
        "**Calculation Steps MUST be based on industry standards:**\n"
        "1. **RER (Resting Energy Requirement) Calculation:** RER = 70 * (Weight in kg)^0.75.\n"
        "2. **MER (Maintenance Energy Requirement) Calculation:** Apply an appropriate, justified multiplier "
        "to the RER based on age, activity level, and goals to determine the MER.\n"
        "3. **Macronutrients:** Calculate protein and fat grams based on the resulting MER, ensuring the final "
        "diet meets or exceeds AAFCO minimum percentages (based on the dog's life stage). The remainder of the MER should be attributed to safe carbohydrate sources.\n"
        "4. **Supplementation:** Based on the profile (especially medical conditions, age, and goals), provide 2-3 specific, detailed supplement recommendations "
        "with rationale (e.g., specific Omega-3 ratios for coat health). The recommendations must be objective and high-quality.\n"
        "Your final response MUST be a JSON object that strictly adheres to the provided JSON schema."
        f"SCHEMA: {json_schema}"
    )
    
    user_prompt = f"Please calculate the full daily nutritional needs and suggest supplements for the dog with the following profile:\n\n{profile_summary}"

    # Define the Structured Output Schema
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Use response_format for guaranteed JSON output
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse and return the result
        result_dict = json.loads(response.choices[0].message.content)
        return NutritionResult.model_validate(result_dict)
        
    except Exception as e:
        print(f"Nutrition AI calculation failed: {e}")
        # Return a safe fallback result structure on failure
        return NutritionResult(
            required_calories_kcal_day=0.0,
            protein_grams_day=0.0,
            fat_grams_day=0.0,
            carbs_grams_day=0.0,
            macro_distribution="Error: Failed to calculate.",
            supplement_suggestions=f"Calculation service failed. Error: {e}",
            calculation_reference="Service Failure"
        )