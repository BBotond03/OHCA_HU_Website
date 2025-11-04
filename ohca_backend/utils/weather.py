import requests
from utils.mortality import get_mortality_rate_for_county
# --- Predefined coordinates for Hungarian counties ---
# (approximate centroids for reliable weather queries)
COUNTY_COORDS = {
    "Bács-Kiskun": (46.5, 19.5),
    "Baranya": (46.1, 18.2),
    "Békés": (46.7, 21.1),
    "Borsod-Abaúj-Zemplén": (48.2, 20.8),
    "Csongrád-Csanád": (46.3, 20.1),
    "Fejér": (47.1, 18.4),
    "Gyor-Moson-Sopron": (47.7, 17.6),
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

import requests

_WMO_CODE_TEXT = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def get_weather_for_county(county_name: str):
    coords = COUNTY_COORDS.get(county_name)
    if not coords:
        return {"error": f"Unknown county: {county_name}"}

    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Europe/Budapest",
        # Use comma-separated values (safer than lists for this API)
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_mean,relative_humidity_2m_mean",
        "forecast_days": 3,  # today + next 2
    }

    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()

        cur = data.get("current", {}) or {}
        current_temp = cur.get("temperature_2m")
        current_hum = cur.get("relative_humidity_2m")
        wmo_code = cur.get("weather_code")
        conditions_text = _WMO_CODE_TEXT.get(wmo_code, "Fair" if wmo_code is None else f"WMO {wmo_code}")

        daily = data.get("daily", {}) or {}
        times = daily.get("time") or []
        tmean = daily.get("temperature_2m_mean") or []
        hmean = daily.get("relative_humidity_2m_mean") or []
        mortality = get_mortality_rate_for_county(county_name)

        temperature_mean_today = tmean[0] if len(tmean) > 0 else None
        humidity_mean_today = hmean[0] if len(hmean) > 0 else None

        forecast_mean = []
        for i in (1, 2):
            if i < len(times):
                forecast_mean.append({
                    "date": times[i],
                    "temperature_mean": tmean[i] if i < len(tmean) else None,
                    "humidity_mean": hmean[i] if i < len(hmean) else None,
                })

        return {
            "temperature": current_temp,
            "humidity": current_hum,
            "conditions": conditions_text,
            "temperature_mean_today": temperature_mean_today,
            "humidity_mean_today": humidity_mean_today,
            "forecast_mean": forecast_mean,
            "mortality_rate": mortality,
            
        }

    except Exception as e:
        return {"error": str(e)}
