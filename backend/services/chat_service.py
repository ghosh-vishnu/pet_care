import os
import json
from typing import Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ✅ Import nutrient service
from services.nutrient_service import calculate_nutrients

# ✅ Import OpenAI
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to FAQ file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FAQ_PATH = os.path.join(BASE_DIR, "data", "faq.json")

# Load FAQ
with open(FAQ_PATH, "r", encoding="utf-8") as fp:
    FAQ = json.load(fp)

QUESTIONS = list(FAQ.keys())
ANSWERS = [FAQ[q] for q in QUESTIONS]

# Load local embedding model (downloads once, then cached)
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Precompute embeddings for FAQ questions
QUESTION_EMBEDDINGS = MODEL.encode(QUESTIONS, normalize_embeddings=True)


def chatgpt_fallback(user_q: str) -> str:
    """
    Calls ChatGPT to get a natural answer.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # lightweight, fast model
            messages=[
                {"role": "system", "content": "You are a helpful veterinary AI assistant for dog health, nutrition, and wellness. Always be safe and professional."},
                {"role": "user", "content": user_q}
            ],
            temperature=0.7,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ ChatGPT unavailable: {e}"


def answer_question(user_q: str, min_score: float = 0.6) -> Tuple[str, str, float]:
    """
    Returns (answer, matched_question, similarity_score).
    Order of resolution:
    1. Nutrition logic
    2. FAQ embeddings
    3. ChatGPT fallback
    """
    try:
        user_q_lower = user_q.lower()

        # 🔍 Step 1: Check if nutrition-related query
        nutrition_keywords = [
            "diet", "nutrition", "food", "meal", "feed", "protein",
            "fat", "carb", "vegetarian", "non-veg", "calorie", "kcal"
        ]
        if any(kw in user_q_lower for kw in nutrition_keywords):
            try:
                answer = calculate_nutrients(user_q)
                return answer, "nutrition_calculation", 1.0
            except Exception as e:
                return f"⚠️ Could not calculate nutrition: {e}", "nutrition_error", 0.0

        # 🔍 Step 2: Try FAQ semantic matching
        user_vec = MODEL.encode([user_q], normalize_embeddings=True)
        sims = cosine_similarity(user_vec, QUESTION_EMBEDDINGS)[0]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])

        if best_score >= min_score:
            return ANSWERS[best_idx], QUESTIONS[best_idx], best_score

        # 🔍 Step 3: ChatGPT fallback
        gpt_answer = chatgpt_fallback(user_q)
        return gpt_answer, "chatgpt", 1.0

    except Exception as e:
        print("Error in answer_question:", e)
        return "Sorry, I couldn’t process your request. Please try again.", "", 0.0
