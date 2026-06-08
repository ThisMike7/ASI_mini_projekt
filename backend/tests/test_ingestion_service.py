from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models.database_models import AirQualityMeasurement, CityScore, WeatherMeasurement
from app.services.ingestion_service import fetch_air_quality, fetch_weather, refresh_city_data
from tests.conftest import make_city


# ---------------------------------------------------------------------------
# fetch_weather
# ---------------------------------------------------------------------------

def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    else:
        mock.raise_for_status.return_value = None
    return mock


def test_fetch_weather_returns_current_block(mocker):
    payload = {"current": {"temperature_2m": 18.5, "wind_speed_10m": 5.0, "precipitation": 0.0}}
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response(payload))
    city = MagicMock(latitude=52.2, longitude=21.0)
    result = fetch_weather(city)
    assert result["temperature_2m"] == 18.5
    assert result["wind_speed_10m"] == 5.0
    assert result["precipitation"] == 0.0


def test_fetch_weather_raises_on_http_error(mocker):
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response({}, status_code=500))
    city = MagicMock(latitude=52.2, longitude=21.0)
    with pytest.raises(requests.HTTPError):
        fetch_weather(city)


def test_fetch_weather_returns_empty_dict_when_no_current_key(mocker):
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response({}))
    city = MagicMock(latitude=52.2, longitude=21.0)
    result = fetch_weather(city)
    assert result == {}


# ---------------------------------------------------------------------------
# fetch_air_quality
# ---------------------------------------------------------------------------

def test_fetch_air_quality_returns_current_block(mocker):
    payload = {"current": {"pm10": 20.0, "pm2_5": 10.0}}
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response(payload))
    city = MagicMock(latitude=52.2, longitude=21.0)
    result = fetch_air_quality(city)
    assert result["pm10"] == 20.0
    assert result["pm2_5"] == 10.0


def test_fetch_air_quality_raises_on_http_error(mocker):
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response({}, status_code=503))
    city = MagicMock(latitude=52.2, longitude=21.0)
    with pytest.raises(requests.HTTPError):
        fetch_air_quality(city)


def test_fetch_air_quality_returns_empty_dict_when_no_current_key(mocker):
    mocker.patch("app.services.ingestion_service.requests.get", return_value=_mock_response({}))
    city = MagicMock(latitude=52.2, longitude=21.0)
    result = fetch_air_quality(city)
    assert result == {}


# ---------------------------------------------------------------------------
# refresh_city_data
# ---------------------------------------------------------------------------

WEATHER_DATA = {"temperature_2m": 20.0, "wind_speed_10m": 5.0, "precipitation": 0.0}
AIR_DATA = {"pm10": 15.0, "pm2_5": 7.0}


def test_refresh_stores_measurements_in_db(db, mocker):
    city = make_city(db)
    mocker.patch("app.services.ingestion_service.fetch_weather", return_value=WEATHER_DATA)
    mocker.patch("app.services.ingestion_service.fetch_air_quality", return_value=AIR_DATA)
    refresh_city_data(db)
    assert db.query(WeatherMeasurement).count() == 1
    assert db.query(AirQualityMeasurement).count() == 1
    assert db.query(CityScore).count() == 1


def test_refresh_returns_ok_status(db, mocker):
    make_city(db)
    mocker.patch("app.services.ingestion_service.fetch_weather", return_value=WEATHER_DATA)
    mocker.patch("app.services.ingestion_service.fetch_air_quality", return_value=AIR_DATA)
    result = refresh_city_data(db)
    assert result["status"] == "ok"
    assert result["refreshed_cities"] == 1
    assert result["failed_cities"] == []


def test_refresh_filters_by_continent(db, mocker):
    make_city(db, name="Warsaw", continent="Europe")
    make_city(db, name="Tokyo", country="Japan", continent="Asia")
    mocker.patch("app.services.ingestion_service.fetch_weather", return_value=WEATHER_DATA)
    mocker.patch("app.services.ingestion_service.fetch_air_quality", return_value=AIR_DATA)
    result = refresh_city_data(db, continent="Europe")
    assert result["refreshed_cities"] == 1
    assert result["requested_cities"] == 1


def test_refresh_partial_success_on_fetch_error(db, mocker):
    make_city(db, name="Warsaw")
    make_city(db, name="Tokyo", country="Japan", continent="Asia")
    mocker.patch("app.services.ingestion_service.fetch_weather", side_effect=Exception("timeout"))
    mocker.patch("app.services.ingestion_service.fetch_air_quality", return_value=AIR_DATA)
    result = refresh_city_data(db)
    assert result["status"] == "partial_success"
    assert result["refreshed_cities"] == 0
    assert len(result["failed_cities"]) == 2


def test_refresh_no_cities_returns_ok(db, mocker):
    result = refresh_city_data(db)
    assert result["status"] == "ok"
    assert result["refreshed_cities"] == 0
