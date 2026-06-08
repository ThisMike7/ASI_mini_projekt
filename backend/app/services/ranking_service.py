from sqlalchemy.orm import Session

from app.models.database_models import (
    AirQualityMeasurement,
    City,
    CityScore,
    WeatherMeasurement,
)


def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))


def calculate_score(
    temperature: float,
    wind_speed: float,
    precipitation: float,
    pm10: float,
    pm25: float,
) -> float:
    """
    Calculates a city quality score in the range 0-100.

    The final score consists of:
    - 60% air quality score
    - 40% weather comfort score

    Higher score means better current conditions.
    """

    # --- Air quality component ---
    # PM10 reference threshold: 50 µg/m³
    # PM2.5 reference threshold: 25 µg/m³
    pm10_penalty = clamp((pm10 / 50.0) * 50.0, 0.0, 50.0)
    pm25_penalty = clamp((pm25 / 25.0) * 50.0, 0.0, 50.0)

    air_quality_score = 100.0 - (0.45 * pm10_penalty + 0.55 * pm25_penalty)
    air_quality_score = clamp(air_quality_score)

    # --- Weather comfort component ---
    # Best comfort temperature range: 20-24°C
    if temperature < 20.0:
        temperature_penalty = min((20.0 - temperature) * 3.0, 35.0)
    elif temperature > 24.0:
        temperature_penalty = min((temperature - 24.0) * 3.0, 35.0)
    else:
        temperature_penalty = 0.0

    wind_penalty = clamp((wind_speed / 40.0) * 30.0, 0.0, 30.0)
    precipitation_penalty = clamp((precipitation / 10.0) * 40.0, 0.0, 40.0)

    weather_score = 100.0 - temperature_penalty - wind_penalty - precipitation_penalty
    weather_score = clamp(weather_score)

    # --- Final weighted score ---
    final_score = 0.6 * air_quality_score + 0.4 * weather_score

    return round(clamp(final_score), 2)

def get_score_category(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Moderate"
    if score >= 40:
        return "Poor"
    return "Very poor"

def get_latest_city_ranking(
    db: Session,
    min_score: float | None = None,
    limit: int | None = None,
    continent: str | None = None,
):
    query = db.query(City)

    if continent and continent != "All":
        query = query.filter(City.continent == continent)

    cities = query.order_by(City.name).all()

    ranking = []

    for city in cities:
        latest_score = (
            db.query(CityScore)
            .filter(CityScore.city_id == city.id)
            .order_by(CityScore.created_at.desc())
            .first()
        )

        latest_weather = (
            db.query(WeatherMeasurement)
            .filter(WeatherMeasurement.city_id == city.id)
            .order_by(WeatherMeasurement.created_at.desc())
            .first()
        )

        latest_air_quality = (
            db.query(AirQualityMeasurement)
            .filter(AirQualityMeasurement.city_id == city.id)
            .order_by(AirQualityMeasurement.created_at.desc())
            .first()
        )

        if latest_score is None or latest_weather is None or latest_air_quality is None:
            continue

        if min_score is not None and latest_score.score < min_score:
            continue

        ranking.append(
            {
                "city_id": city.id,
                "city": city.name,
                "country": city.country,
                "continent": city.continent,
                "latitude": city.latitude,
                "longitude": city.longitude,
                "temperature": latest_weather.temperature,
                "wind_speed": latest_weather.wind_speed,
                "precipitation": latest_weather.precipitation,
                "pm10": latest_air_quality.pm10,
                "pm25": latest_air_quality.pm25,
                "score": latest_score.score,
                "category": get_score_category(latest_score.score),
                "measured_at": latest_score.created_at,
            }
        )

    ranking.sort(key=lambda item: item["score"], reverse=True)

    if limit is not None:
        ranking = ranking[:limit]

    return ranking
