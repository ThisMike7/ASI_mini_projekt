from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database_models import (
    AirQualityMeasurement,
    Base,
    City,
    CityScore,
    WeatherMeasurement,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def make_city(db, name="Warsaw", country="Poland", continent="Europe", lat=52.2, lon=21.0):
    city = City(name=name, country=country, continent=continent, latitude=lat, longitude=lon)
    db.add(city)
    db.flush()
    return city


def add_measurements(
    db,
    city,
    temperature=20.0,
    wind_speed=5.0,
    precipitation=0.0,
    pm10=10.0,
    pm25=5.0,
    score=85.0,
    at: datetime | None = None,
):
    ts = at or datetime.utcnow()
    db.add(WeatherMeasurement(city_id=city.id, temperature=temperature, wind_speed=wind_speed, precipitation=precipitation, created_at=ts))
    db.add(AirQualityMeasurement(city_id=city.id, pm10=pm10, pm25=pm25, created_at=ts))
    db.add(CityScore(city_id=city.id, score=score, created_at=ts))
    db.flush()
