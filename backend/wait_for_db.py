import os
import time

import psycopg2


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://city_user:city_password@db:5432/city_quality",
)

max_attempts = 30

for attempt in range(1, max_attempts + 1):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        print("Database is ready.")
        break
    except Exception as error:
        print(f"Waiting for database... attempt {attempt}/{max_attempts}")
        print(error)
        time.sleep(2)
else:
    raise RuntimeError("Database is not available after waiting.")
