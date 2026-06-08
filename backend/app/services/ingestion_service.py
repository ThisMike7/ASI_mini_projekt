import logging

import requests
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.database_models import (
    AirQualityMeasurement,
    City,
    CityScore,
    WeatherMeasurement,
)
from app.services.ranking_service import calculate_score


WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_weather(city: City) -> dict:
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": "temperature_2m,wind_speed_10m,precipitation",
    }

    response = requests.get(WEATHER_API_URL, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    return data.get("current", {})


def fetch_air_quality(city: City) -> dict:
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": "pm10,pm2_5",
    }

    response = requests.get(AIR_QUALITY_API_URL, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    return data.get("current", {})


def refresh_city_data(db: Session, continent: str | None = None) -> dict:
    query = db.query(City)

    if continent and continent != "All":
        query = query.filter(City.continent == continent)

    cities = query.order_by(City.name).all()

    refreshed = 0
    failed = []

    for city in cities:
        try:
            weather = fetch_weather(city)
            air_quality = fetch_air_quality(city)

            temperature = weather.get("temperature_2m")
            wind_speed = weather.get("wind_speed_10m")
            precipitation = weather.get("precipitation")
            pm10 = air_quality.get("pm10")
            pm25 = air_quality.get("pm2_5")

            weather_measurement = WeatherMeasurement(
                city_id=city.id,
                temperature=temperature,
                wind_speed=wind_speed,
                precipitation=precipitation,
            )

            air_quality_measurement = AirQualityMeasurement(
                city_id=city.id,
                pm10=pm10,
                pm25=pm25,
            )

            score = calculate_score(
                temperature=temperature or 0,
                wind_speed=wind_speed or 0,
                precipitation=precipitation or 0,
                pm10=pm10 or 0,
                pm25=pm25 or 0,
            )

            city_score = CityScore(
                city_id=city.id,
                score=score,
            )

            db.add(weather_measurement)
            db.add(air_quality_measurement)
            db.add(city_score)

            refreshed += 1

        except Exception as error:
            logger.error("Failed to refresh %s (%s): %s", city.name, city.country, error)
            failed.append(
                {
                    "city": city.name,
                    "country": city.country,
                    "continent": city.continent,
                    "error": str(error),
                }
            )

    db.commit()
    logger.info("Refresh complete: %d/%d cities updated, %d failed", refreshed, len(cities), len(failed))

    return {
        "status": "ok" if not failed else "partial_success",
        "continent": continent or "All",
        "requested_cities": len(cities),
        "refreshed_cities": refreshed,
        "failed_cities": failed,
    }
