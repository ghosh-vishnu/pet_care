# services/health_advice.py

HEALTH_GUIDE = {
    "beagle": {
        "diet": "Balanced diet with controlled calories (prone to obesity).",
        "exercise": "At least 1 hour daily walk + playtime.",
        "common_issues": ["Epilepsy", "Hypothyroidism", "Hip dysplasia"]
    },
    "golden_retriever": {
        "diet": "High-quality protein, joint-support supplements.",
        "exercise": "2 hours daily activity.",
        "common_issues": ["Cancer", "Hip/elbow dysplasia", "Heart disease"]
    },
    "pug": {
        "diet": "Light meals to prevent obesity.",
        "exercise": "Short walks (avoid heat).",
        "common_issues": ["Breathing problems", "Skin infections"]
    },
    "german_shepherd": {
        "diet": "Protein-rich diet, joint-support food.",
        "exercise": "2+ hours vigorous activity.",
        "common_issues": ["Hip dysplasia", "Degenerative myelopathy"]
    },
    "bulldog": {
        "diet": "Low-fat, nutrient-dense food.",
        "exercise": "Short, moderate exercise.",
        "common_issues": ["Breathing problems", "Skin infections"]
    },
    "husky": {
        "diet": "High-protein diet for energy.",
        "exercise": "At least 2 hours daily running.",
        "common_issues": ["Eye disorders", "Hip dysplasia"]
    },
}

def get_health_report(breed: str) -> dict:
    return HEALTH_GUIDE.get(breed.lower(), {
        "diet": "Standard balanced diet.",
        "exercise": "Daily walks and playtime.",
        "common_issues": ["General health risks, consult vet regularly."]
    })
