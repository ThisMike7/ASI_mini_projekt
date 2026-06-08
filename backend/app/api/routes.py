import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import City
from app.services.history_service import get_city_history
from app.services.ingestion_service import refresh_city_data
from app.services.ranking_service import get_latest_city_ranking

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "city-quality-ranking-api",
    }


@router.get("/cities")
def get_cities(
    continent: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(City)

    if continent and continent != "All":
        query = query.filter(City.continent == continent)

    cities = query.order_by(City.name).all()

    return [
        {
            "id": city.id,
            "name": city.name,
            "country": city.country,
            "continent": city.continent,
            "latitude": city.latitude,
            "longitude": city.longitude,
        }
        for city in cities
    ]


@router.post("/refresh")
def refresh_data(
    continent: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    logger.info("Manual refresh requested for continent: %s", continent or "All")
    result = refresh_city_data(db=db, continent=continent)
    logger.info("Refresh result: %s cities refreshed, %s failed", result["refreshed_cities"], len(result["failed_cities"]))
    return result


@router.get("/ranking")
def get_ranking(
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    limit: Optional[int] = Query(default=None, ge=1, le=300),
    continent: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_latest_city_ranking(
        db=db,
        min_score=min_score,
        limit=limit,
        continent=continent,
    )


@router.get("/cities/{city_id}/history")
def get_history(
    city_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = get_city_history(db=db, city_id=city_id, limit=limit)

    if result is None:
        logger.warning("History requested for unknown city_id: %s", city_id)
        raise HTTPException(status_code=404, detail="City not found")

    return result
