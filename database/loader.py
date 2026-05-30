import pandas as pd
from loguru import logger
from database.schema import (
    get_session,
    WeatherForecast,
    WeatherHistory,
    ClimateIndicator,
    Region,
    RiskScore,
)
from config.settings import TARGET_REGIONS


# ─────────────────────────────────────────────
# SEED REGIONS
# ─────────────────────────────────────────────
def load_regions():
    """Seed the regions master table."""
    session = get_session()
    try:
        for r in TARGET_REGIONS:
            exists = session.query(Region).filter_by(
                city=r["name"], country=r["country"]
            ).first()
            if not exists:
                session.add(Region(
                    city=r["name"],
                    country=r["country"],
                    lat=r["lat"],
                    lon=r["lon"],
                ))
        session.commit()
        logger.success(f"✅ Regions seeded — {len(TARGET_REGIONS)} cities")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Region seed failed: {e}")
    finally:
        session.close()


# ─────────────────────────────────────────────
# LOAD WEATHER FORECASTS
# ─────────────────────────────────────────────
def load_weather_forecast(df: pd.DataFrame):
    """Load forecast data into weather_forecasts table, skip duplicates."""
    if df.empty:
        logger.warning("⚠️ Forecast dataframe is empty — nothing to load")
        return

    session = get_session()
    loaded = 0
    skipped = 0
    try:
        for _, row in df.iterrows():
            exists = session.query(WeatherForecast).filter_by(
                city=row["city"],
                country=row["country"],
                date=str(row["date"])
            ).first()
            if not exists:
                session.add(WeatherForecast(
                    city=row["city"],
                    country=row["country"],
                    date=str(row["date"]),
                    temperature_2m_max=row.get("temperature_2m_max"),
                    temperature_2m_min=row.get("temperature_2m_min"),
                    precipitation_sum=row.get("precipitation_sum"),
                    windspeed_10m_max=row.get("windspeed_10m_max"),
                    et0_fao_evapotranspiration=row.get("et0_fao_evapotranspiration"),
                    weathercode=row.get("weathercode"),
                    lat=row.get("lat"),
                    lon=row.get("lon"),
                    fetched_at=row.get("fetched_at"),
                ))
                loaded += 1
            else:
                skipped += 1
        session.commit()
        logger.success(f"✅ Forecast loaded: {loaded} new | {skipped} skipped")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Forecast load failed: {e}")
    finally:
        session.close()


# ─────────────────────────────────────────────
# LOAD WEATHER HISTORY
# ─────────────────────────────────────────────
def load_weather_history(df: pd.DataFrame):
    """Load historical weather data into weather_history table, skip duplicates."""
    if df.empty:
        logger.warning("⚠️ History dataframe is empty — nothing to load")
        return

    session = get_session()
    loaded = 0
    skipped = 0
    try:
        for _, row in df.iterrows():
            exists = session.query(WeatherHistory).filter_by(
                city=row["city"],
                country=row["country"],
                date=str(row["date"])
            ).first()
            if not exists:
                session.add(WeatherHistory(
                    city=row["city"],
                    country=row["country"],
                    date=str(row["date"]),
                    temperature_2m_max=row.get("temperature_2m_max"),
                    temperature_2m_min=row.get("temperature_2m_min"),
                    precipitation_sum=row.get("precipitation_sum"),
                    windspeed_10m_max=row.get("windspeed_10m_max"),
                    et0_fao_evapotranspiration=row.get("et0_fao_evapotranspiration"),
                    weathercode=row.get("weathercode"),
                    lat=row.get("lat"),
                    lon=row.get("lon"),
                    fetched_at=row.get("fetched_at"),
                ))
                loaded += 1
            else:
                skipped += 1
        session.commit()
        logger.success(f"✅ History loaded: {loaded} new | {skipped} skipped")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ History load failed: {e}")
    finally:
        session.close()


# ─────────────────────────────────────────────
# LOAD WORLD BANK CLIMATE INDICATORS
# ─────────────────────────────────────────────
def load_climate_indicators(df: pd.DataFrame):
    """Load World Bank indicators into climate_indicators table, skip duplicates."""
    if df.empty:
        logger.warning("⚠️ Indicators dataframe is empty — nothing to load")
        return

    session = get_session()
    loaded = 0
    skipped = 0
    try:
        for _, row in df.iterrows():
            exists = session.query(ClimateIndicator).filter_by(
                country_code=row["country_code"],
                indicator=row["indicator"],
                year=int(row["year"])
            ).first()
            if not exists:
                session.add(ClimateIndicator(
                    country_code=row["country_code"],
                    country_name=row["country_name"],
                    indicator=row["indicator"],
                    year=int(row["year"]),
                    value=float(row["value"]),
                ))
                loaded += 1
            else:
                skipped += 1
        session.commit()
        logger.success(f"✅ Indicators loaded: {loaded} new | {skipped} skipped")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Indicator load failed: {e}")
    finally:
        session.close()


# ─────────────────────────────────────────────
# LOAD AI RISK SCORES
# ─────────────────────────────────────────────
def load_risk_score(
    city: str,
    country: str,
    flood_risk: float,
    drought_risk: float,
    heatwave_risk: float,
    air_quality_risk: float,
    overall_risk: float,
    risk_level: str,
    ai_summary: str,
    raw_data_snapshot: str,
):
    """Save an AI-generated risk score for a city."""
    session = get_session()
    try:
        session.add(RiskScore(
            city=city,
            country=country,
            flood_risk=flood_risk,
            drought_risk=drought_risk,
            heatwave_risk=heatwave_risk,
            air_quality_risk=air_quality_risk,
            overall_risk=overall_risk,
            risk_level=risk_level,
            ai_summary=ai_summary,
            raw_data_snapshot=raw_data_snapshot,
        ))
        session.commit()
        logger.success(f"✅ Risk score saved — {city}, {country} | {risk_level} ({overall_risk:.1f}/100)")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Risk score save failed for {city}: {e}")
    finally:
        session.close()


# ─────────────────────────────────────────────
# QUERY HELPERS
# ─────────────────────────────────────────────
def get_latest_forecast(city: str, country: str) -> pd.DataFrame:
    """Retrieve the latest 7-day forecast for a city."""
    session = get_session()
    try:
        rows = session.query(WeatherForecast).filter_by(
            city=city, country=country
        ).order_by(WeatherForecast.date.desc()).limit(7).all()
        data = [{
            "date": r.date,
            "temperature_2m_max": r.temperature_2m_max,
            "temperature_2m_min": r.temperature_2m_min,
            "precipitation_sum": r.precipitation_sum,
            "windspeed_10m_max": r.windspeed_10m_max,
            "weathercode": r.weathercode,
        } for r in rows]
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"❌ Forecast query failed: {e}")
        return pd.DataFrame()
    finally:
        session.close()


def get_historical_summary(city: str, country: str) -> dict:
    """Get 30-day historical averages for a city."""
    session = get_session()
    try:
        rows = session.query(WeatherHistory).filter_by(
            city=city, country=country
        ).order_by(WeatherHistory.date.desc()).limit(30).all()

        if not rows:
            return {}

        temps = [r.temperature_2m_max for r in rows if r.temperature_2m_max]
        precip = [r.precipitation_sum for r in rows if r.precipitation_sum is not None]
        winds = [r.windspeed_10m_max for r in rows if r.windspeed_10m_max]

        return {
            "avg_temp_max": round(sum(temps) / len(temps), 2) if temps else None,
            "total_precipitation_30d": round(sum(precip), 2) if precip else 0,
            "avg_windspeed": round(sum(winds) / len(winds), 2) if winds else None,
            "days_with_rain": sum(1 for p in precip if p > 1.0),
            "days_no_rain": sum(1 for p in precip if p == 0.0),
        }
    except Exception as e:
        logger.error(f"❌ History query failed: {e}")
        return {}
    finally:
        session.close()


def get_country_indicators(country_code: str) -> dict:
    """Get latest World Bank indicators for a country."""
    session = get_session()
    try:
        rows = session.query(ClimateIndicator).filter_by(
            country_code=country_code
        ).order_by(ClimateIndicator.year.desc()).all()

        indicators = {}
        seen = set()
        for r in rows:
            if r.indicator not in seen:
                indicators[r.indicator] = {
                    "value": r.value,
                    "year": r.year
                }
                seen.add(r.indicator)
        return indicators
    except Exception as e:
        logger.error(f"❌ Indicator query failed: {e}")
        return {}
    finally:
        session.close()


def get_all_latest_risk_scores() -> pd.DataFrame:
    """Get the most recent risk score for every city."""
    session = get_session()
    try:
        from sqlalchemy import func
        subq = session.query(
            RiskScore.city,
            func.max(RiskScore.scored_at).label("latest")
        ).group_by(RiskScore.city).subquery()

        rows = session.query(RiskScore).join(
            subq,
            (RiskScore.city == subq.c.city) &
            (RiskScore.scored_at == subq.c.latest)
        ).all()

        data = [{
            "city": r.city,
            "country": r.country,
            "overall_risk": r.overall_risk,
            "risk_level": r.risk_level,
            "flood_risk": r.flood_risk,
            "drought_risk": r.drought_risk,
            "heatwave_risk": r.heatwave_risk,
            "air_quality_risk": r.air_quality_risk,
            "ai_summary": r.ai_summary,
            "scored_at": r.scored_at,
        } for r in rows]
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"❌ Risk score query failed: {e}")
        return pd.DataFrame()
    finally:
        session.close()


# ─────────────────────────────────────────────
# MAIN — seed + verify
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🌱 Seeding regions...")
    load_regions()

    logger.info("🔍 Verifying query helpers...")
    summary = get_historical_summary("Nairobi", "Kenya")
    logger.info(f"Nairobi 30-day summary: {summary}")

    indicators = get_country_indicators("KE")
    logger.info(f"Kenya indicators: {indicators}")