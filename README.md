# :oncoming_bus: Public transport

## :busstop: Requirements

- Docker + Docker Compose

## :gear: Setup

1. Create a `.env` file in the project root with at least:

       DJANGO_SECRET_KEY=<pick-a-random-secret>
       POSTGRES_DB=public_transport
       POSTGRES_USER=public_transport
       POSTGRES_PASSWORD=<pick-a-local-password>
       POSTGRES_HOST=db
       POSTGRES_PORT=5432

2. Build and start the stack:

       docker compose up

3. Apply migrations (run once, and again after pulling changes that add new ones):

       docker compose run --rm app python manage.py migrate

The app is now running at http://localhost:8000, with a PostGIS-backed Postgres database (`postgis/postgis:17-3.5`) running alongside it.

**Current state:** the `routes` app has no migrations yet — its data model is being reworked (`BusStop`, `Route`, `Corridor`, etc.) and a fresh initial migration lands with that change. Until then, pages that query route/stop data (including the homepage) will 500 with `relation "routes_route" does not exist` — that's expected, not a setup mistake. Django's own admin, auth, and session tables are fully migrated and usable.

## :white_check_mark: Running tests

    docker compose run --rm app python -m pytest

## :art: Linting / formatting

Lint and format are both handled by `ruff` (configured in `pyproject.toml`). There's no pre-commit hook or CI step running these automatically — run them yourself before pushing:

    docker compose run --rm app ruff check .          # lint
    docker compose run --rm app ruff check --fix .     # lint, auto-fixing what it can
    docker compose run --rm app ruff format .          # format
    docker compose run --rm app ruff format --check .  # format, check only (no changes written)

## :warning: Legacy data pipeline

The old Scrapy-based crawler (`scrapy crawl sitp`, `python manage.py load_bus_stations`) predates the move to PostgreSQL/PostGIS and hasn't been re-verified against the new database. It's still in the repo but scheduled for retirement once the GTFS-based refresh pipeline lands in a future story — don't rely on it for now.

## Data

* Estaciones Troncales de TRANSMILENIO: https://datosabiertos.bogota.gov.co/en/dataset/estaciones-troncales-de-transmilenio1
* Trazados Troncales de TRANSMILENIO: https://datosabiertos.bogota.gov.co/en/dataset/trazados-troncales-de-transmilenio
* Rutas Zonales del SITP: https://datosabiertos.bogota.gov.co/en/dataset/ru
  * https://datosabiertos.bogota.gov.co/dataset/servicios-rutas-troncales-y-zonales
* Paraderos Zonales del SITP:
  * https://datosabiertos-transmilenio.hub.arcgis.com/search?groupIds=69785fbaa2524cd88a47fe75c58ef48c
  * https://datosabiertos.bogota.gov.co/dataset/paraderos-zonales-del-sitp (outdated)
* Trazados cable: https://datosabiertos.bogota.gov.co/en/dataset/trazados-cable
