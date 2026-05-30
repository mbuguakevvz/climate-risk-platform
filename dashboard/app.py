import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.loader import (
    get_all_latest_risk_scores,
    get_latest_forecast,
    get_historical_summary,
)
from ai_engine.risk_scorer import score_all_cities, score_city, COUNTRY_CODES
from config.settings import TARGET_REGIONS

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Climate Risk Intelligence Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    .main { background-color: #0a0f1e; }

    .risk-card {
        background: linear-gradient(135deg, #1a1f35 0%, #0d1526 100%);
        border: 1px solid #2a3a5c;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }

    .metric-critical { color: #ff4757; font-weight: 700; }
    .metric-high     { color: #ff6b35; font-weight: 700; }
    .metric-medium   { color: #ffa502; font-weight: 700; }
    .metric-low      { color: #2ed573; font-weight: 700; }

    .header-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #0099cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }

    .header-sub {
        color: #8899aa;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    .stMetric label { color: #8899aa !important; font-size: 0.8rem !important; }
    .stMetric value { color: #ffffff !important; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1526 0%, #0a0f1e 100%);
        border-right: 1px solid #2a3a5c;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
LEVEL_COLORS = {
    "CRITICAL": "#ff4757",
    "HIGH":     "#ff6b35",
    "MEDIUM":   "#ffa502",
    "LOW":      "#2ed573",
}

def level_badge(level: str) -> str:
    color = LEVEL_COLORS.get(level, "#888")
    return f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600">{level}</span>'

@st.cache_data(ttl=300)
def load_risk_data() -> pd.DataFrame:
    return get_all_latest_risk_scores()

@st.cache_data(ttl=300)
def load_forecast(city, country):
    return get_latest_forecast(city, country)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 Climate Risk Platform")
    st.markdown("---")

    page = st.radio("Navigate", [
        "🗺️ Global Overview",
        "🏙️ City Deep Dive",
        "📊 Risk Analytics",
        "🔄 Run Scoring Engine",
    ])

    st.markdown("---")
    st.markdown("### Filters")
    risk_filter = st.multiselect(
        "Risk Level",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    )

    st.markdown("---")
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    st.caption("Data: Open-Meteo · World Bank · Rule-based AI Engine")


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df = load_risk_data()

if df.empty:
    st.warning("⚠️ No risk scores found. Go to **Run Scoring Engine** to generate scores.")
    df = pd.DataFrame()
else:
    if risk_filter:
        df = df[df["risk_level"].isin(risk_filter)]


# ─────────────────────────────────────────────
# PAGE: GLOBAL OVERVIEW
# ─────────────────────────────────────────────
if page == "🗺️ Global Overview":

    st.markdown('<p class="header-title">🌍 Climate Risk Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-sub">Real-time climate risk assessment across 12 global cities · Powered by Open-Meteo & World Bank data</p>', unsafe_allow_html=True)
    st.markdown("---")

    if not df.empty:
        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            critical = len(df[df["risk_level"] == "CRITICAL"])
            st.metric("🔴 Critical Risk Cities", critical)
        with col2:
            high = len(df[df["risk_level"] == "HIGH"])
            st.metric("🟠 High Risk Cities", high)
        with col3:
            avg_risk = df["overall_risk"].mean()
            st.metric("📊 Avg Global Risk Score", f"{avg_risk:.1f}/100")
        with col4:
            top_city = df.loc[df["overall_risk"].idxmax()]
            st.metric("⚠️ Highest Risk City", top_city["city"])

        st.markdown("---")

        # World map
        st.markdown("### 🗺️ Global Risk Map")

        region_lookup = {r["name"]: r for r in TARGET_REGIONS}
        df["lat"] = df["city"].map(lambda c: region_lookup.get(c, {}).get("lat"))
        df["lon"] = df["city"].map(lambda c: region_lookup.get(c, {}).get("lon"))
        df["color"] = df["risk_level"].map(LEVEL_COLORS)
        df["size"] = df["overall_risk"] * 1.2

        fig_map = px.scatter_geo(
            df,
            lat="lat", lon="lon",
            color="risk_level",
            size="size",
            hover_name="city",
            hover_data={
                "country": True,
                "overall_risk": ":.1f",
                "flood_risk": ":.1f",
                "drought_risk": ":.1f",
                "heatwave_risk": ":.1f",
                "lat": False, "lon": False, "size": False, "color": False
            },
            color_discrete_map=LEVEL_COLORS,
            projection="natural earth",
            title="",
        )
        fig_map.update_layout(
            paper_bgcolor="#0a0f1e",
            plot_bgcolor="#0a0f1e",
            geo=dict(
                bgcolor="#0d1526",
                landcolor="#1a2744",
                oceancolor="#0a0f1e",
                showocean=True,
                lakecolor="#0a0f1e",
                showland=True,
                showcountries=True,
                countrycolor="#2a3a5c",
            ),
            legend=dict(bgcolor="#0d1526", font=dict(color="#ffffff")),
            margin=dict(l=0, r=0, t=10, b=0),
            height=480,
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.markdown("---")

        # Risk table
        st.markdown("### 📋 City Risk Rankings")
        display_df = df[[
            "city", "country", "overall_risk", "risk_level",
            "flood_risk", "drought_risk", "heatwave_risk", "air_quality_risk"
        ]].sort_values("overall_risk", ascending=False).reset_index(drop=True)

        display_df.index += 1

        st.dataframe(
            display_df.style
                .background_gradient(subset=["overall_risk"], cmap="RdYlGn_r")
                .background_gradient(subset=["flood_risk"], cmap="Blues")
                .background_gradient(subset=["drought_risk"], cmap="YlOrBr")
                .background_gradient(subset=["heatwave_risk"], cmap="Reds")
                .format({
                    "overall_risk": "{:.1f}",
                    "flood_risk": "{:.1f}",
                    "drought_risk": "{:.1f}",
                    "heatwave_risk": "{:.1f}",
                    "air_quality_risk": "{:.1f}",
                }),
            use_container_width=True,
            height=420,
        )


# ─────────────────────────────────────────────
# PAGE: CITY DEEP DIVE
# ─────────────────────────────────────────────
elif page == "🏙️ City Deep Dive":
    st.markdown("### 🏙️ City Deep Dive")

    all_cities = [(r["name"], r["country"]) for r in TARGET_REGIONS]
    city_options = [f"{c}, {co}" for c, co in all_cities]
    selected = st.selectbox("Select a city", city_options)
    city, country = selected.split(", ", 1)

    if not df.empty:
        city_data = df[df["city"] == city]
        if not city_data.empty:
            row = city_data.iloc[0]

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"## {city}")
                st.markdown(f"**{country}**")
                level = row["risk_level"]
                color = LEVEL_COLORS.get(level, "#888")
                st.markdown(f'<h2 style="color:{color}">{level} RISK</h2>', unsafe_allow_html=True)
                st.metric("Overall Score", f"{row['overall_risk']:.1f} / 100")
                st.markdown("---")
                st.markdown("#### AI Risk Summary")
                st.info(row["ai_summary"])

            with col2:
                # Radar chart
                categories = ["Flood", "Drought", "Heatwave", "Air Quality"]
                values = [
                    row["flood_risk"], row["drought_risk"],
                    row["heatwave_risk"], row["air_quality_risk"]
                ]
                values_closed = values + [values[0]]
                categories_closed = categories + [categories[0]]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=values_closed,
                    theta=categories_closed,
                    fill="toself",
                    fillcolor=f"rgba(0,212,255,0.15)",
                    line=dict(color="#00d4ff", width=2),
                    name=city,
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor="#0d1526",
                        radialaxis=dict(visible=True, range=[0, 100], color="#8899aa"),
                        angularaxis=dict(color="#ffffff"),
                    ),
                    paper_bgcolor="#0a0f1e",
                    plot_bgcolor="#0a0f1e",
                    font=dict(color="#ffffff"),
                    showlegend=False,
                    height=350,
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # Forecast chart
            st.markdown("---")
            st.markdown("#### 📅 7-Day Weather Forecast")
            forecast_df = load_forecast(city, country)
            if not forecast_df.empty:
                fig_forecast = go.Figure()
                fig_forecast.add_trace(go.Bar(
                    x=forecast_df["date"],
                    y=forecast_df["precipitation_sum"],
                    name="Precipitation (mm)",
                    marker_color="#00d4ff",
                    yaxis="y2",
                    opacity=0.6,
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["temperature_2m_max"],
                    name="Max Temp (°C)",
                    line=dict(color="#ff4757", width=2),
                    mode="lines+markers",
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["temperature_2m_min"],
                    name="Min Temp (°C)",
                    line=dict(color="#2ed573", width=2, dash="dot"),
                    mode="lines+markers",
                ))
                fig_forecast.update_layout(
                    paper_bgcolor="#0a0f1e",
                    plot_bgcolor="#0d1526",
                    font=dict(color="#ffffff"),
                    legend=dict(bgcolor="#0d1526"),
                    xaxis=dict(gridcolor="#2a3a5c"),
                    yaxis=dict(title="Temperature (°C)", gridcolor="#2a3a5c"),
                    yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right", gridcolor="#2a3a5c"),
                    height=320,
                    margin=dict(l=10, r=10, t=10, b=10),
                )
                st.plotly_chart(fig_forecast, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE: RISK ANALYTICS
# ─────────────────────────────────────────────
elif page == "📊 Risk Analytics":
    st.markdown("### 📊 Risk Analytics")

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Risk level distribution
            level_counts = df["risk_level"].value_counts().reset_index()
            level_counts.columns = ["Risk Level", "Count"]
            fig_pie = px.pie(
                level_counts, names="Risk Level", values="Count",
                color="Risk Level", color_discrete_map=LEVEL_COLORS,
                title="Risk Level Distribution",
            )
            fig_pie.update_layout(
                paper_bgcolor="#0a0f1e",
                plot_bgcolor="#0a0f1e",
                font=dict(color="#ffffff"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Risk components comparison
            fig_bar = px.bar(
                df.sort_values("overall_risk", ascending=True),
                x="overall_risk", y="city",
                orientation="h",
                color="risk_level",
                color_discrete_map=LEVEL_COLORS,
                title="Overall Risk Score by City",
                labels={"overall_risk": "Risk Score", "city": ""},
            )
            fig_bar.update_layout(
                paper_bgcolor="#0a0f1e",
                plot_bgcolor="#0d1526",
                font=dict(color="#ffffff"),
                xaxis=dict(gridcolor="#2a3a5c", range=[0, 100]),
                yaxis=dict(gridcolor="#2a3a5c"),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Risk components heatmap
        st.markdown("---")
        st.markdown("#### 🌡️ Risk Components Heatmap")
        heat_df = df[["city", "flood_risk", "drought_risk", "heatwave_risk", "air_quality_risk"]].set_index("city")
        fig_heat = px.imshow(
            heat_df,
            color_continuous_scale="RdYlGn_r",
            title="",
            labels=dict(color="Risk Score"),
            zmin=0, zmax=100,
            aspect="auto",
        )
        fig_heat.update_layout(
            paper_bgcolor="#0a0f1e",
            plot_bgcolor="#0d1526",
            font=dict(color="#ffffff"),
            height=420,
        )
        st.plotly_chart(fig_heat, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE: RUN SCORING ENGINE
# ─────────────────────────────────────────────
elif page == "🔄 Run Scoring Engine":
    st.markdown("### 🔄 Run Scoring Engine")
    st.markdown("Fetch fresh data and recalculate risk scores for all 12 cities.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌍 Score All 12 Cities", type="primary", use_container_width=True):
            with st.spinner("Running risk scoring engine..."):
                results = score_all_cities()
                st.cache_data.clear()
            st.success(f"✅ Scored {len(results)} cities successfully!")
            st.dataframe(pd.DataFrame(results)[[
                "city", "country", "overall_risk", "risk_level",
                "flood_risk", "drought_risk", "heatwave_risk", "air_quality_risk"
            ]].sort_values("overall_risk", ascending=False))

    with col2:
        st.markdown("**Score a single city:**")
        city_options = [f"{r['name']}, {r['country']}" for r in TARGET_REGIONS]
        selected_city = st.selectbox("Select city", city_options)
        if st.button("📊 Score Selected City", use_container_width=True):
            city, country = selected_city.split(", ", 1)
            with st.spinner(f"Scoring {city}..."):
                result = score_city(city, country)
                st.cache_data.clear()
            if result:
                st.success(f"✅ {city} scored!")
                st.json(result)