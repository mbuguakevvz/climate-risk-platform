import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "climate_risk_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# APIs
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# App
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Target regions for global coverage
TARGET_REGIONS = [
    {"name": "Nairobi", "country": "Kenya", "lat": -1.286389, "lon": 36.817223},
    {"name": "Lagos", "country": "Nigeria", "lat": 6.524379, "lon": 3.379206},
    {"name": "Cairo", "country": "Egypt", "lat": 30.044420, "lon": 31.235712},
    {"name": "Mumbai", "country": "India", "lat": 19.076090, "lon": 72.877426},
    {"name": "Jakarta", "country": "Indonesia", "lat": -6.208763, "lon": 106.845599},
    {"name": "São Paulo", "country": "Brazil", "lat": -23.550520, "lon": -46.633308},
    {"name": "New York", "country": "USA", "lat": 40.712776, "lon": -74.005974},
    {"name": "London", "country": "UK", "lat": 51.507351, "lon": -0.127758},
    {"name": "Beijing", "country": "China", "lat": 39.904202, "lon": 116.407394},
    {"name": "Sydney", "country": "Australia", "lat": -33.868820, "lon": 151.209290},
    {"name": "Dhaka", "country": "Bangladesh", "lat": 23.810332, "lon": 90.412521},
    {"name": "Karachi", "country": "Pakistan", "lat": 24.860966, "lon": 67.010011},
]