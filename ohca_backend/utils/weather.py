# backend/utils/weather.py
# Minimal-deps backend: only stdlib + requests. Reads ratio curves from CSV (no pandas/numpy).

import os
import csv
import math
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Tuple, Any, List

import requests
from utils.mortality import get_mortality_rate_for_county

# --- Predefined coordinates for Hungarian counties (centroids) ---
COUNTY_COORDS: Dict[str, Tuple[float, float]] = {
    "Bács-Kiskun": (46.5, 19.5),
    "Baranya": (46.1, 18.2),
    "Békés": (46.7, 21.1),
    "Borsod-Abaúj-Zemplén": (48.2, 20.8),
    "Csongrád": (46.3, 20.1),
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

# ------------------------------------------------------------------------------------
# Ratio loading & interpolation (CSV only; no pandas/numpy)
# ------------------------------------------------------------------------------------

def _ratio_dir() -> Path:
    """Where ratio CSVs live. Override with env RATIO_DIR if desired."""
    env = os.environ.get("RATIO_DIR")
    if env:
        return Path(env)
    # default: backend/data/ratio_store/pct5/
    return Path(__file__).resolve().parents[1] / "data" / "ratio_store" / "pct5"

_PARAM_TO_FILENAME = {
    "temp_c": "temp_c_ratio_pct5.csv",
    "rh_pct": "rh_pct_ratio_pct5.csv",
}

@lru_cache(maxsize=8)
def _load_ratio_csv(param: str) -> Optional[Tuple[List[float], List[float]]]:
    """Load ratio CSV for param -> (x_list, r_list). Returns None if not available/valid."""
    fname = _PARAM_TO_FILENAME.get(param)
    if not fname:
        return None
    path = _ratio_dir() / fname
    if not path.exists():
        return None

    xs: List[float] = []
    rs: List[float] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Expect columns 'x' and 'R_hat_bc'
            for row in reader:
                try:
                    x = float(row["x"])
                    r = float(row["R_hat_bc"])
                    if math.isfinite(x) and math.isfinite(r):
                        xs.append(x); rs.append(r)
                except Exception:
                    continue
        # Basic sanity
        if len(xs) < 2:
            return None
        # Ensure x is sorted (should already be)
        if any(xs[i] > xs[i+1] for i in range(len(xs)-1)):
            # sort both by x
            pairs = sorted(zip(xs, rs), key=lambda t: t[0])
            xs = [p[0] for p in pairs]
            rs = [p[1] for p in pairs]
        return xs, rs
    except Exception:
        return None

def _interp_ratio(xs: List[float], rs: List[float], v: float, clip: bool = True) -> float:
    """Linear interpolation on (xs, rs) at v (optionally clipped to domain)."""
    x_min, x_max = xs[0], xs[-1]
    if clip:
        if v <= x_min: return rs[0]
        if v >= x_max: return rs[-1]
    # locate insertion point
    i = bisect_left(xs, v)
    if i <= 0: return rs[0]
    if i >= len(xs): return rs[-1]
    x0, x1 = xs[i-1], xs[i]
    r0, r1 = rs[i-1], rs[i]
    # guard division by zero
    if x1 == x0:
        return r0
    t = (v - x0) / (x1 - x0)
    return r0 + t * (r1 - r0)

def _ratio_value(param: str, value: Optional[float], clip: bool = True) -> Optional[float]:
    """Public: interpolate ratio for a param at value; None if missing."""
    if value is None:
        return None
    loaded = _load_ratio_csv(param)
    if loaded is None:
        return None
    xs, rs = loaded
    try:
        v = float(value)
    except Exception:
        return None
    return float(_interp_ratio(xs, rs, v, clip=clip))

def _ratio_emoji(r: Optional[float]) -> str:
    """Map ratio to a color badge."""
    if r is None or not math.isfinite(r):
        return "⬜"  # unknown/neutral
    if r < 0.8:
        return "🟩"  # protective
    if r < 1.3:
        return "⬜"  # near-neutral (white)
    if r < 1.6:
        return "🟨"  # mild elevation
    if r < 2.3:
        return "🟧"  # moderate elevation
    return "🟥"      # strong elevation

def _combine_risks_mult(r1: Optional[float], r2: Optional[float]) -> Optional[float]:
    """Combine two ratios multiplicatively if both present."""
    if r1 is None or r2 is None:
        return r1 or r2
    return float(r1 * r2)

# ------------------------------------------------------------------------------------
# Weather + risk service
# ------------------------------------------------------------------------------------

def get_weather_for_county(county_name: str) -> Dict[str, Any]:
    """
    Fetch weather and attach risk (pct=5 ratio) for today's daily means and the next 2 days.
    Uses current conditions only for display (no risk).
    """
    coords = COUNTY_COORDS.get(county_name)
    if not coords:
        return {"error": f"Unknown county: {county_name}"}

    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Europe/Budapest",
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_mean,relative_humidity_2m_mean",
        "forecast_days": 3,  # today + next 2
    }

    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()

        # --- current ---
        cur = data.get("current", {}) or {}
        current_temp = cur.get("temperature_2m")
        current_hum = cur.get("relative_humidity_2m")
        wmo_code = cur.get("weather_code")
        conditions_text = _WMO_CODE_TEXT.get(
            wmo_code, "Fair" if wmo_code is None else f"WMO {wmo_code}"
        )

        # --- daily means (today + 2) ---
        daily = data.get("daily", {}) or {}
        times: List[str] = daily.get("time") or []
        tmean: List[Optional[float]] = daily.get("temperature_2m_mean") or []
        hmean: List[Optional[float]] = daily.get("relative_humidity_2m_mean") or []

        mortality = get_mortality_rate_for_county(county_name)

        def risk_dict(t: Optional[float], h: Optional[float]) -> Dict[str, Any]:
            r_t = _ratio_value("temp_c", t)
            r_h = _ratio_value("rh_pct", h)
            r_c = _combine_risks_mult(r_t, r_h)
            return {
                "temp_ratio": r_t,
                "temp_emoji": _ratio_emoji(r_t),
                "rh_ratio": r_h,
                "rh_emoji": _ratio_emoji(r_h),
                "combined_ratio": r_c,
                "combined_emoji": _ratio_emoji(r_c),
            }

        # today
        temperature_mean_today = tmean[0] if len(tmean) > 0 else None
        humidity_mean_today = hmean[0] if len(hmean) > 0 else None
        risk_today = risk_dict(temperature_mean_today, humidity_mean_today)

        # forecast
        forecast_mean = []
        for i in (1, 2):
            if i < len(times):
                entry = {
                    "date": times[i],
                    "temperature_mean": (tmean[i] if i < len(tmean) else None),
                    "humidity_mean": (hmean[i] if i < len(hmean) else None),
                }
                entry["risk"] = risk_dict(entry["temperature_mean"], entry["humidity_mean"])
                forecast_mean.append(entry)

        return {
            "temperature": current_temp,
            "humidity": current_hum,
            "conditions": conditions_text,

            "temperature_mean_today": temperature_mean_today,
            "humidity_mean_today": humidity_mean_today,
            "risk_today": risk_today,

            "forecast_mean": forecast_mean,
            "mortality_rate": mortality,
        }

    except Exception as e:
        # Return a structured error so the UI can handle it gracefully
        return {"error": f"{type(e).__name__}: {e}"}
