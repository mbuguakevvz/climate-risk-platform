from sqlalchemy import (
    create_engine, Column, String, Float, Integer,
    DateTime, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from loguru import logger
from config.settings import DATABASE_URL

Base = declarative_base()

# ─────────────────────────────────────────────
# TABLE 1: Cities / Regions master list
# ─────────────────────────────────────────────
class Region(Base):
    __tablename__ = "regions"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    city        = Column(String(100), nullable=False)
    country     = Column(String(100), nullable=False)
    country_code= Column(String(5))
    lat         = Column(Float, nullable=False)
    lon         = Column(Float, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("city", "country", name="uq_city_country"),
    )

# ─────────────────────────────────────────────
# TABLE 2: Daily weather forecasts
# ─────────────────────────────────────────────
class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    city                    = Column(String(100), nullable=False)
    country                 = Column(String(100), nullable=False)
    date                    = Column(String(20), nullable=False)
    temperature_2m_max      = Column(Float)
    temperature_2m_min      = Column(Float)
    precipitation_sum       = Column(Float)
    windspeed_10m_max       = Column(Float)
    et0_fao_evapotranspiration = Column(Float)
    weathercode             = Column(Integer)
    lat                     = Column(Float)
    lon                     = Column(Float)
    fetched_at              = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("city", "country", "date", name="uq_forecast_city_date"),
        Index("idx_forecast_city_date", "city", "date"),
    )

# ─────────────────────────────────────────────
# TABLE 3: Historical weather data
# ─────────────────────────────────────────────
class WeatherHistory(Base):
    __tablename__ = "weather_history"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    city                    = Column(String(100), nullable=False)
    country                 = Column(String(100), nullable=False)
    date                    = Column(String(20), nullable=False)
    temperature_2m_max      = Column(Float)
    temperature_2m_min      = Column(Float)
    precipitation_sum       = Column(Float)
    windspeed_10m_max       = Column(Float)
    et0_fao_evapotranspiration = Column(Float)
    weathercode             = Column(Integer)
    lat                     = Column(Float)
    lon                     = Column(Float)
    fetched_at              = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("city", "country", "date", name="uq_history_city_date"),
        Index("idx_history_city_date", "city", "date"),
    )

# ─────────────────────────────────────────────
# TABLE 4: World Bank climate indicators
# ─────────────────────────────────────────────
class ClimateIndicator(Base):
    __tablename__ = "climate_indicators"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    country_code    = Column(String(5), nullable=False)
    country_name    = Column(String(100))
    indicator       = Column(String(100), nullable=False)
    year            = Column(Integer, nullable=False)
    value           = Column(Float)
    fetched_at      = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("country_code", "indicator", "year", name="uq_indicator"),
        Index("idx_indicator_country_year", "country_code", "year"),
    )

# ─────────────────────────────────────────────
# TABLE 5: AI Risk Scores (Phase 5)
# ─────────────────────────────────────────────
class RiskScore(Base):
    __tablename__ = "risk_scores"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    city                = Column(String(100), nullable=False)
    country             = Column(String(100), nullable=False)
    scored_at           = Column(DateTime, default=datetime.utcnow)
    flood_risk          = Column(Float)   # 0-100
    drought_risk        = Column(Float)   # 0-100
    heatwave_risk       = Column(Float)   # 0-100
    air_quality_risk    = Column(Float)   # 0-100
    overall_risk        = Column(Float)   # 0-100
    risk_level          = Column(String(20))  # LOW / MEDIUM / HIGH / CRITICAL
    ai_summary          = Column(Text)
    raw_data_snapshot   = Column(Text)    # JSON snapshot of input data

    __table_args__ = (
        Index("idx_risk_city_date", "city", "scored_at"),
    )


# ─────────────────────────────────────────────
# Database connection & table creation
# ─────────────────────────────────────────────
def get_engine():
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def create_all_tables():
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.success("✅ All database tables created successfully")

def drop_all_tables():
    engine = get_engine()
    Base.metadata.drop_all(engine)
    logger.warning("⚠️ All tables dropped")


if __name__ == "__main__":
    logger.info("🗄️ Creating database schema...")
    create_all_tables()