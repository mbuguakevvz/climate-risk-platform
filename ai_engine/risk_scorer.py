import json
import os
from loguru import logger
from config.settings import TARGET_REGIONS, ANTHROPIC_API_KEY
from database.loader import (
    get_latest_forecast,
    get_historical_summary,
    get_country_indicators,
    load_risk_score,
)

# ─────────────────────────────────────────────
# CONFIG — auto-switches to AI when key exists
# ─────────────────────────────────────────────
USE_AI_SCORING = bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.strip() != "")

COUNTRY_CODES = {
    "Kenya": "KE", "Nigeria": "NG", "Egypt": "EG",
    "India": "IN", "Indonesia": "ID", "Brazil": "BR",
    "USA": "US", "UK": "GB", "China": "CN",
    "Australia": "AU", "Bangladesh": "BD", "Pakistan": "PK",
}


# ─────────────────────────────────────────────
# RULE-BASED SCORING FUNCTIONS
# ─────────────────────────────────────────────
def calculate_flood_risk(history: dict, forecast: list) -> float:
    """High precipitation + many rain days = flood risk."""
    score = 0.0
    total_precip = history.get("total_precipitation_30d", 0) or 0
    rain_days    = history.get("days_with_rain", 0) or 0

    if total_precip > 300:    score += 40
    elif total_precip > 150:  score += 25
    elif total_precip > 80:   score += 15
    elif total_precip > 30:   score += 8

    if rain_days > 20:   score += 30
    elif rain_days > 12: score += 20
    elif rain_days > 6:  score += 10

    forecast_precip = sum(d.get("precipitation_sum") or 0 for d in forecast)
    if forecast_precip > 100:  score += 30
    elif forecast_precip > 50: score += 20
    elif forecast_precip > 20: score += 10

    return min(round(score, 1), 100.0)


def calculate_drought_risk(history: dict, indicators: dict) -> float:
    """Low rainfall + high evapotranspiration + freshwater stress = drought risk."""
    score = 0.0
    total_precip = history.get("total_precipitation_30d", 0) or 0
    dry_days     = history.get("days_no_rain", 0) or 0

    if total_precip < 10:    score += 45
    elif total_precip < 30:  score += 30
    elif total_precip < 60:  score += 15
    elif total_precip < 100: score += 5

    if dry_days > 25:   score += 30
    elif dry_days > 18: score += 20
    elif dry_days > 10: score += 10

    fw = indicators.get("freshwater_stress_pct", {}).get("value")
    if fw:
        if fw > 80:   score += 25
        elif fw > 50: score += 15
        elif fw > 25: score += 8

    return min(round(score, 1), 100.0)


def calculate_heatwave_risk(history: dict, forecast: list) -> float:
    """High temperatures in history and forecast = heatwave risk."""
    score    = 0.0
    avg_temp = history.get("avg_temp_max") or 0

    if avg_temp > 40:    score += 45
    elif avg_temp > 35:  score += 35
    elif avg_temp > 30:  score += 20
    elif avg_temp > 25:  score += 10

    forecast_temps = [d.get("temperature_2m_max") or 0 for d in forecast]
    if forecast_temps:
        max_forecast = max(forecast_temps)
        if max_forecast > 42:    score += 40
        elif max_forecast > 38:  score += 30
        elif max_forecast > 33:  score += 18
        elif max_forecast > 28:  score += 8

    hot_days = sum(1 for t in forecast_temps if t > 35)
    score += hot_days * 3

    return min(round(score, 1), 100.0)


def calculate_air_quality_risk(indicators: dict) -> float:
    """PM2.5 levels and CO2 emissions drive air quality risk."""
    score = 0.0

    pm25 = indicators.get("pm25_air_pollution", {}).get("value")
    if pm25:
        if pm25 > 75:    score += 60
        elif pm25 > 50:  score += 45
        elif pm25 > 35:  score += 30
        elif pm25 > 15:  score += 15
        elif pm25 > 10:  score += 8

    co2 = indicators.get("co2_emissions_per_capita", {}).get("value")
    if co2:
        if co2 > 15:   score += 35
        elif co2 > 8:  score += 25
        elif co2 > 4:  score += 15
        elif co2 > 2:  score += 8

    forest = indicators.get("forest_area_pct", {}).get("value")
    if forest:
        if forest > 60:   score -= 10
        elif forest > 30: score -= 5

    return min(max(round(score, 1), 0.0), 100.0)


def calculate_overall_risk(flood: float, drought: float, heatwave: float, air: float) -> float:
    """Weighted average — flood and heat weighted slightly higher."""
    return round((flood * 0.30) + (drought * 0.25) + (heatwave * 0.30) + (air * 0.15), 1)


def get_risk_level(score: float) -> str:
    if score >= 76:   return "CRITICAL"
    elif score >= 51: return "HIGH"
    elif score >= 26: return "MEDIUM"
    return "LOW"


def generate_summary(city, country, flood, drought, heatwave, air, overall, level) -> str:
    """Generate a human-readable risk summary."""
    risks = {
        "flood": flood, "drought": drought,
        "heatwave": heatwave, "air quality": air
    }
    top_risks = sorted(risks.items(), key=lambda x: x[1], reverse=True)[:2]
    top_str   = " and ".join([f"{k} ({v:.0f}/100)" for k, v in top_risks])

    if overall > 50:
        return (
            f"{city}, {country} has an overall climate risk level of {level} ({overall:.1f}/100). "
            f"The highest risk factors are {top_str}. "
            f"Immediate attention is recommended for early warning systems and community preparedness."
        )
    return (
        f"{city}, {country} has a {level} overall climate risk score of {overall:.1f}/100. "
        f"Primary concerns include {top_str}. "
        f"Continued monitoring is advised to detect emerging climate trends."
    )


# ─────────────────────────────────────────────
# CLAUDE AI PROMPT BUILDER
# ─────────────────────────────────────────────
def build_prompt(city: str, country: str, forecast: list, history: dict, indicators: dict) -> str:
    return f"""
You are an expert climate risk analyst. Analyze this real climate data for {city}, {country}.

FORECAST (next 7 days):
{json.dumps(forecast, indent=2)}

HISTORICAL SUMMARY (last 30 days):
{json.dumps(history, indent=2)}

WORLD BANK CLIMATE INDICATORS:
{json.dumps(indicators, indent=2)}

Calculate risk scores from 0 to 100:
- flood_risk: Based on precipitation and rainfall patterns
- drought_risk: Based on low rainfall, evapotranspiration, freshwater stress
- heatwave_risk: Based on max temperatures and heat trends
- air_quality_risk: Based on PM2.5 and CO2 data
- overall_risk: Weighted average of all four risks

Risk levels: 0-25=LOW, 26-50=MEDIUM, 51-75=HIGH, 76-100=CRITICAL

Return ONLY a valid JSON object, nothing else:
{{
  "flood_risk": <float 0-100>,
  "drought_risk": <float 0-100>,
  "heatwave_risk": <float 0-100>,
  "air_quality_risk": <float 0-100>,
  "overall_risk": <float 0-100>,
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "ai_summary": "<2-3 sentence human-readable risk summary for this city>"
}}
"""


# ─────────────────────────────────────────────
# RULE-BASED SCORER
# ─────────────────────────────────────────────
def _score_with_rules(city, country, forecast, history, indicators) -> dict:
    """Score a city using the rule-based engine."""
    flood    = calculate_flood_risk(history, forecast)
    drought  = calculate_drought_risk(history, indicators)
    heatwave = calculate_heatwave_risk(history, forecast)
    air      = calculate_air_quality_risk(indicators)
    overall  = calculate_overall_risk(flood, drought, heatwave, air)
    level    = get_risk_level(overall)
    summary  = generate_summary(city, country, flood, drought, heatwave, air, overall, level)

    load_risk_score(
        city=city,
        country=country,
        flood_risk=flood,
        drought_risk=drought,
        heatwave_risk=heatwave,
        air_quality_risk=air,
        overall_risk=overall,
        risk_level=level,
        ai_summary=summary,
        raw_data_snapshot=json.dumps({
            "forecast": forecast,
            "history": history,
            "indicators": indicators,
        }),
    )

    return {
        "city": city, "country": country,
        "flood_risk": flood, "drought_risk": drought,
        "heatwave_risk": heatwave, "air_quality_risk": air,
        "overall_risk": overall, "risk_level": level,
        "ai_summary": summary,
    }


# ─────────────────────────────────────────────
# CLAUDE AI SCORER
# ─────────────────────────────────────────────
def _score_with_claude(city, country, forecast, history, indicators) -> dict:
    """Score a city using Claude API — falls back to rules on failure."""
    try:
        import anthropic
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt  = build_prompt(city, country, forecast, history, indicators)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)

        load_risk_score(
            city=city,
            country=country,
            flood_risk=result["flood_risk"],
            drought_risk=result["drought_risk"],
            heatwave_risk=result["heatwave_risk"],
            air_quality_risk=result["air_quality_risk"],
            overall_risk=result["overall_risk"],
            risk_level=result["risk_level"],
            ai_summary=result["ai_summary"],
            raw_data_snapshot=json.dumps({
                "forecast": forecast,
                "history": history,
                "indicators": indicators,
            }),
        )

        logger.success(f"🤖 Claude scored {city} — {result['risk_level']} ({result['overall_risk']:.1f}/100)")
        return {"city": city, "country": country, **result}

    except Exception as e:
        logger.error(f"❌ Claude API failed for {city}: {e} — falling back to rule-based")
        return _score_with_rules(city, country, forecast, history, indicators)


# ─────────────────────────────────────────────
# MAIN SCORER — auto-selects AI or rules
# ─────────────────────────────────────────────
def score_city(city: str, country: str) -> dict | None:
    """Score a single city — uses Claude AI if key is set, else rule-based."""
    mode = "AI 🤖" if USE_AI_SCORING else "Rule-based 📐"
    logger.info(f"📊 Scoring {city}, {country} [{mode}]...")

    forecast_df = get_latest_forecast(city, country)
    history     = get_historical_summary(city, country)
    country_code = COUNTRY_CODES.get(country, "")
    indicators  = get_country_indicators(country_code)

    if forecast_df.empty:
        logger.warning(f"⚠️ No forecast data for {city} — skipping")
        return None

    forecast = forecast_df.to_dict(orient="records")

    if USE_AI_SCORING:
        return _score_with_claude(city, country, forecast, history, indicators)
    else:
        return _score_with_rules(city, country, forecast, history, indicators)


def score_all_cities() -> list:
    """Score all 12 cities and print a summary table."""
    mode = "Claude AI 🤖" if USE_AI_SCORING else "Rule-based Engine 📐"
    logger.info(f"🌍 Starting risk scoring for all cities using {mode}...")

    results = []
    for region in TARGET_REGIONS:
        result = score_city(region["name"], region["country"])
        if result:
            results.append(result)

    logger.info(f"\n{'='*75}")
    logger.info(f"✅ Scoring complete — {len(results)}/{len(TARGET_REGIONS)} cities scored via {mode}")
    logger.info(f"{'='*75}\n")

    print(f"\n{'CITY':<15} {'COUNTRY':<12} {'OVERALL':>8} {'LEVEL':<10} {'FLOOD':>6} {'DROUGHT':>8} {'HEAT':>6} {'AIR':>5}")
    print("-" * 75)
    for r in sorted(results, key=lambda x: x["overall_risk"], reverse=True):
        print(
            f"{r['city']:<15} {r['country']:<12} "
            f"{r['overall_risk']:>7.1f} {r['risk_level']:<10} "
            f"{r['flood_risk']:>6.1f} {r['drought_risk']:>8.1f} "
            f"{r['heatwave_risk']:>6.1f} {r['air_quality_risk']:>5.1f}"
        )

    return results


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"🔧 AI Scoring: {'ENABLED' if USE_AI_SCORING else 'DISABLED — using rule-based engine'}")
    score_all_cities()