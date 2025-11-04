# weather_sidebar.py
import streamlit as st
from datetime import datetime

def render_weather_sidebar(sidebar, county_name, county_data):
    # --- tiny formatters ---
    fT = lambda x: f"{float(x):.1f} °C" if isinstance(x, (int, float)) else (
        f"{float(x):.1f} °C" if isinstance(x, str) and x.replace('.', '', 1).isdigit() else "N/A"
    )
    def fH(x):
        try: return f"{int(round(float(x)))}%"
        except: return "N/A"
    def fPct01(x):
        try: return f"{float(x)*100:.1f}%"
        except: return "N/A"
    def pD(s):
        try: return datetime.strptime(s, "%Y-%m-%d").strftime("%a %b %d")
        except: return s or "N/A"

    # --- pull forecast (tomorrow & day after) safely ---
    days = county_data.get("forecast_mean") or []
    tm = days[0] if len(days) > 0 else {}
    da = days[1] if len(days) > 1 else {}

    # --- header + current ---
    sidebar.subheader(f"📍 {county_name}")
    sidebar.markdown(f"🌡️ Temperature: **{fT(county_data.get('temperature'))}**")
    sidebar.markdown(f"💧 Humidity: **{fH(county_data.get('humidity'))}**")

    # --- daily means (today + next 2) ---
    sidebar.markdown("### 🔮 Daily Averages")
    sidebar.markdown(
        f"**Today:** {fT(county_data.get('temperature_mean_today'))} · "
        f"{fH(county_data.get('humidity_mean_today'))}"
    )
    sidebar.markdown(
        f"**🗓️ {pD(tm.get('date'))} (tomorrow):** "
        f"{fT(tm.get('temperature_mean'))} · {fH(tm.get('humidity_mean'))}"
    )
    sidebar.markdown(
        f"**🗓️ {pD(da.get('date'))} (day after):** "
        f"{fT(da.get('temperature_mean'))} · {fH(da.get('humidity_mean'))}"
    )

    # --- your extra metrics ---
    sidebar.markdown(f"📅 Yesterday cases: **{county_data.get('yesterday_cases', 'N/A')}**")
    sidebar.markdown(f"🔮 Predicted cases: **{county_data.get('predicted_cases', 'N/A')}**")
    sidebar.markdown(f"⚰️ Mortality rate: **{fPct01(county_data.get('mortality_rate'))}**")

    # --- legend moved inside ---
    with sidebar.expander("🗺️ Color Legend", expanded=True):
        st.markdown("🟩 **Low risk:** Predicted < 60 cases")
        st.markdown("🟧 **Moderate risk:** 60 ≤ Predicted < 90 cases")
        st.markdown("🟥 **High risk:** Predicted ≥ 90 cases")
