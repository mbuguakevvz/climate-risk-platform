import requests
import pandas as pd
from loguru import logger

BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"

INDICATORS = {
    "EN.ATM.CO2E.PC":     "co2_emissions_per_capita",
    "EN.CLC.DRSK.XQ":     "climate_risk_index",
    "AG.LND.FRST.ZS":     "forest_area_pct",
    "ER.H2O.FWST.ZS":     "freshwater_stress_pct",
    "EN.ATM.PM25.MC.M3":  "pm25_air_pollution",
}

COUNTRY_CODES = {
    "Kenya": "KE", "Nigeria": "NG", "Egypt": "EG",
    "India": "IN", "Indonesia": "ID", "Brazil": "BR",
    "USA": "US", "UK": "GB", "China": "CN",
    "Australia": "AU", "Bangladesh": "BD", "Pakistan": "PK",
}

def fetch_indicator(country_code: str, indicator_code: str, indicator_name: str) -> pd.DataFrame:
    url = BASE_URL.format(country=country_code, indicator=indicator_code)
    params = {"format": "json", "mrv": 5, "per_page": 10}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        if len(payload) < 2 or not payload[1]:
            return pd.DataFrame()

        records = []
        for entry in payload[1]:
            if entry.get("value") is not None:
                records.append({
                    "country_code": country_code,
                    "country_name": entry["country"]["value"],
                    "indicator": indicator_name,
                    "year": int(entry["date"]),
                    "value": float(entry["value"]),
                })

        df = pd.DataFrame(records)
        logger.success(f"✅ World Bank — {country_code} | {indicator_name} | {len(df)} records")
        return df

    except Exception as e:
        logger.error(f"❌ World Bank failed {country_code}/{indicator_name}: {e}")
        return pd.DataFrame()


def fetch_all() -> pd.DataFrame:
    all_data = []
    for country, code in COUNTRY_CODES.items():
        for ind_code, ind_name in INDICATORS.items():
            df = fetch_indicator(code, ind_code, ind_name)
            if not df.empty:
                all_data.append(df)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"📦 World Bank total records: {len(combined)}")
        return combined
    return pd.DataFrame()


if __name__ == "__main__":
    logger.info("🌍 Fetching World Bank climate indicators...")
    df = fetch_all()
    if not df.empty:
        print(df.to_string())