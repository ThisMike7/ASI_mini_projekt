import datetime
import logging
import os
import time

from app.database import SessionLocal
from app.services.ingestion_service import refresh_city_data


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("worker")

RUN_ON_STARTUP = os.getenv("RUN_ON_STARTUP", "false").lower() == "true"
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))


def get_next_full_hour() -> datetime.datetime:
    now = datetime.datetime.now(datetime.timezone.utc)

    return (now + datetime.timedelta(hours=1)).replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def refresh_all_capitals():
    db = SessionLocal()

    try:
        started_at = datetime.datetime.now(datetime.timezone.utc)
        logger.info("Starting full refresh at %s", started_at.isoformat())

        result = refresh_city_data(db=db, continent=None)

        finished_at = datetime.datetime.now(datetime.timezone.utc)
        logger.info("Finished full refresh at %s", finished_at.isoformat())
        logger.info("Result: %s", result)

    except Exception:
        logger.exception("Error during full refresh")

    finally:
        db.close()


def run_worker():
    logger.info("City quality hourly worker started.")
    logger.info("Mode: full refresh for all capitals at every full UTC hour.")

    if RUN_ON_STARTUP:
        logger.info("RUN_ON_STARTUP=true, running initial refresh now.")
        refresh_all_capitals()

    next_run_at = get_next_full_hour()
    logger.info("Next scheduled run at %s", next_run_at.isoformat())

    while True:
        now = datetime.datetime.now(datetime.timezone.utc)

        if now >= next_run_at:
            logger.info("Scheduled time reached: %s", now.isoformat())
            refresh_all_capitals()

            next_run_at = get_next_full_hour()
            logger.info("Next scheduled run at %s", next_run_at.isoformat())

        seconds_left = max(0, int((next_run_at - now).total_seconds()))
        sleep_seconds = min(CHECK_INTERVAL_SECONDS, seconds_left if seconds_left > 0 else CHECK_INTERVAL_SECONDS)

        logger.info(
            "Worker alive. Current UTC time: %s. Next run: %s. Sleeping %s seconds.",
            now.isoformat(),
            next_run_at.isoformat(),
            sleep_seconds,
        )

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    run_worker()
