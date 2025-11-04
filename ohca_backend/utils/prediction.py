import random
from utils.mortality import get_mortality_rate_for_county  # Updated function name


def predict_cases(county: str, weather_data: dict):
    """Return mock predictions (placeholder for real ML model)."""
    temp = weather_data.get("temperature", 20)
    humidity = weather_data.get("humidity", 60)

    # Get mortality rate and handle errors
    mortality = get_mortality_rate_for_county(county)

    # Dummy logic: cases increase slightly with temperature and humidity
    base = random.randint(40, 120)

    return {
        "yesterday_cases": base - random.randint(0, 15),
        "predicted_cases": base,
        "mortality_rate": mortality,
        }
