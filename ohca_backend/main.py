from fastapi import FastAPI
from utils.weather import get_weather_for_county
from utils.prediction import predict_cases
import json
import os

# --- Initialize FastAPI app ---
app = FastAPI(
    title="OHCA Prediction API",
    version="1.0",
    description="Backend for the OHCA Hungary prediction dashboard."
)

# --- Load county list from GeoJSON ---
DATA_PATH = os.path.join(os.path.dirname(__file__), "../ohca_frontend/data/hu.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    counties = [feature["properties"]["name"] for feature in json.load(f)["features"]]


@app.get("/")
def root():
    """Root endpoint for health check."""
    return {"message": "OHCA Prediction API is running!"}


@app.get("/weather/{county}")
def weather(county: str):
    """Fetch live weather for a given county."""
    return get_weather_for_county(county)


@app.get("/predict/{county}")
def predict(county: str):
    """Generate mock prediction for a county using weather data."""
    weather_data = get_weather_for_county(county)
    prediction = predict_cases(county, weather_data)
    return {"county": county, "weather": weather_data, "prediction": prediction}


@app.get("/predict_all")
def predict_all():
    """Generate predictions for all Hungarian counties."""
    results = []
    for county in counties:
        weather_data = get_weather_for_county(county)
        prediction = predict_cases(county, weather_data)
        results.append({
            "county": county,
            "weather": weather_data,
            "prediction": prediction
        })
    return results


# --- Run server locally ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
