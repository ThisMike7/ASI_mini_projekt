from datetime import datetime, timedelta

from app.services.history_service import get_city_history
from tests.conftest import add_measurements, make_city


def test_history_returns_none_for_unknown_city(db):
    result = get_city_history(db, city_id=9999)
    assert result is None


def test_history_returns_city_metadata(db):
    city = make_city(db, name="Warsaw", country="Poland", continent="Europe", lat=52.2, lon=21.0)
    add_measurements(db, city)
    result = get_city_history(db, city.id)
    assert result["city"] == "Warsaw"
    assert result["country"] == "Poland"
    assert result["continent"] == "Europe"
    assert result["latitude"] == 52.2
    assert result["longitude"] == 21.0


def test_history_empty_when_no_measurements(db):
    city = make_city(db)
    result = get_city_history(db, city.id)
    assert result is not None
    assert result["history"] == []


def test_history_entries_have_required_fields(db):
    city = make_city(db)
    add_measurements(db, city)
    entry = get_city_history(db, city.id)["history"][0]
    for field in ("score", "category", "temperature", "wind_speed", "precipitation", "pm10", "pm25", "measured_at"):
        assert field in entry


def test_history_respects_limit(db):
    city = make_city(db)
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(10):
        add_measurements(db, city, score=float(50 + i), at=base + timedelta(hours=i))
    result = get_city_history(db, city.id, limit=5)
    assert len(result["history"]) == 5


def test_history_ordered_most_recent_first(db):
    city = make_city(db)
    base = datetime(2024, 1, 1, 12, 0, 0)
    add_measurements(db, city, score=60.0, at=base)
    add_measurements(db, city, score=80.0, at=base + timedelta(hours=1))
    history = get_city_history(db, city.id)["history"]
    assert history[0]["score"] == 80.0
    assert history[1]["score"] == 60.0


def test_history_category_matches_score(db):
    city = make_city(db)
    add_measurements(db, city, score=95.0)
    entry = get_city_history(db, city.id)["history"][0]
    assert entry["category"] == "Excellent"


def test_history_correct_values(db):
    city = make_city(db)
    add_measurements(db, city, temperature=18.5, wind_speed=7.0, precipitation=2.0, pm10=20.0, pm25=10.0, score=72.0)
    entry = get_city_history(db, city.id)["history"][0]
    assert entry["temperature"] == 18.5
    assert entry["wind_speed"] == 7.0
    assert entry["precipitation"] == 2.0
    assert entry["pm10"] == 20.0
    assert entry["pm25"] == 10.0
    assert entry["score"] == 72.0
