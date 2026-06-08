import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.database_models import City


CAPITALS_FILE = Path(__file__).resolve().parent.parent / "data" / "capitals.json"


def load_capitals() -> list[dict]:
    with open(CAPITALS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def seed_cities(db: Session):
    capitals = load_capitals()

    for capital_data in capitals:
        existing_city = (
            db.query(City)
            .filter(
                City.name == capital_data["name"],
                City.country == capital_data["country"],
            )
            .first()
        )

        if existing_city is None:
            city = City(
                name=capital_data["name"],
                country=capital_data["country"],
                continent=capital_data["continent"],
                latitude=capital_data["latitude"],
                longitude=capital_data["longitude"],
            )
            db.add(city)
        else:
            existing_city.continent = capital_data["continent"]
            existing_city.latitude = capital_data["latitude"]
            existing_city.longitude = capital_data["longitude"]

    db.commit()
