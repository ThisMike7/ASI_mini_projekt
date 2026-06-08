import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import Base, SessionLocal, engine
from app.models import database_models
from app.services.seed_service import seed_cities

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
logger.info("Database tables ensured.")

db = SessionLocal()
try:
    seed_cities(db)
    logger.info("City seed completed.")
finally:
    db.close()

app = FastAPI(
    title="City Quality Ranking API",
    description="API for ranking cities based on weather and air quality data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "City Quality Ranking API",
        "docs": "/docs",
    }
