from sqlalchemy.orm import Session

from app.models.database_models import (
    AirQualityMeasurement,
    City,
    CityScore,
    WeatherMeasurement,
)
from app.services.ranking_service import get_score_category


def get_city_history(db: Session, city_id: int, limit: int = 10):
    city = db.query(City).filter(City.id == city_id).first()

    if city is None:
        return None

    scores = (
        db.query(CityScore)
        .filter(CityScore.city_id == city_id)
        .order_by(CityScore.created_at.desc())
        .limit(limit)
        .all()
    )

    history = []

    for score in scores:
        weather = (
            db.query(WeatherMeasurement)
            .filter(
                WeatherMeasurement.city_id == city_id,
                WeatherMeasurement.created_at <= score.created_at,
            )
            .order_by(WeatherMeasurement.created_at.desc())
            .first()
        )

        air_quality = (
            db.query(AirQualityMeasurement)
            .filter(
                AirQualityMeasurement.city_id == city_id,
                AirQualityMeasurement.created_at <= score.created_at,
            )
            .order_by(AirQualityMeasurement.created_at.desc())
            .first()
        )

        if weather is None or air_quality is None:
            continue

        history.append(
            {
                "score": score.score,
                "category": get_score_category(score.score),
                "temperature": weather.temperature,
                "wind_speed": weather.wind_speed,
                "precipitation": weather.precipitation,
                "pm10": air_quality.pm10,
                "pm25": air_quality.pm25,
                "measured_at": score.created_at,
            }
        )

    return {
        "city_id": city.id,
        "city": city.name,
        "country": city.country,
        "continent": city.continent,
        "latitude": city.latitude,
        "longitude": city.longitude,
        "history": history,
    }
