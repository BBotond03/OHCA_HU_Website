import requests

# --- Predefined coordinates for Hungarian counties ---
# (approximate centroids for reliable weather queries)
COUNTY_COORDS = {
    "Bács-Kiskun": (46.5, 19.5),
    "Baranya": (46.1, 18.2),
    "Békés": (46.7, 21.1),
    "Borsod-Abaúj-Zemplén": (48.2, 20.8),
    "Csongrád-Csanád": (46.3, 20.1),
    "Fejér": (47.1, 18.4),
    "Győr-Moson-Sopron": (47.7, 17.6),
    "Hajdú-Bihar": (47.5, 21.6),
    "Heves": (47.9, 20.3),
    "Jász-Nagykun-Szolnok": (47.2, 20.2),
    "Komárom-Esztergom": (47.6, 18.3),
    "Nógrád": (48.0, 19.3),
    "Pest": (47.3, 19.4),
    "Somogy": (46.5, 17.6),
    "Szabolcs-Szatmár-Bereg": (48.1, 22.1),
    "Tolna": (46.5, 18.6),
    "Vas": (47.1, 16.8),
    "Veszprém": (47.1, 17.9),
    "Zala": (46.8, 16.9),
    "Budapest": (47.5, 19.0),
}

def get_weather_for_county(county_name: str):
    """
    Fetch current weather for a Hungarian county using Open-Meteo API.
    Returns temperature, humidity, and conditions (mocked).
    """
    coords = COUNTY_COORDS.get(county_name)
    if not coords:
        return {"error": f"Unknown county: {county_name}"}

    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m"],
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if "current" not in data:
            return {"error": "No current weather data found."}

        return {
            "temperature": data["current"]["temperature_2m"],
            "humidity": data["current"]["relative_humidity_2m"],
            # We mock a short description (Open-Meteo doesn’t provide this directly)
            "conditions": "Fair",
        }

    except Exception as e:
        return {"error": str(e)}
