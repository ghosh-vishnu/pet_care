import requests

def enrich_with_location(location: str, query: str):
    """
    Adds real-time location-based context.
    Example: weather, nearby vets, food availability.
    """
    advice = []

    # Weather check
    try:
        weather_api = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid=YOUR_KEY&units=metric"
        data = requests.get(weather_api).json()
        if "main" in data:
            temp = data["main"]["temp"]
            if temp > 30:
                advice.append("It’s quite hot, ensure your dog stays hydrated and avoid long walks in the afternoon.")
            elif temp < 10:
                advice.append("It’s cold, keep your dog warm and limit time outdoors.")
    except:
        pass

    # Vets / local services (dummy now, can extend with Google Maps API)
    advice.append(f"You can also check local vets near {location} for professional support.")

    return "\n".join(advice)
