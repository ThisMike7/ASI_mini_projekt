import pytest

from app.services.ranking_service import (
    calculate_score,
    clamp,
    get_latest_city_ranking,
    get_score_category,
)
from tests.conftest import add_measurements, make_city


# ---------------------------------------------------------------------------
# clamp
# ---------------------------------------------------------------------------

def test_clamp_within_range():
    assert clamp(50.0) == 50.0


def test_clamp_below_min():
    assert clamp(-10.0) == 0.0


def test_clamp_above_max():
    assert clamp(150.0) == 100.0


def test_clamp_at_boundaries():
    assert clamp(0.0) == 0.0
    assert clamp(100.0) == 100.0


def test_clamp_custom_range():
    assert clamp(5.0, min_value=10.0, max_value=20.0) == 10.0
    assert clamp(25.0, min_value=10.0, max_value=20.0) == 20.0
    assert clamp(15.0, min_value=10.0, max_value=20.0) == 15.0


# ---------------------------------------------------------------------------
# calculate_score
# ---------------------------------------------------------------------------

def test_calculate_score_perfect_conditions():
    score = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    assert score == 100.0


def test_calculate_score_returns_float():
    score = calculate_score(temperature=20.0, wind_speed=10.0, precipitation=5.0, pm10=25.0, pm25=12.0)
    assert isinstance(score, float)


def test_calculate_score_always_in_range():
    score = calculate_score(temperature=-30.0, wind_speed=200.0, precipitation=100.0, pm10=1000.0, pm25=1000.0)
    assert 0.0 <= score <= 100.0


def test_calculate_score_high_pollution_gives_low_score():
    score_clean = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    score_polluted = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=500.0, pm25=500.0)
    assert score_polluted < score_clean
    assert score_polluted < 75.0


def test_calculate_score_optimal_temperature_beats_cold():
    score_optimal = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    score_cold = calculate_score(temperature=0.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    assert score_optimal > score_cold


def test_calculate_score_high_wind_lowers_score():
    score_calm = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    score_windy = calculate_score(temperature=22.0, wind_speed=80.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    assert score_calm > score_windy


def test_calculate_score_precipitation_lowers_score():
    score_dry = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=0.0, pm10=0.0, pm25=0.0)
    score_rainy = calculate_score(temperature=22.0, wind_speed=0.0, precipitation=20.0, pm10=0.0, pm25=0.0)
    assert score_dry > score_rainy


def test_calculate_score_is_rounded_to_two_decimals():
    score = calculate_score(temperature=15.0, wind_speed=7.5, precipitation=3.0, pm10=20.0, pm25=10.0)
    assert score == round(score, 2)


# ---------------------------------------------------------------------------
# get_score_category
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (100.0, "Excellent"),
    (90.0,  "Excellent"),
    (89.9,  "Good"),
    (75.0,  "Good"),
    (74.9,  "Moderate"),
    (60.0,  "Moderate"),
    (59.9,  "Poor"),
    (40.0,  "Poor"),
    (39.9,  "Very poor"),
    (0.0,   "Very poor"),
])
def test_get_score_category(score, expected):
    assert get_score_category(score) == expected


# ---------------------------------------------------------------------------
# get_latest_city_ranking (in-memory SQLite)
# ---------------------------------------------------------------------------

def test_ranking_returns_city_with_data(db):
    city = make_city(db)
    add_measurements(db, city)
    ranking = get_latest_city_ranking(db)
    assert len(ranking) == 1
    assert ranking[0]["city"] == "Warsaw"


def test_ranking_excludes_city_without_data(db):
    make_city(db)
    ranking = get_latest_city_ranking(db)
    assert len(ranking) == 0


def test_ranking_sorted_by_score_descending(db):
    city1 = make_city(db, name="Warsaw")
    city2 = make_city(db, name="Berlin", country="Germany")
    add_measurements(db, city1, score=70.0)
    add_measurements(db, city2, score=90.0)
    ranking = get_latest_city_ranking(db)
    assert ranking[0]["city"] == "Berlin"
    assert ranking[1]["city"] == "Warsaw"


def test_ranking_filters_by_continent(db):
    city_eu = make_city(db, name="Warsaw", continent="Europe")
    city_as = make_city(db, name="Tokyo", country="Japan", continent="Asia")
    add_measurements(db, city_eu, score=80.0)
    add_measurements(db, city_as, score=85.0)
    ranking = get_latest_city_ranking(db, continent="Europe")
    assert len(ranking) == 1
    assert ranking[0]["city"] == "Warsaw"


def test_ranking_all_continent_returns_all(db):
    city_eu = make_city(db, name="Warsaw", continent="Europe")
    city_as = make_city(db, name="Tokyo", country="Japan", continent="Asia")
    add_measurements(db, city_eu, score=80.0)
    add_measurements(db, city_as, score=85.0)
    ranking = get_latest_city_ranking(db, continent="All")
    assert len(ranking) == 2


def test_ranking_filters_by_min_score(db):
    city = make_city(db)
    add_measurements(db, city, score=50.0)
    assert len(get_latest_city_ranking(db, min_score=60.0)) == 0
    assert len(get_latest_city_ranking(db, min_score=50.0)) == 1


def test_ranking_limit(db):
    for i in range(5):
        city = make_city(db, name=f"City{i}", country=f"Country{i}")
        add_measurements(db, city, score=float(i * 10 + 10))
    ranking = get_latest_city_ranking(db, limit=3)
    assert len(ranking) == 3


def test_ranking_entry_has_required_fields(db):
    city = make_city(db)
    add_measurements(db, city, temperature=18.0, wind_speed=3.0, precipitation=1.0, pm10=15.0, pm25=8.0, score=78.0)
    entry = get_latest_city_ranking(db)[0]
    for field in ("city", "country", "continent", "latitude", "longitude", "temperature", "wind_speed", "precipitation", "pm10", "pm25", "score", "category", "measured_at"):
        assert field in entry
