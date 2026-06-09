# Capital Quality Monitoring System

System monitoruje jakość życia w stolicach świata na podstawie danych pogodowych i jakości powietrza pobieranych na bieżąco z zewnętrznych API. Dane są zapisywane w bazie, przetwarzane do postaci rankingu i prezentowane na stronie WWW z mapą.

## Źródła danych

Projekt korzysta z dwóch niezależnych źródeł:

1. **Open-Meteo Weather API** — temperatura, prędkość wiatru, opady (REST, bez klucza API)
2. **Open-Meteo Air Quality API** — stężenie PM10 i PM2.5 (REST, bez klucza API)

Oba źródła są odpytywane osobno dla każdego miasta i zapisywane jako oddzielne rekordy w bazie.

## Architektura systemu

Diagramy C4 (Context, Container, Component) znajdują się w [`docs/architecture.md`](docs/architecture.md).


System jest zbudowany warstwowo:

```
[Open-Meteo Weather API]  [Open-Meteo Air Quality API]
            |                          |
            └──────────┬───────────────┘
                       ↓
            [Data Ingestion Service]
            pobiera dane dla każdego miasta
                       ↓
            [Processing / Ranking Service]
            oblicza score 0-100 na podstawie
            temperatury, wiatru, opadów, PM10, PM2.5
                       ↓
             [PostgreSQL Database]
             cities, weather_measurements,
             air_quality_measurements, city_scores
                       ↓
              [FastAPI Backend / REST API]
              endpointy: /ranking, /cities,
              /refresh, /cities/{id}/history
                       ↓
              [Frontend - strona WWW]
              mapa Leaflet + tabela rankingu
```

Worker odpytuje oba API co godzinę dla wszystkich stolic i zapisuje wyniki. Użytkownik może też ręcznie wyzwolić odświeżenie przez przycisk na stronie.

## Uruchamianie

Projekt ma trzy środowiska Docker.

**Development** (hot reload, baza dostępna lokalnie):
```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Testy jednostkowe** (izolowane, bez PostgreSQL):
```bash
docker-compose -f docker-compose.test.yml run --rm test
```

**Production** (restart automatyczny, baza niedostępna z zewnątrz):
```bash
docker-compose -f docker-compose.prod.yml up --build
```

Po uruchomieniu dev:
- Frontend: http://localhost:8080
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Technologie i uzasadnienie wyboru

| Technologia | Rola | 
|---|---|
| **FastAPI** | Backend / REST API |
| **PostgreSQL** | Baza danych |
| **SQLAlchemy** | ORM |
| **Docker / Compose** |
| **Leaflet.js** | Mapa na froncie | 
| **Chart.js** | Wykresy historii |
| **Locust** | Testy wydajnościowe | 
| **pytest** | Testy jednostkowe | 
| **Vanilla JS** | Frontend |

## Struktura projektu

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # endpointy REST
│   │   ├── models/                # modele SQLAlchemy
│   │   ├── services/
│   │   │   ├── ingestion_service.py   # pobieranie danych z API
│   │   │   ├── ranking_service.py     # obliczanie score
│   │   │   ├── history_service.py     # historia pomiarów
│   │   │   └── seed_service.py        # inicjalizacja miast
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/                     # testy jednostkowe (pytest)
│   ├── worker.py                  # cykliczne pobieranie danych co godzinę
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── performance-tests/
│   └── locustfile.py
├── docker-compose.dev.yml
├── docker-compose.test.yml
└── docker-compose.prod.yml
```

## API

Dokumentacja interaktywna dostępna pod `/docs` (Swagger UI).

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/ranking` | Ranking miast (opcjonalnie: `continent`, `min_score`, `limit`) |
| GET | `/cities` | Lista wszystkich miast |
| GET | `/cities/{id}/history` | Historia pomiarów dla danego miasta |
| POST | `/refresh` | Ręczne odświeżenie danych z API |
| GET | `/health` | Status serwisu |

## Testy

Testy jednostkowe pokrywają trzy moduły serwisowe:

- `test_ranking_service.py` — logika scoringu (`clamp`, `calculate_score`, `get_score_category`, ranking z DB)
- `test_history_service.py` — pobieranie historii pomiarów
- `test_ingestion_service.py` — pobieranie danych z API (mockowane) i zapis do DB

```bash
# uruchomienie przez Docker
docker-compose -f docker-compose.test.yml run --rm test

# lub bezpośrednio w kontenerze
docker exec city-quality-backend python -m pytest tests/ -v
```

Testy wydajnościowe (Locust) znajdują się w `performance-tests/locustfile.py`.
