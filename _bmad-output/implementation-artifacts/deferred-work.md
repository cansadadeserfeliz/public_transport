# Deferred Work

## Deferred from: code review of story-1-1-foundation-django-5-2-postgresql-postgis-upgrade (2026-08-19)

- No automatic `migrate` step before `runserver` in `docker-compose.yml`'s `app` command — matches what Story 1.1's Task 1.2 explicitly specified (`runserver`-only for hot reload); worth revisiting once Story 1.8 writes the setup docs.
- ~~No non-root `USER` directive in the Dockerfile~~ — **resolved 2026-08-19**, see story 1.1's Review Findings for detail.
- No `HEALTHCHECK` on the `app` compose service (the `db` service has one) — same reasoning as above; revisit alongside a future deploy/production-hardening story.
- Gunicorn's `CMD` has no explicit `--timeout` — the 30s default is reasonable for current scope; revisit if real workloads surface timeout issues.

## Deferred from: code review of 6-1-dependency-modernization-and-ruff-migration (2026-08-19)

- No dev/prod split for `requirements.txt` — `ruff`, `pytest`, `pytest-cov`, `pytest-sugar`, `factory-boy` all live in the same flat file as `gunicorn`/`requests`/`Django`. Pre-existing pattern, not introduced by this story; worth a `requirements-dev.txt` split if the dependency list keeps growing.
- No lockfile or hash-pinning (`pip-compile`/`requirements.lock`) — the project has always used loose `==` pins with no transitive-dependency locking. Legitimate future supply-chain hardening, out of scope for a dependency-version-bump story.

## Deferred from: code review of story-1-2-gtfs-ready-data-model (2026-08-23)

- `Corridor.color` has a hex-format `CheckConstraint` (`corridor_color_valid_hex`); the pre-existing `Route.color` field (same shape, same `#95B734`-style help text, carried over unchanged from the old model) does not. Not introduced by this story — `Route.color` predates the amendment. Retrofitting the same constraint needs a decision first: `Route.color` defaults to `''` (empty string), which the strict `^#[0-9A-Fa-f]{6}$` regex would reject outright, so tightening it would need either a looser pattern (allow empty) or a data audit of existing `''`-valued rows before enforcing. Worth revisiting once real GTFS data is loaded (Story 1.3) and it's clear whether every active route actually gets a color.
