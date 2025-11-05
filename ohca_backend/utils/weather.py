# backend/utils/weather.py
# Minimal-deps backend: stdlib + requests. Adds centroid fallback for any unmapped names.
import os, csv, math, json, unicodedata
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Tuple, Any, List

import requests
from utils.mortality import get_mortality_rate_for_county

# ------------------------- CONFIG -------------------------

# Where the saved ratio CSVs live (can override with env RATIO_DIR)
def _ratio_dir() -> Path:
    env = os.environ.get("RATIO_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "data" / "ratio_store" / "pct5"

# Where to find the ORIGINAL (unfiltered) GeoJSON.
# We try several common places, or override via GEOJSON_PATH env var.
def _geojson_path() -> Optional[Path]:
    cand = []
    if os.getenv("GEOJSON_PATH"):
        cand.append(Path(os.getenv("GEOJSON_PATH")))
    base = Path(__file__).resolve().parents[1]  # .../backend
    cand += [
        base / "data" / "hu.json",     # backend/data/hu.json
        base.parents[0] / "data" / "hu.json",  # <repo_root>/data/hu.json
        Path("data/hu.json"),          # CWD relative
    ]
    for p in cand:
        if p and p.exists():
            return p
    return None

# -------------------- BASE COORDS (your curated 20) --------------------
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
EXTRA_LOCATIONS = {
    "Békéscsaba": (46.6833, 21.1000),
    "Debrecen": (47.5316, 21.6273),
    "Dunaújváros": (46.9619, 18.9355),
    "Eger": (47.9027, 20.3733),
    # Note: hu.json uses "Gyôr" (ô), not "Győr" (ő)
    "Gyôr": (47.6875, 17.6504),
    # hu.json uses "Hódmezôvásárhely" (ô)
    "Hódmezôvásárhely": (46.4167, 20.3333),
    "Kaposvár": (46.3667, 17.8000),
    "Kecskemét": (46.9062, 19.6913),
    "Miskolc": (48.1031, 20.7781),
    "Nagykanizsa": (46.4535, 16.9910),
    "Nyíregyháza": (47.9554, 21.7167),
    "Pécs": (46.0727, 18.2323),
    "Salgótarján": (48.0987, 19.8030),
    "Sopron": (47.6850, 16.5905),
    "Szeged": (46.2530, 20.1414),
    "Szekszárd": (46.3501, 18.7091),
    "Szolnok": (47.1833, 20.2000),
    "Szombathely": (47.2307, 16.6218),
    "Székesfehérvár": (47.1900, 18.4103),
    "Tatabánya": (47.5850, 18.3948),
    "Zalaegerszeg": (46.8417, 16.8416),
    "Érd": (47.3949, 18.9136),
}

# Merge them into COUNTY_COORDS so existing loops/logic just work.
COUNTY_COORDS.update(EXTRA_LOCATIONS)
# Known label quirks → canonical keys in our data
ALIASES = {
    "Csongrád-Csanád": "Csongrád",
    "Győr-Moson-Sopron": "Gyor-Moson-Sopron",
    "Gyor-Moson-Sopron": "Gyor-Moson-Sopron",
}

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("–", "-").replace("—", "-")
    return " ".join(s.split()).strip().lower()

# -------------------- Simple centroid helpers (no shapely) --------------------
def _ring_centroid(lonlat_ring: List[List[float]]) -> Tuple[float, float]:
    # GeoJSON coords are [lon, lat]
    pts = lonlat_ring[:]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    area2 = 0.0
    cx = cy = 0.0
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        cross = x0 * y1 - x1 * y0
        area2 += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area2) < 1e-12:
        xs = [p[0] for p in pts[:-1]]
        ys = [p[1] for p in pts[:-1]]
        return (sum(ys) / len(ys), sum(xs) / len(xs))
    cx /= (3.0 * area2)
    cy /= (3.0 * area2)
    return (cy, cx)  # (lat, lon)

def _polygon_centroid(poly_coords: List[List[List[float]]]) -> Tuple[float, float]:
    exterior = poly_coords[0]
    return _ring_centroid(exterior)

def _multipolygon_centroid(mpoly_coords: List[List[List[List[float]]]]) -> Tuple[float, float]:
    total_area2 = 0.0
    acc_lon = acc_lat = 0.0
    for poly in mpoly_coords:
        ring = poly[0]
        pts = ring[:]
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        area2 = 0.0
        cx = cy = 0.0
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            cross = x0 * y1 - x1 * y0
            area2 += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
        if abs(area2) < 1e-12:
            xs = [p[0] for p in pts[:-1]]
            ys = [p[1] for p in pts[:-1]]
            lon = sum(xs) / len(xs)
            lat = sum(ys) / len(ys)
            w = 1.0
        else:
            cx /= (3.0 * area2)
            cy /= (3.0 * area2)
            lon, lat = cx, cy
            w = abs(area2)
        total_area2 += w
        acc_lon += lon * w
        acc_lat += lat * w
    if total_area2 <= 0:
        return (47.0, 19.0)
    return (acc_lat / total_area2, acc_lon / total_area2)

@lru_cache(maxsize=1)
def _centroids_from_geojson() -> Dict[str, Tuple[float, float]]:
    path = _geojson_path()
    out: Dict[str, Tuple[float, float]] = {}
    if not path:
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            fc = json.load(f)
    except Exception:
        return out
    for ft in fc.get("features", []):
        props = ft.get("properties") or {}
        name = props.get("name")
        geom = ft.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not name or not gtype or not coords:
            continue
        try:
            if gtype == "Polygon":
                lat, lon = _polygon_centroid(coords)
            elif gtype == "MultiPolygon":
                lat, lon = _multipolygon_centroid(coords)
            else:
                continue
            out[name] = (float(lat), float(lon))
        except Exception:
            continue
    return out

@lru_cache(maxsize=1)
def _all_coords() -> Dict[str, Tuple[float, float]]:
    # Start with GeoJSON-derived centroids (so cities and any extras are covered)
    allc = dict(_centroids_from_geojson())
    # Overlay curated county coords (these win)
    allc.update(COUNTY_COORDS)
    # Add alias keys
    for alias, target in ALIASES.items():
        if alias not in allc and target in allc:
            allc[alias] = allc[target]
    return allc

def _coords_for(name: str) -> Optional[Tuple[float, float]]:
    allc = _all_coords()
    # exact
    if name in allc:
        return allc[name]
    # alias
    if name in ALIASES and ALIASES[name] in allc:
        return allc[ALIASES[name]]
    # normalized match
    n = _norm(name)
    for k, v in allc.items():
        if _norm(k) == n:
            return v
    return None

# -------------------- Ratio loading (CSV only) --------------------
_PARAM_TO_FILENAME = {
    "temp_c": "temp_c_ratio_pct5.csv",
    "rh_pct": "rh_pct_ratio_pct5.csv",
}

@lru_cache(maxsize=8)
def _load_ratio_csv(param: str) -> Optional[Tuple[List[float], List[float]]]:
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
            for row in reader:
                try:
                    x = float(row["x"]); r = float(row["R_hat_bc"])
                    if math.isfinite(x) and math.isfinite(r):
                        xs.append(x); rs.append(r)
                except Exception:
                    continue
        if len(xs) < 2:
            return None
        if any(xs[i] > xs[i+1] for i in range(len(xs)-1)):
            pairs = sorted(zip(xs, rs), key=lambda t: t[0])
            xs = [p[0] for p in pairs]; rs = [p[1] for p in pairs]
        return xs, rs
    except Exception:
        return None

def _interp_ratio(xs: List[float], rs: List[float], v: float, clip: bool = True) -> float:
    x_min, x_max = xs[0], xs[-1]
    if clip:
        if v <= x_min: return rs[0]
        if v >= x_max: return rs[-1]
    i = bisect_left(xs, v)
    if i <= 0: return rs[0]
    if i >= len(xs): return rs[-1]
    x0, x1 = xs[i-1], xs[i]; r0, r1 = rs[i-1], rs[i]
    if x1 == x0: return r0
    t = (v - x0) / (x1 - x0)
    return r0 + t * (r1 - r0)

def _ratio_value(param: str, value: Optional[float], clip: bool = True) -> Optional[float]:
    if value is None:
        return None
    loaded = _load_ratio_csv(param)
    if not loaded:
        return None
    xs, rs = loaded
    try:
        v = float(value)
    except Exception:
        return None
    return float(_interp_ratio(xs, rs, v, clip=clip))

def _ratio_emoji(r: Optional[float]) -> str:
    if r is None or not math.isfinite(r): return "⬜"
    if r < 0.8:  return "🟩"
    if r < 1.3:  return "⬜"
    if r < 1.6:  return "🟨"
    if r < 2.3:  return "🟧"
    return "🟥"

# -------------------- API: weather + risk --------------------
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

def get_weather_for_county(county_name: str) -> Dict[str, Any]:
    """
    Fetch weather and attach risk (pct=5 ratio) for today's daily means and the next 2 days.
    Works for both your 20 counties and any other names present in the original GeoJSON.
    """
    coords = _coords_for(county_name)
    if not coords:
        return {"error": f"Unknown area: {county_name}"}
    lat, lon = coords

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Europe/Budapest",
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_mean,relative_humidity_2m_mean",
        "forecast_days": 3,
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
        times: List[str] = daily.get("time") or []
        tmean: List[Optional[float]] = daily.get("temperature_2m_mean") or []
        hmean: List[Optional[float]] = daily.get("relative_humidity_2m_mean") or []

        def risk_pair(t: Optional[float], h: Optional[float]) -> Dict[str, Any]:
            rt = _ratio_value("temp_c", t)
            rh = _ratio_value("rh_pct", h)
            return {
                "temp_ratio": rt, "temp_emoji": _ratio_emoji(rt),
                "rh_ratio": rh,   "rh_emoji": _ratio_emoji(rh),
            }

        t_today = tmean[0] if len(tmean) > 0 else None
        h_today = hmean[0] if len(hmean) > 0 else None
        risk_today = risk_pair(t_today, h_today)

        forecast_mean = []
        for i in (1, 2):
            if i < len(times):
                entry = {
                    "date": times[i],
                    "temperature_mean": (tmean[i] if i < len(tmean) else None),
                    "humidity_mean": (hmean[i] if i < len(hmean) else None),
                }
                entry["risk"] = risk_pair(entry["temperature_mean"], entry["humidity_mean"])
                forecast_mean.append(entry)

        mortality = get_mortality_rate_for_county(county_name)

        return {
            "temperature": current_temp,
            "humidity": current_hum,
            "conditions": conditions_text,
            "temperature_mean_today": t_today,
            "humidity_mean_today": h_today,
            "risk_today": risk_today,
            "forecast_mean": forecast_mean,
            "mortality_rate": mortality,
        }

    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
