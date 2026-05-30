import json
from loguru import logger
from config.settings import TARGET_REGIONS
from database.loader import (
    get_latest_forecast,
    get_historical_summary,
    get_country_indicators,
    load_risk_score,
)

COUNTRY_CODES = {
    "Kenya": "KE", "Nigeria": "NG", "Egypt": "EG",
    "India": "IN", "Indonesia": "ID", "Brazil": "BR",
    "USA": "US", "UK": "GB", "China": "CN",
    "Australia": "AU", "Bangladesh": "BD", "Pakistan": "PK",
}


def calculate_flood_risk(history: dict, forecast: list) -> float:
    """High precipitation + many rain days = flood risk."""
    score = 0.0
    total_precip = history.get("total_precipitation_30d", 0) or 0
    rain_days = history.get("days_with_rain", 0) or 0

    # 30-day precipitation scoring
    if total_precip > 300:   score += 40
    elif total_precip > 150: score += 25
    elif total_precip > 80:  score += 15
    elif total_precip > 30:  score += 8

    # Rain frequency scoring
    if rain_days > 20:  score += 30
    elif rain_days > 12: score += 20
    elif rain_days > 6:  score += 10

    # Forecast precipitation (next 7 days)
    forecast_precip = sum(d.get("precipitation_sum") or 0 for d in forecast)
    if forecast_precip > 100: score += 30
    elif forecast_precip > 50: score += 20
    elif forecast_precip > 20: score += 10

    return min(round(score, 1), 100.0)


def calculate_drought_risk(history: dict, indicators: dict) -> float:
    """Low rainfall + high evapotranspiration + freshwater stress = drought risk."""
    score = 0.0
    total_precip = history.get("total_precipitation_30d", 0) or 0
    dry_days = history.get("days_no_rain", 0) or 0

    # Low precipitation = drought risk
    if total_precip < 10:   score += 45
    elif total_precip < 30: score += 30
    elif total_precip < 60: score += 15
    elif total_precip < 100: score += 5

    # Dry days
    if dry_days > 25:  score += 30
    elif dry_days > 18: score += 20
    elif dry_days > 10: score += 10

    # Freshwater stress from World Bank
    fw = indicators.get("freshwater_stress_pct", {}).get("value")
    if fw:
        if fw > 80:   score += 25
        elif fw > 50: score += 15
        elif fw > 25: score += 8

    return min(round(score, 1), 100.0)


def calculate_heatwave_risk(history: dict, forecast: list) -> float:
    """High temperatures in history and forecast = heatwave risk."""
    score = 0.0
    avg_temp = history.get("avg_temp_max") or 0

    # Historical average temperature
    if avg_temp > 40:   score += 45
    elif avg_temp > 35: score += 35
    elif avg_temp > 30: score += 20
    elif avg_temp > 25: score += 10

    # Forecast max temperatures
    forecast_temps = [d.get("temperature_2m_max") or 0 for d in forecast]
    if forecast_temps:
        max_forecast = max(forecast_temps)
        if max_forecast > 42:   score += 40
        elif max_forecast > 38: score += 30
        elif max_forecast > 33: score += 18
        elif max_forecast > 28: score += 8

    # Days above 35°C in forecast
    hot_days = sum(1 for t in forecast_temps if t > 35)
    score += hot_days * 3

    return min(round(score, 1), 100.0)


def calculate_air_quality_risk(indicators: dict) -> float:
    """PM2.5 levels and CO2 emissions drive air quality risk."""
    score = 0.0

    pm25 = indicators.get("pm25_air_pollution", {}).get("value")
    if pm25:
        if pm25 > 75:   score += 60
        elif pm25 > 50: score += 45
        elif pm25 > 35: score += 30
        elif pm25 > 15: score += 15
        elif pm25 > 10: score += 8

    co2 = indicators.get("co2_emissions_per_capita", {}).get("value")
    if co2:
        if co2 > 15:   score += 35
        elif co2 > 8:  score += 25
        elif co2 > 4:  score += 15
        elif co2 > 2:  score += 8

    # Forest area acts as buffer — more forest = less risk
    forest = indicators.get("forest_area_pct", {}).get("value")
    if forest:
        if forest > 60: score -= 10
        elif forest > 30: score -= 5

    return min(max(round(score, 1), 0.0), 100.0)


def calculate_overall_risk(flood, drought, heatwave, air) -> float:
    """Weighted average — flood and heat weighted slightly higher."""
    weighted = (flood * 0.30) + (drought * 0.25) + (heatwave * 0.30) + (air * 0.15)
    return round(weighted, 1)


def get_risk_level(score: float) -> str:
    if score >= 76: return "CRITICAL"
    elif score >= 51: return "HIGH"
    elif score >= 26: return "MEDIUM"
    return "LOW"


def generate_summary(city, country, flood, drought, heatwave, air, overall, level) -> str:
    """Generate a human-readable risk summary."""
    risks = {
        "flood": flood,
        "drought": drought,
        "heatwave": heatwave,
        "air quality": air
    }
    top_risks = sorted(risks.items(), key=lambda x: x[1], reverse=True)[:2]
    top_str = " and ".join([f"{k} ({v:.0f}/100)" for k, v in top_risks])

    return (
        f"{city}, {country} has an overall climate risk level of {level} ({overall:.1f}/100). "
        f"The highest risk factors are {top_str}. "
        f"Immediate attention is recommended for early warning systems and community preparedness."
        if overall > 50 else
        f"{city}, {country} has a {level} overall climate risk score of {overall:.1f}/100. "
        f"Primary concerns include {top_str}. "
        f"Continued monitoring is advised to detect emerging climate trends."
    )


def score_city(city: str, country: str) -> dict | None:
    """Score a single city using rule-based engine."""
    logger.info(f"📊 Scoring {city}, {country}...")

    forecast_df = get_latest_forecast(city, country)
    history = get_historical_summary(city, country)
    country_code = COUNTRY_CODES.get(country, "")
    indicators = get_country_indicators(country_code)

    if forecast_df.empty:
        logger.warning(f"⚠️ No forecast data for {city} — skipping")
        return None

    forecast = forecast_df.to_dict(orient="records")

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


def score_all_cities() -> list:
    """Score all 12 cities and print a summary table."""
    logger.info("🌍 Starting rule-based risk scoring for all cities...")
    results = []

    for region in TARGET_REGIONS:
        result = score_city(region["name"], region["country"])
        if result:
            results.append(result)

    logger.info(f"\n{'='*75}")
    logger.info(f"✅ Scoring complete — {len(results)}/{len(TARGET_REGIONS)} cities scored")
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


if __name__ == "__main__":
    score_all_cities()