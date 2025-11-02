import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import requests
import os
from dotenv import load_dotenv
from shapely.geometry import shape, Point

# --- LOAD ENV VARIABLES ---
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/predict_all")

# --- STREAMLIT PAGE SETUP ---
st.set_page_config(page_title="OHCA Prediction Map", layout="wide")
st.title("🩺 OHCA Prediction Dashboard — Hungary")

# --- CUSTOM CSS ---
st.markdown("""
<style>
.block-container { padding-top: 3rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; max-width: 100%; }
iframe { height: 70vh !important; width: 100% !important; }
section[data-testid="stSidebar"] { width: 320px !important; }
</style>
""", unsafe_allow_html=True)

# --- LOAD GEOJSON ---
@st.cache_data
def load_geojson():
    with open("data/hu.json", "r", encoding="utf-8") as f:
        return json.load(f)

counties = load_geojson()

# --- FETCH DATA FROM BACKEND ---
def fetch_data():
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        response.raise_for_status()
        data_list = response.json()

        data_dict = {}
        for item in data_list:
            county = item["county"]
            prediction = item.get("prediction", {})
            weather = item.get("weather", {})
            combined = {**prediction, **weather}
            data_dict[county] = combined
        
        return data_dict, "✅ Data successfully loaded from backend."
    except Exception as e:
        return None, f"❌ Failed to load data from backend: {e}"

if "county_data" not in st.session_state:
    data_dict, message = fetch_data()
    if data_dict:
        st.session_state.county_data = data_dict
        st.success(message)
    else:
        st.error(message)
        st.stop()

data_dict = st.session_state.county_data

# --- SIDEBAR SETUP ---
sidebar = st.sidebar
sidebar.header("📊 County Dashboard")

if sidebar.button("🔄 Refresh data"):
    # Clear all relevant session state keys
    st.session_state.pop("county_data", None)
    st.session_state.pop("selected_county", None)
    st.rerun()

# --- COLOR SCALE ---
def color_scale(value):
    if value is None or value < 60:
        return "green"
    elif value < 90:
        return "orange"
    else:
        return "red"

# --- INITIAL MAP SETTINGS ---
center = [46.3, 19.5033]
zoom = 7
if "selected_county" not in st.session_state:
    st.session_state.selected_county = None

# --- CREATE MAP ---
m = folium.Map(
    location=center,
    zoom_start=zoom,
    min_zoom=7,
    max_zoom=7,
    zoom_control=False,
    scrollWheelZoom=False,
    dragging=False,
    doubleClickZoom=False,
)

# --- ADD GEOJSON LAYERS ---
for feature in counties["features"]:
    name = feature["properties"]["name"]
    if name not in data_dict:
        continue
    
    county_data = data_dict[name]
    predicted_cases = county_data.get("predicted_cases")
    color = color_scale(predicted_cases)

    # Highlight the selected county
    border_color = "blue" if st.session_state.get("selected_county") == name else "black"
    border_weight = 4 if st.session_state.get("selected_county") == name else 1

    folium.GeoJson(
        feature,
        style_function=lambda _, v=color, bc=border_color, bw=border_weight: {
            "fillColor": v,
            "color": bc,
            "weight": bw,
            "fillOpacity": 0.6,
        },
        highlight_function=lambda x: {"weight": 3, "color": "blue", "fillOpacity": 0.8},
    ).add_to(m)

# --- DISPLAY MAP AND GET CLICK ---
map_click_data = st_folium(
    m,
    key="map",
    returned_objects=["last_clicked"],
    width=1200,
    height=700,
)

# --- PROCESS CLICK AND RERUN IF SELECTION CHANGES ---
# This is the core logic fix.
# When a click happens, we determine the new county.
# If the selected county has changed, we update session_state and
# immediately rerun the script. This ensures the map is redrawn
# with the new selection in the very next frame.
if map_click_data and map_click_data.get("last_clicked"):
    coords = map_click_data["last_clicked"]
    point = Point(coords["lng"], coords["lat"])
    
    clicked_county = None
    for feature in counties["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            clicked_county = feature["properties"]["name"]
            break
    
    # If the click was on a valid county AND it's different from the current one
    if clicked_county and st.session_state.get("selected_county") != clicked_county:
        st.session_state.selected_county = clicked_county
        st.rerun() # The key to the fix!

# --- SHOW COUNTY DETAILS IN SIDEBAR ---
# This code will now always run with the correct selected_county,
# because if it changed, the script would have rerun before reaching here.
if st.session_state.get("selected_county"):
    county_name = st.session_state["selected_county"]
    county_data = data_dict.get(county_name, {})
    
    sidebar.subheader(f"📍 {county_name}")
    sidebar.markdown(f"🌡️ Temperature: **{county_data.get('temperature', 'N/A')} °C**")
    sidebar.markdown(f"💧 Humidity: **{county_data.get('humidity', 'N/A')}%**")
    sidebar.markdown(f"📅 Yesterday cases: **{county_data.get('yesterday_cases', 'N/A')}**")
    sidebar.markdown(f"🔮 Predicted cases: **{county_data.get('predicted_cases', 'N/A')}**")
    
    mortality_rate = county_data.get('mortality_rate', 0)
    sidebar.markdown(f"⚰️ Mortality rate: **{mortality_rate*100:.1f}%**")

# --- LEGEND ---
with sidebar.expander("🗺️ Color Legend", expanded=True):
    st.markdown("🟩 **Low risk:** Predicted < 60 cases")
    st.markdown("🟧 **Moderate risk:** 60 ≤ Predicted < 90 cases")
    st.markdown("🟥 **High risk:** Predicted ≥ 90 cases")