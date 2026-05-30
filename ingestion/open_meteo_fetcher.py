import requests
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from config.settings import TARGET_REGIONS

BASE_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
    "et0_fao_evapotranspiration",
    "weathercode",
]

def fetch_forecast(region: dict, days: int = 7) -> pd.DataFrame:
    """Fetch 7-day weather forecast for a region."""
    params = {
        "latitude": region["lat"],
        "longitude": region["lon"],
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "forecast_days": days,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["daily"]

        df = pd.DataFrame(data)
        df["city"] = region["name"]
        df["country"] = region["country"]
        df["lat"] = region["lat"]
        df["lon"] = region["lon"]
        df["fetched_at"] = datetime.utcnow()
        df.rename(columns={"time": "date"}, inplace=True)
        logger.success(f"✅ Open-Meteo forecast fetched — {region['name']}, {len(df)} days")
        return df

    except Exception as e:
        logger.error(f"❌ Failed fetching Open-Meteo for {region['name']}: {e}")
        return pd.DataFrame()


def fetch_historical(region: dict, days_back: int = 30) -> pd.DataFrame:
    """Fetch last N days of historical weather for a region."""
    end_date = datetime.utcnow().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)

    params = {
        "latitude": region["lat"],
        "longitude": region["lon"],
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    url = "https://archive-api.open-meteo.com/v1/archive"

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["daily"]

        df = pd.DataFrame(data)
        df["city"] = region["name"]
        df["country"] = region["country"]
        df["lat"] = region["lat"]
        df["lon"] = region["lon"]
        df["fetched_at"] = datetime.utcnow()
        df.rename(columns={"time": "date"}, inplace=True)
        logger.success(f"✅ Historical weather fetched — {region['name']}, {len(df)} days")
        return df

    except Exception as e:
        logger.error(f"❌ Failed fetching history for {region['name']}: {e}")
        return pd.DataFrame()


def fetch_all_regions(mode: str = "forecast") -> pd.DataFrame:
    """Fetch data for all 12 cities."""
    all_data = []
    for region in TARGET_REGIONS:
        if mode == "forecast":
            df = fetch_forecast(region)
        else:
            df = fetch_historical(region)
        if not df.empty:
            all_data.append(df)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"📦 Total records fetched: {len(combined)}")
        return combined
    return pd.DataFrame()


if __name__ == "__main__":
    logger.info("🌍 Fetching forecast data for all cities...")
    df = fetch_all_regions(mode="forecast")
    if not df.empty:
        print(df[["city", "country", "date", "temperature_2m_max", "precipitation_sum"]].to_string())