import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import random

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="OHCA Prediction Map", layout="wide")

# --- CUSTOM CSS TO EXPAND MAP & STYLE SIDEBAR ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;    
    }
    iframe {
        height: 70vh !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] {
        width: 320px !important;  /* Adjust sidebar width */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🩺 OHCA Prediction Dashboard — Hungary")

# --- LOAD MAP DATA ---
with open("data/hu.json", "r", encoding="utf-8") as f:
    counties = json.load(f)

# --- GENERATE MOCK DATA ONCE ---
if "county_data" not in st.session_state:
    data_dict = {}
    for feature in counties["features"]:
        name = feature["properties"]["name"]
        data_dict[name] = {
            "predicted_cases": random.randint(40, 120),
            "yesterday_cases": random.randint(30, 100),
            "temperature": round(random.uniform(10, 25), 1),
            "humidity": round(random.uniform(40, 90), 1),
            "mortality_rate": round(random.uniform(0.05, 0.15), 2),
        }
    st.session_state.county_data = data_dict
else:
    data_dict = st.session_state.county_data

# --- REFRESH BUTTON (SIDEBAR) ---
sidebar = st.sidebar
sidebar.header("📊 County Dashboard")

if sidebar.button("🔄 Refresh mock data"):
    st.session_state.pop("county_data", None)
    st.session_state.pop("selected_county", None)
    st.rerun()

# --- COLOR SCALE FUNCTION ---
def color_scale(value):
    if value < 60:
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
    zoom_start=7,
    min_zoom=7,
    max_zoom=7,
    zoom_control=False,         # removes + / - buttons
    scrollWheelZoom=False,      # disables zoom with mouse wheel
    dragging=False,             # disables dragging
    doubleClickZoom=False,      # disables double-click zoom
)

# --- ADD COUNTY GEOJSON LAYERS ---
for feature in counties["features"]:
    name = feature["properties"]["name"]
    county_data = data_dict[name]
    color = color_scale(county_data["predicted_cases"])

    gj = folium.GeoJson(
        feature,
        style_function=lambda feature, v=color: {
            "fillColor": v,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        highlight_function=lambda x: {"weight": 3, "color": "blue"},
        tooltip=(
            f"<b>{name}</b><br>"
            f"🌡️ Temp: {county_data['temperature']} °C<br>"
            f"📅 Yesterday: {county_data['yesterday_cases']} cases<br>"
            f"🔮 Predicted: {county_data['predicted_cases']} cases<br>"
            f"⚰️ Mortality: {county_data['mortality_rate']*100:.1f}%"
        ),
    )
    gj.add_to(m)

# --- CAPTURE MAP INTERACTION ---
st_data = st_folium(m, width=None, height=750)

if st_data and st_data.get("last_active_drawing"):
    selected = st_data["last_active_drawing"]["properties"]["name"]
    st.session_state.selected_county = selected

# --- SIDEBAR DASHBOARD DETAILS ---
if st.session_state.selected_county:
    county_name = st.session_state.selected_county
    county_data = data_dict[county_name]

    sidebar.subheader(f"🏙️ {county_name}")

    # Safely extract data
    temperature = county_data.get("temperature", "N/A")
    humidity = county_data.get("humidity", "N/A")
    yesterday = county_data.get("yesterday_cases", "N/A")
    predicted = county_data.get("predicted_cases", "N/A")
    mortality = county_data.get("mortality_rate", "N/A")

    sidebar.markdown(f"**🌡️ Temperature:** {temperature} °C")
    sidebar.markdown(f"**💧 Humidity:** {humidity}%")
    sidebar.markdown(f"**📅 Yesterday’s Cases:** {yesterday}")
    sidebar.markdown(f"**🔮 Predicted Cases:** {predicted}")
    sidebar.markdown(
        f"**⚰️ Mortality Rate:** {float(mortality)*100 if mortality != 'N/A' else 'N/A'}%"
    )

else:
    sidebar.info("🖱️ Click on a county to view its details.")

# --- ADD COLOR LEGEND ---
with sidebar.expander("🗺️ Color Legend", expanded=True):
    st.markdown("🟩 **Low risk:** Predicted < 60 cases")
    st.markdown("🟧 **Moderate risk:** 60 ≤ Predicted < 90 cases")
    st.markdown("🟥 **High risk:** Predicted ≥ 90 cases")
