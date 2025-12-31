# services/nutrient_service.py

def calculate_rer(weight_kg: float) -> float:
    """Resting Energy Requirement (RER) formula."""
    return 70 * (weight_kg ** 0.75)


def calculate_mer(rer: float, age_stage: str, activity_level: str) -> float:
    """Maintenance Energy Requirement (MER) depends on age + activity."""
    factors = {
        "puppy": 3.0,       # up to 4 months
        "young": 2.0,       # 4-12 months
        "adult": 1.6,       # normal activity
        "senior": 1.2,      # lower metabolism
    }

    # Adjust for activity
    if activity_level == "active":
        mult = 1.8
    elif activity_level == "working":
        mult = 2.5
    else:
        mult = 1.0

    return rer * factors.get(age_stage, 1.6) * mult


def calculate_macros(mer: float, weight_kg: float) -> dict:
    """Split MER into macros based on dog nutrition guidelines."""
    protein_g = 2.62 * weight_kg   # g per kg bodyweight (AAFCO)
    fat_g = 1.3 * weight_kg        # g per kg bodyweight (AAFCO)
    carb_g = (mer * 0.3) / 4       # ~30% calories from carbs, 4 kcal/g

    return {
        "protein_g": round(protein_g, 1),
        "fat_g": round(fat_g, 1),
        "carbs_g": round(carb_g, 1),
    }


def generate_tips(age_stage: str, mer: float, macros: dict, diet_type: str = "mixed") -> str:
    """Generate tailored nutrition tips based on calculation."""
    tips = []

    if age_stage == "puppy":
        tips.append("Puppies need higher protein and fat for growth — ensure DHA from fish oils.")
    elif age_stage == "adult":
        tips.append("Focus on balanced nutrition with lean protein and digestible carbs.")
    elif age_stage == "senior":
        tips.append("Senior dogs need fewer calories but more joint support (glucosamine, omega-3).")

    # MER thresholds
    if mer > 2000:
        tips.append("High calorie needs — consider multiple small meals instead of one large meal.")
    elif mer < 500:
        tips.append("Very low calorie requirement — risk of underfeeding if not monitored.")

    # Diet type
    if diet_type == "vegetarian":
        tips.append("For vegetarian diet, ensure enough taurine, L-carnitine, and vitamin B12 from supplements.")
    elif diet_type == "non-vegetarian":
        tips.append("Include high-quality animal protein sources like chicken, fish, or lamb.")

    # Macro guidance
    tips.append(f"Daily intake: {macros['protein_g']}g protein, {macros['fat_g']}g fat, {macros['carbs_g']}g carbs.")

    return "\n".join(tips)


def calculate_nutrients(user_msg: str) -> str:
    """
    Parse basic info from user_msg and return nutrient recommendations.
    Example user_msg: "My 5 year old 20kg Labrador is active and vegetarian"
    """
    import re

    # --- Extract weight ---
    weight_match = re.search(r"(\d+)\s?kg", user_msg.lower())
    weight = float(weight_match.group(1)) if weight_match else 20.0  # default 20kg

    # --- Extract age ---
    age_match = re.search(r"(\d+)\s?(year|yr|years|yrs|month|mo)", user_msg.lower())
    age_stage = "adult"
    if age_match:
        val = int(age_match.group(1))
        if "month" in age_match.group(2) and val <= 4:
            age_stage = "puppy"
        elif "month" in age_match.group(2):
            age_stage = "young"
        elif "year" in age_match.group(2) and val >= 7:
            age_stage = "senior"
        else:
            age_stage = "adult"

    # --- Extract activity ---
    if "active" in user_msg.lower():
        activity = "active"
    elif "work" in user_msg.lower():
        activity = "working"
    else:
        activity = "normal"

    # --- Extract diet type ---
    diet_type = "mixed"
    if "vegetarian" in user_msg.lower():
        diet_type = "vegetarian"
    elif "non-veg" in user_msg.lower() or "meat" in user_msg.lower():
        diet_type = "non-vegetarian"

    # --- Calculate ---
    rer = calculate_rer(weight)
    mer = calculate_mer(rer, age_stage, activity)
    macros = calculate_macros(mer, weight)
    tips = generate_tips(age_stage, mer, macros, diet_type)

    # --- Build Response ---
    return (
        f"📌 Nutrient Requirements for your dog:\n"
        f"- Weight: {weight} kg\n"
        f"- Age Stage: {age_stage.capitalize()}\n"
        f"- Activity: {activity}\n"
        f"- Diet: {diet_type}\n\n"
        f"🔥 Daily Energy: {round(mer)} kcal\n"
        f"💪 Protein: {macros['protein_g']} g\n"
        f"🥓 Fat: {macros['fat_g']} g\n"
        f"🍚 Carbs: {macros['carbs_g']} g\n\n"
        f"💡 Tips:\n{tips}"
    )
