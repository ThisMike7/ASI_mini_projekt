from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    continent = Column(String, nullable=False, default="Europe")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    weather_measurements = relationship("WeatherMeasurement", back_populates="city")
    air_quality_measurements = relationship("AirQualityMeasurement", back_populates="city")
    scores = relationship("CityScore", back_populates="city")


class WeatherMeasurement(Base):
    __tablename__ = "weather_measurements"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    temperature = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City", back_populates="weather_measurements")


class AirQualityMeasurement(Base):
    __tablename__ = "air_quality_measurements"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    pm10 = Column(Float, nullable=True)
    pm25 = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City", back_populates="air_quality_measurements")


class CityScore(Base):
    __tablename__ = "city_scores"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City", back_populates="scores")
