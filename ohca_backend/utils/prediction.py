import random

def predict_cases(county: str, weather_data: dict):
    """Return mock predictions (placeholder for real ML model)."""
    temp = weather_data.get("temperature", 20)
    humidity = weather_data.get("humidity", 60)

    # Dummy logic: cases increase slightly with temperature and humidity
    base = random.randint(40, 120)
    mortality = round(random.uniform(0.05, 0.15), 2)

    return {
        "yesterday_cases": base - random.randint(0, 15),
        "predicted_cases": base,
        "mortality_rate": mortality,
        "temperature": temp,
        "humidity": humidity,
    }
