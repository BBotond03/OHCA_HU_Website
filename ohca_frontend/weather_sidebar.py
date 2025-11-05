# weather_sidebar.py
import streamlit as st
from datetime import datetime

def _fmt_temp(x):
    try: return f"{float(x):.1f} °C"
    except: return "N/A"

def _fmt_hum(x):
    try: return f"{int(round(float(x)))}%"
    except: return "N/A"

def _fmt_pct01(x):
    try: return f"{float(x)*100:.1f}%"
    except: return "N/A"

def _fmt_date(s):
    try: return datetime.strptime(s, "%Y-%m-%d").strftime("%a %b %d")
    except: return s or "N/A"

def _fmt_ratio(x):
    try:
        fx = float(x)
        return f"{fx:.2f}"
    except:
        return "—"

def _risk_chip(label, ratio, emoji):
    return f"{emoji} **{label}:** {_fmt_ratio(ratio)}"

def render_weather_sidebar(sidebar, county_name, county_data):
    # Pull forecast safely
    days = county_data.get("forecast_mean") or []
    tm = days[0] if len(days) > 0 else {}
    da = days[1] if len(days) > 1 else {}

    # =======================
    # Header
    # =======================
    sidebar.subheader(f"📍 {county_name}")

    # =======================
    # 1) Today — Daily Averages & Risk (no overall mix)
    # =======================
    t_today = county_data.get("temperature_mean_today")
    h_today = county_data.get("humidity_mean_today")
    risk_today = county_data.get("risk_today") or {}

    sidebar.markdown("### 📆 Today (daily averages & risk)")
    col1, col2 = sidebar.columns(2)
    with col1:
        sidebar.markdown(f"🌡️ Temp (mean): **{_fmt_temp(t_today)}**")
        sidebar.markdown(_risk_chip("Temp risk", risk_today.get("temp_ratio"), risk_today.get("temp_emoji", "⬜")))
    with col2:
        sidebar.markdown(f"💧 Humidity (mean): **{_fmt_hum(h_today)}**")
        sidebar.markdown(_risk_chip("Humidity risk", risk_today.get("rh_ratio"), risk_today.get("rh_emoji", "⬜")))

    # =======================
    # 2) Current Conditions
    # =======================
    sidebar.markdown("### ☁️ Current Conditions")
    sidebar.markdown(f"🌡️ Temperature: **{_fmt_temp(county_data.get('temperature'))}**")
    sidebar.markdown(f"💧 Humidity: **{_fmt_hum(county_data.get('humidity'))}**")
    if county_data.get("conditions"):
        sidebar.caption(f"Conditions: _{county_data['conditions']}_")

    # =======================
    # 3) Next 2 Days — Daily Averages & Risk (no overall mix)
    # =======================
    sidebar.markdown("### 🔮 Next 2 Days (daily averages & risk)")

    # Tomorrow
    sidebar.markdown(
        f"**🗓️ {_fmt_date(tm.get('date'))} (tomorrow)** · "
        f"{_fmt_temp(tm.get('temperature_mean'))} · {_fmt_hum(tm.get('humidity_mean'))}"
    )
    r_tm = (tm.get("risk") or {})
    sidebar.markdown(
        f"{_risk_chip('Temp', r_tm.get('temp_ratio'), r_tm.get('temp_emoji','⬜'))} · "
        f"{_risk_chip('Humidity', r_tm.get('rh_ratio'), r_tm.get('rh_emoji','⬜'))}"
    )

    # Day after
    sidebar.markdown(
        f"**🗓️ {_fmt_date(da.get('date'))} (day after)** · "
        f"{_fmt_temp(da.get('temperature_mean'))} · {_fmt_hum(da.get('humidity_mean'))}"
    )
    r_da = (da.get("risk") or {})
    sidebar.markdown(
        f"{_risk_chip('Temp', r_da.get('temp_ratio'), r_da.get('temp_emoji','⬜'))} · "
        f"{_risk_chip('Humidity', r_da.get('rh_ratio'), r_da.get('rh_emoji','⬜'))}"
    )

    # =======================
    # 4) Extra metrics (optional / unchanged)
    # =======================
    if "yesterday_cases" in county_data:
        sidebar.markdown(f"📅 Yesterday cases: **{county_data.get('yesterday_cases', 'N/A')}**")
    if "predicted_cases" in county_data:
        sidebar.markdown(f"🔮 Predicted cases: **{county_data.get('predicted_cases', 'N/A')}**")
    if "mortality_rate" in county_data:
        sidebar.markdown(f"⚰️ Mortality rate: **{_fmt_pct01(county_data.get('mortality_rate'))}**")

    # =======================
    # Legends
    # =======================
    with sidebar.expander("🧪 Risk Legend (ratio → color)", expanded=False):
        st.markdown("🟩 **Low**: R < 0.8")
        st.markdown("⬜ **Neutral-ish**: 0.8 ≤ R < 1.3")
        st.markdown("🟨 **Mild**: 1.3 ≤ R < 1.6")
        st.markdown("🟧 **Moderate**: 1.6 ≤ R < 2.3")
        st.markdown("🟥 **High**: R ≥ 2.3")

    with sidebar.expander("🗺️ Map Legend (predicted cases)", expanded=False):
        st.markdown("🟩 **Low:** Predicted < 60 cases")
        st.markdown("🟧 **Moderate:** 60 ≤ Predicted < 90 cases")
        st.markdown("🟥 **High:** Predicted ≥ 90 cases")
