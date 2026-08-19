# Story 1.1: Foundation — Django 5.2 + PostgreSQL/PostGIS Upgrade

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want the app running on Django 5.2 LTS against a PostgreSQL+PostGIS database instead of Django 4.2.4/SQLite,
so that the rest of the product can be built on a modern, spatially-capable foundation instead of fighting an obsolete stack.

## Acceptance Criteria

1. **Given** the existing Django 4.2.4/SQLite codebase, **when** the upgrade is applied, **then** the app runs on Django 5.2 LTS with a `postgis/postgis:17-3.5` PostgreSQL+PostGIS database via GeoDjango, started locally through Docker Compose.
2. **And** the new `Dockerfile` pins **Python 3.11** as its base image (not bumped — matches the architecture's "already fixed, not re-decided" call), with GDAL/GEOS system packages installed for GeoDjango.
3. **And** WhiteNoise middleware is configured for static asset compression and cache headers (NFR1 mechanism).
4. **And** the legacy `db.sqlite3` is archived, not upgraded in place — the new database starts empty.
5. **And** Gunicorn is configured to run with exactly **1 worker process** (`gunicorn --workers 1`, not Gunicorn's multi-core-scaling default) — required for Django's local-memory cache to behave as a single shared cache rather than one independent copy per worker, which would otherwise multiply calls to the fragile transmiapp API beyond the "one call per TTL window" bound Story 3.1 depends on.
6. **Given** the old migration history (`routes/migrations/0001`–`0007`), **when** the foundation lands, **then** those migrations are deleted in preparation for a single fresh `0001_initial` to be generated once the amended models exist (Story 1.2) — this story does **not** generate a new initial migration.
7. **And** a base stylesheet defines the design token foundation as CSS custom properties — color palette, the 8-scale spacing system, the soft-curves border-radius scale, and the type scale — loaded through Django's static files app with no build step, so every component built in later stories pulls from tokens rather than hardcoded values (UX-DR1).

## Tasks / Subtasks

- [x] Task 1: Add PostgreSQL/PostGIS + app service to Docker Compose (AC: #1)
  *(Tasks 1 and 2 land together — the `app` service's `build: .` context assumes the Task 2 Dockerfile exists. Implement both before running `docker-compose up`; order between them doesn't matter.)*
  - [x] 1.1 Create `docker-compose.yml`: `db` service using `postgis/postgis:17-3.5`, named volume for Postgres data, `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` sourced from `.env`, with a `healthcheck` (`pg_isready -U $POSTGRES_USER`) so dependents wait for real readiness, not just container start
  - [x] 1.2 `app` service builds from the new `Dockerfile`, `depends_on: db: condition: service_healthy` (not a bare `depends_on: db` — avoids a race where Django tries to connect before Postgres finishes initializing on first `up`), port `8000:8000`, bind-mounts the repo for local dev, `command: python manage.py runserver 0.0.0.0:8000` overriding the image's default CMD (hot reload for local dev; the Dockerfile's own CMD stays the production Gunicorn line — see Task 2)
  - [x] 1.3 Add `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` to `.env` (already gitignored). Do **not** write the full `.env.example` yet — that file, and documenting every required var, is Story 1.8's explicit AC; this story only needs enough for `docker-compose up` to work locally.

- [x] Task 2: Build the app `Dockerfile` (AC: #1, #2, #5)
  - [x] 2.1 Base image `python:3.11-slim` (pins Python 3.11 — do not bump to 3.12+, per architecture decision)
  - [x] 2.2 `apt-get install` GDAL/GEOS/PROJ system packages required for GeoDjango: `gdal-bin libgdal-dev libgeos-dev libproj-dev binutils`
  - [x] 2.3 `pip install -r requirements.txt`
  - [x] 2.4 `CMD ["gunicorn", "app.wsgi:application", "--workers", "1", "--bind", "0.0.0.0:8000"]` — exactly 1 worker, never Gunicorn's default multi-core scaling (see Dev Notes: Why 1 Worker)
  - [x] 2.5 Add a `.dockerignore` at the repo root excluding `.env`, `venv/`, `.git`, `db.sqlite3*`, `__pycache__/`, `*.pyc`, `.idea/` — without it, `COPY . .` bakes `.env`'s secrets and the whole `venv/` straight into the image layer

- [x] Task 3: Upgrade Django and switch the DB backend (AC: #1)
  - [x] 3.1 Bump `requirements.txt`: `Django==5.2.16` (current LTS patch as of Jul 2026), add `psycopg[binary]==3.3.4` (Postgres driver — GeoDjango's `postgis` backend needs a DB-API driver; psycopg 3 is the modern, non-deprecated choice over psycopg2), `whitenoise==6.12.0`, `gunicorn==26.0.0`, `pytest-django` (latest stable — required for Task 8; see there for why). Leave Scrapy/`python-telegram-bot`/`python-dotenv`/black/flake8/pre-commit untouched — out of scope for this story.
  - [x] 3.2 Add `'django.contrib.gis'` to `INSTALLED_APPS` in `app/settings.py`
  - [x] 3.3 Point `DATABASES['default']['ENGINE']` to `'django.contrib.gis.db.backends.postgis'`; read `NAME`/`USER`/`PASSWORD`/`HOST`/`PORT` from environment variables (see 3.4)
  - [x] 3.4 Wire `python-dotenv` into `app/settings.py` (`from dotenv import load_dotenv; load_dotenv()` near the top, before reading any `os.environ` value). **This does not exist today** — `python-dotenv` is currently only called from `telegram_bot/services.py`; `app/settings.py` never loads `.env` at all. Without this change, the DB env vars from Task 1.3 won't resolve.

- [x] Task 4: Configure WhiteNoise (AC: #3)
  - [x] 4.1 Insert `'whitenoise.middleware.WhiteNoiseMiddleware'` into `MIDDLEWARE` immediately after `'django.middleware.security.SecurityMiddleware'`
  - [x] 4.2 Set `STORAGES['staticfiles']['BACKEND'] = 'whitenoise.storage.CompressedManifestStaticFilesStorage'` using Django 5.2's `STORAGES` setting (the older `STATICFILES_STORAGE` setting is deprecated — don't use it)
  - [x] 4.3 Do not add a `collectstatic` step to the Docker build or Compose flow in this story — production static serving is wired up as part of the deploy story (`deploy.sh` doesn't exist yet); local dev via `runserver` with `DEBUG=True` doesn't need it

- [x] Task 5: Archive the legacy SQLite database (AC: #4)
  - [x] 5.1 Move `db.sqlite3` out of the active path (e.g. rename to `db.sqlite3.bak`, or relocate under a clearly-labeled archive location) — do not delete outright, and do not attempt to migrate its data into PostGIS; Story 1.2's `refresh_gtfs` populates the new database from scratch, not from this file
  - [x] 5.2 Confirm nothing in `DATABASES` or settings still points at `db.sqlite3`

- [x] Task 6: Delete the obsolete migration history (AC: #6)
  - [x] 6.1 Delete `routes/migrations/0001_initial.py` through `routes/migrations/0007_alter_busstation_transmilenio_id.py`; keep `routes/migrations/__init__.py`
  - [x] 6.2 Do **not** run `makemigrations` or generate a new `0001_initial` in this story. `routes/models.py` still describes the pre-amendment schema (`BusStation`, `route_type`, `DecimalField` lat/lng) — the fresh initial migration is only generated once Story 1.2 lands the amended models. Ending this story with `routes/migrations/` containing only `__init__.py`, and no `routes` tables in the new database, is the correct, expected state — not a gap to fix here.

- [x] Task 7: Land the design token stylesheet (AC: #7)
  - [x] 7.1 Create `static/css/tokens.css` (project-level; register its parent directory in `STATICFILES_DIRS`) defining CSS custom properties: neutrals (`--paper`, `--paper-raised`, `--ink`, `--ink-soft`, `--line`, `--line-strong`, `--muted`) for light and `[data-theme="dark"]`, the app accent (Páramo green: `--accent`, `--accent-soft`, `--accent-ink`), the 8-scale spacing system (`--space-1` … `--space-8`, 4px–48px), the soft-curves border-radius scale (`--radius-sm/md/lg` = 8/14/22px), and the type scale (`--font-ui`, `--font-data`) — see Dev Notes for the exact ratified values
  - [x] 7.2 Treat `docs/visual-foundation-reference.html`'s `:root` block as the single source of truth for values — copy them exactly, don't invent new ones
  - [x] 7.3 Link `tokens.css` in `app/templates/layout/base.html`'s `<head>` so every page inherits it
  - [x] 7.4 Scope check: no corridor color chart, no component styles (route rows, markers, panels) here — this story only lands the token foundation; components are built per-story later against these tokens

- [x] Task 8: Foundation smoke test (Testing Standards)
  - [x] 8.1 Add `DJANGO_SETTINGS_MODULE = app.settings` to `pytest.ini`'s `[pytest]` section, and wire in `pytest-django` (added in Task 3.1). **This is a real prerequisite, not boilerplate**: plain `pytest` today has zero Django integration — no `conftest.py`, no `DJANGO_SETTINGS_MODULE` anywhere — which is fine for the existing `crawler/tests/test_utils.py` (pure functions, no Django import), but `django.contrib.gis.geos` touches `django.conf.settings` on import and will raise `ImproperlyConfigured` without this
  - [x] 8.2 Add one minimal test asserting the environment is wired correctly — e.g. instantiate `django.contrib.gis.geos.Point(-74.05, 4.65)` to prove GDAL/GEOS are reachable from the app container, and that Django starts up against the `postgis` DB engine
  - [x] 8.3 Do not add `routes/tests/test_nearby.py`, `test_gtfs_refresh.py`, or `test_views.py` yet — those are Story 1.2's, once real models/services exist to test. They *will* need `@pytest.mark.django_db` once written — that's exactly what 8.1's wiring enables.

### Review Findings

**Code review (2026-08-19)** — 3-layer adversarial review (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against the working-tree diff.

- [x] [Review][Decision] `sprint-status.yaml` bundles an unrelated `epic-6`/`6-1-dependency-modernization-and-ruff-migration` backlog addition into this diff — that came from a separately-requested Story 6.1 draft, not from Story 1.1's implementation. **Resolved:** Vera chose to keep it bundled with Story 1.1's commit (no split needed).

- [x] [Review][Patch] Missing `STATIC_ROOT` causes `ImproperlyConfigured` on every template render, including `base.html` itself [app/settings.py] — verified empirically via `render_to_string('layout/base.html', {})`, not theoretical: `CompressedManifestStaticFilesStorage` requires `STATIC_ROOT` to be set, and this fires even in `DEBUG=True`/`runserver`, not just in a `collectstatic`-dependent production path. **Fixed:** added `STATIC_ROOT = BASE_DIR / 'staticfiles'`; added `staticfiles/` to `.gitignore`/`.dockerignore`. Re-verified: `render_to_string('layout/base.html', {})` now succeeds (2691 chars).
- [x] [Review][Patch] `POSTGRES_PASSWORD` silently defaults to an empty string on both ends — `os.environ.get('POSTGRES_PASSWORD', '')` in settings.py, and no `${VAR:?required}` guard in `docker-compose.yml` — so a missing `.env` value fails silently with a blank-password auth attempt instead of erroring clearly [app/settings.py, docker-compose.yml]. **Fixed:** `os.environ['POSTGRES_PASSWORD']` (raises `KeyError` loudly if unset) in settings.py; `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}` in docker-compose.yml.
- [x] [Review][Patch] `STORAGES['default']` is explicitly redefined to `FileSystemStorage`, which is already Django's built-in default for any key not overridden in `STORAGES` — dead, confusing config [app/settings.py]. **Fixed:** removed the redundant `'default'` block.
- [x] [Review][Patch] Missing trailing newlines in 4 new files [.dockerignore, Dockerfile, docker-compose.yml, static/css/tokens.css]. **Fixed.**
- [x] [Review][Patch] The `# last_updated:` comment in `sprint-status.yaml`'s header block is stale — out of sync with the live `last_updated:` field below it, because only the field was updated across multiple edits [sprint-status.yaml:2]. **Fixed:** synced to match the live field.
- [x] [Review][Patch] `binutils` is installed in the Dockerfile with no comment explaining why it's there (it's a real GDAL system-library-introspection dependency on Debian, not obviously so at a glance) [Dockerfile]. **Fixed:** added an explanatory comment; verified the comment doesn't break the backslash-continued `RUN` block (rebuilt, confirmed `apt-get` cleanup and package installation both still succeed).

- [x] [Review][Defer] No automatic `migrate` step before `runserver` in `docker-compose.yml`'s `app` command — deferred, matches what Task 1.2 explicitly specified (`runserver`-only for hot reload); worth revisiting once Story 1.8 writes the setup docs.
- [x] [Review][Defer] No non-root `USER` directive in the Dockerfile — deferred, production hardening not wired up yet (no `deploy.sh`/production topology exists to harden against).
- [x] [Review][Defer] No `HEALTHCHECK` on the `app` compose service (the `db` service has one) — deferred, same reasoning as above.
- [x] [Review][Defer] Gunicorn's `CMD` has no explicit `--timeout` — deferred, the 30s default is reasonable for current scope; revisit if real workloads surface timeout issues.

**Dismissed (8, by-design or out-of-scope, not defects):** `routes/migrations` deleted with no replacement (explicitly spec'd in AC #6/Task 6.2, confirmed against spec by the Acceptance Auditor — Story 1.2's job); `django.contrib.gis` installed with no spatial model field yet (Story 1.2's job); Gunicorn's `--workers 1` (explicitly required by AC #5, not an arbitrary hardcode); GEOS import at module level could break bare-host `pytest` (already documented as an unsupported workflow in Dev Notes — Docker is the supported path); no `.dockerignore` entry for a `staticfiles/` output dir (premature — that directory doesn't exist yet, nothing writes to it in this story's scope); `load_dotenv()`'s lack of `override=`/absence-handling (correct as-is — silent no-op on a missing `.env` and env-vars-take-precedence are `python-dotenv`'s standard, desired behavior); `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` not externalized (explicitly out of scope per this story's own guardrails, confirmed against spec by the Acceptance Auditor); no `restart` policy on compose services (out of scope for a local-dev-only compose file; revisit when a production topology/`deploy.sh` exists).

## Dev Notes

### Why exactly 1 Gunicorn worker (AC #5)

Django's local-memory cache (`LocMemCache`) is per-process, not shared. Story 3.1 depends on the live-tracking proxy calling the fragile, reverse-engineered transmiapp API roughly once per TTL window (~15–30s) *regardless of concurrent riders* — that bound only holds if there's exactly one cache, i.e. exactly one worker process. `N` workers would silently become `N` independent cache-miss paths, multiplying calls to an API this project deliberately avoids drawing attention to. Pin this explicitly in the Dockerfile CMD now; don't leave it at Gunicorn's default.

### Scope guardrails — do NOT do these in this story

The architecture doc's target project structure includes several things that look adjacent but belong to later stories. Adding them here would create merge conflicts or duplicate work:
- **No DRF, no `django.contrib.gis` serializers, no `services.py` files** — those land with the nearby-query endpoint (later Epic 1 stories) and Story 1.2's data model.
- **No Sentry integration** — Story 1.4 (GTFS Refresh Failure Alerting) owns this, including the PII-scrubbing config, which must be in place *before* any geolocation-touching endpoint ships (not this story).
- **No `LANGUAGE_CODE` change** — stays `'en-us'` for now; flipping to `'es'` is Epic 5's job (FR19), not Epic 1's.
- **No `.github/workflows/ci.yml`** — GitHub Actions CI isn't in this story's AC list; the architecture's "Implementation Sequence" places it after the frontend work, and no Epic 1 story currently claims it. Don't add it speculatively.
- **No `.env.example`** — Story 1.8 owns the full env-var documentation pass as part of the README rewrite.
- **No `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` hardening** — these are pre-existing gaps (hardcoded insecure key, `DEBUG = True`, empty `ALLOWED_HOSTS`) that predate this story and aren't in its AC. Leave them as-is; don't gold-plate.

### Current-state facts that affect this story

- `python-dotenv` is a listed dependency but is **only called from `telegram_bot/services.py`** today — `app/settings.py` has zero dotenv wiring. Task 3.4 is a real gap to close, not a formality.
- `DATABASES` currently points at `BASE_DIR / 'db.sqlite3'` with the plain `django.db.backends.sqlite3` engine (`app/settings.py`) — this whole block gets replaced (Task 3.3).
- `STATIC_URL = 'static/'` already exists; no `STATICFILES_DIRS` is currently defined, so it needs adding for Task 7.1's project-level `static/css/`.
- `INSTALLED_APPS` currently: `admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `app`, `routes`, `crawler` — `django.contrib.gis` is a new addition (Task 3.2), nothing else changes here.
- No `Dockerfile` or `docker-compose.yml` exist anywhere in the repo yet — both are created fresh by this story.
- `routes/migrations/` currently has `0001_initial.py` through `0007_alter_busstation_transmilenio_id.py` (7 files) plus `__init__.py`.
- Adding `'django.contrib.gis'` to `INSTALLED_APPS` means **any** `manage.py` invocation now needs GDAL/GEOS/PROJ importable at startup — including tests and lint-adjacent commands. Run everything through the `app` Docker Compose service, not a bare host `venv`, or these will fail with a cryptic `OSError` about GDAL not being found. This is worth a one-line callout in whatever the dev agent's own working notes are, since it's an easy thing to burn time on.
- `pytest-django` is not currently a dependency, and nothing sets `DJANGO_SETTINGS_MODULE` for test runs (`pytest.ini` has no `[pytest]` Django config, no `conftest.py` exists anywhere). Today's only test suite, `crawler/tests/test_utils.py`, works around this by never importing Django. Task 8 closes this gap — deliberately in this story, since Story 1.2 can't write real model/service tests without it.
- No `.dockerignore` exists yet, and the Dockerfile's build context is the whole repo root — without one, `COPY . .` would copy `.env` (real secrets), `venv/`, and `db.sqlite3` into the image. Task 2.5 adds it.

### Design token values (Task 7) — from `docs/visual-foundation-reference.html`

Light (default `:root`):
```css
--paper: #faf9f5;
--paper-raised: #ffffff;
--ink: #22251f;
--ink-soft: #4a4d43;
--line: #ddd9cc;
--line-strong: #c7c2b0;
--muted: #8c897c;
--accent: #4f7a5b;       /* Páramo green — app chrome only, never route identity */
--accent-soft: #dde8de;
--accent-ink: #1f3527;
--radius-sm: 8px;
--radius-md: 14px;
--radius-lg: 22px;
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 24px;
--space-6: 32px;
--space-8: 48px;
--font-ui: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
--font-data: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", monospace;
```

Dark (`:root[data-theme="dark"]`, plus the `prefers-color-scheme: dark` media-query fallback already in the reference file):
```css
--paper: #1b1d18;
--paper-raised: #24261f;
--ink: #ede9dd;
--ink-soft: #c3bfae;
--line: #38392f;
--line-strong: #4a4b3d;
--muted: #8f8c7c;
--accent: #7cab89;
--accent-soft: #263429;
--accent-ink: #cfe6d5;
```
Radii, spacing, and font stacks don't change between themes. The reference file also defines an alternate `data-accent="sabana"` (blue) variant — that's not the chosen direction; Páramo green (above) is the one this story ships. Corridor colors (Tier 2 of the four-tier color system) are **not** part of this story — they arrive with `Corridor` in Story 1.2.

### Architecture & pattern compliance

- Foundation is explicitly "Implementation Sequence" step 1 in `relaunch-architecture.md` (Decision Impact Analysis) — everything else in the epic blocks on this landing first.
- Python stays pinned at 3.11 (`relaunch-architecture.md` → Starter Template Evaluation → "Already Fixed by the Existing Codebase") — this is a version-target upgrade for Django/DB only, not a Python bump.
- `postgis/postgis:17-3.5` is the exact required image tag — not `18-3.6` or any other pairing (chosen deliberately for a stable, non-bleeding-edge solo-maintained production server).
- The new database must start **empty** — no in-place SQLite→PostGIS data migration exists or is planned; `refresh_gtfs` (Story 1.3) is the only path that populates real data.
- Coding standards continue as documented in `project-context.md`: one import per line, 79-char lines enforced by `black` (not flake8 — flake8 ignores `E501` per `.flake8`), Google-style docstrings on non-trivial public functions.

### Testing Standards

- `pytest` + `pytest-cov` per existing `pytest.ini` (`--cov=./ --no-cov-on-fail` — coverage is collected but a low/zero number doesn't fail the build)
- `pytest-django` + `DJANGO_SETTINGS_MODULE = app.settings` in `pytest.ini` are new as of this story (Task 8.1) — required for any test that imports `django.contrib.gis` or touches models/the DB. Future stories (starting 1.2) rely on this being in place already.
- Test file convention: `tests/` subdirectory per app, `test_<module>.py` naming (matches existing `crawler/tests/test_utils.py` precedent) — this story's smoke test can live at `routes/tests/test_foundation.py` (new `routes/tests/` dir, since none exists yet) or `app/tests/test_settings.py`; either is acceptable, pick one and be consistent for later stories to follow.

### Project Structure Notes

New files this story creates, matching `relaunch-architecture.md`'s target tree exactly:
- `Dockerfile` (root)
- `docker-compose.yml` (root)
- `.dockerignore` (root — not in the architecture doc's tree, but required to keep secrets/`venv/` out of the built image)
- `static/css/tokens.css` (new project-level `static/` dir — the architecture tree shows `static/js/` for later stories; this story adds the `css/` sibling)

Variance from the target tree (both intentional, both temporary):
- `routes/migrations/` ends this story with only `__init__.py` — the target tree shows a fresh `0001_initial.py`, which is Story 1.2's deliverable, not this one's.
- `routes/tests/` is created here (Task 8) ahead of the architecture doc's attribution of that directory to Story 1.2 — acceptable since a foundation smoke test has nowhere else sensible to live; Story 1.2 adds `test_nearby.py`/`test_gtfs_refresh.py`/`test_views.py` alongside it.

### References

- [Source: _bmad-output/planning-artifacts/relaunch-epics.md#Story 1.1: Foundation — Django 5.2 + PostgreSQL/PostGIS Upgrade] — story statement and full AC text
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Starter Template Evaluation] — Python 3.11 pin, Django 5.2 LTS choice, `postgis/postgis:17-3.5`, Docker Compose decision
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Core Architectural Decisions] — Gunicorn 1-worker rationale, caching backend, empty-DB-start policy
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Infrastructure & Deployment] — WhiteNoise/NFR1, CI/CD split (CI explicitly not this story)
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Project Structure & Boundaries] — target directory tree, file-by-file annotations
- [Source: _bmad-output/planning-artifacts/relaunch-ux-design-specification.md#Visual Design Foundation] — UX-DR1 token requirements (color/spacing/radius/type scale)
- [Source: docs/visual-foundation-reference.html] — authoritative CSS custom property values (light + dark)
- [Source: _bmad-output/project-context.md#Technology Stack & Versions] — current (pre-upgrade) stack baseline, coding-standard rules that continue unchanged
- [Source: app/settings.py] — current state verified directly: SQLite `DATABASES` block, no dotenv wiring, no `STATICFILES_DIRS`, `INSTALLED_APPS` list
- Version pins verified live (Aug 2026): [Django 5.2.16 security release](https://www.djangoproject.com/weblog/2026/jul/07/security-releases/), [psycopg 3.3.4 on PyPI](https://pypi.org/project/psycopg/), [whitenoise 6.12.0](https://pypi.org/project/whitenoise/), [gunicorn 26.0.0](https://pypi.org/project/gunicorn/)

## Change Log

- 2026-08-19: Implemented all 8 tasks. Django upgraded to 5.2.16 against PostGIS via Docker Compose, WhiteNoise configured, legacy SQLite archived, obsolete migrations deleted, design tokens landed, pytest-django wired in with a passing foundation smoke test. Status moved to `review`.
- 2026-08-19: Code review (3-layer adversarial: Blind Hunter, Edge Case Hunter, Acceptance Auditor) found 1 decision-needed item and 6 patch-worthy issues, most notably a real `STATIC_ROOT` misconfiguration that broke every template render — reproduced and fixed. All 6 patches applied and re-verified against a running PostGIS container; the 1 decision resolved (keep sprint-status.yaml's epic-6 addition bundled). 4 additional items deferred to `deferred-work.md` (non-root Docker user, app healthcheck, auto-migrate on boot, Gunicorn timeout) — legitimate but out of this story's scope. Status moved to `done`.

## Dev Agent Record

### Agent Model Used

### Debug Log References

- `docker build -t public_transport-app:test .` — clean build; verified GDAL/GEOS/Django import inside the container and confirmed `.env`/`venv/` are excluded from the image via `.dockerignore`.
- `docker compose up -d db` — `postgis/postgis:17-3.5` reached `healthy` via the `pg_isready` healthcheck.
- `docker compose run --rm app python manage.py check` — first run surfaced `staticfiles.W004` (empty `static/` dir, before Task 7 landed); re-run after Task 7 returned "System check identified no issues".
- `docker compose run --rm app python manage.py migrate` — applied all built-in Django app migrations (admin/auth/contenttypes/sessions) against PostGIS; `routes` correctly has zero migrations to apply (expected — Task 6).
- `docker compose run --rm app python -m pytest routes/tests/test_foundation.py -v` — first run (before Task 8's `pytest.ini` change) failed `test_database_engine_is_postgis` with `ImproperlyConfigured: ... DJANGO_SETTINGS_MODULE`, confirming the gap identified in story validation; second run after adding `DJANGO_SETTINGS_MODULE = app.settings` to `pytest.ini` passed all 3.
- `docker compose run --rm app python -m pytest -q` (full suite): 78 passed, 3 pre-existing failures in `crawler/tests/test_utils.py` (`parse_schedule` weekday parsing) — confirmed via `git diff --stat crawler/` (empty) that this story touches nothing in `crawler/`; not a regression.
- `black --check` / `flake8` on all changed Python files — clean after one `black` reformat pass on `app/settings.py` and `routes/tests/test_foundation.py`.
- `docker compose down -v` — stack and volume torn down after validation.

### Completion Notes List

- All 7 ACs implemented and verified against a real running PostGIS container, not just code review — see Debug Log References above for the actual commands run.
- `db.sqlite3` archived to `db.sqlite3.bak` (filesystem rename; both are gitignored, so this isn't a tracked git change — added `db.sqlite3.bak` to `.gitignore` alongside the existing `db.sqlite3` entry for completeness).
- Foundation smoke test suite: `routes/tests/test_foundation.py` (3 tests, all passing) — proves GDAL/GEOS import, the `postgis` DB engine is active, and Django is on 5.2.x.
- Pre-existing, unrelated test failures in `crawler/tests/test_utils.py` (3 tests) were left as-is — out of scope for this story (crawler app untouched; scheduled for retirement once the GTFS pipeline lands, per architecture).
- Scope guardrails from Dev Notes were followed: no DRF, no Sentry, no `LANGUAGE_CODE` change, no CI workflow, no `.env.example`, no `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` hardening.

### File List

**Added:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `static/css/tokens.css`
- `routes/tests/__init__.py`
- `routes/tests/test_foundation.py`

**Modified:**
- `app/settings.py` — `django.contrib.gis` added to `INSTALLED_APPS`; `DATABASES` switched to `django.contrib.gis.db.backends.postgis` reading env vars (`POSTGRES_PASSWORD` now raises `KeyError` if unset, per review fix); `python-dotenv` wired in via `load_dotenv()`; `WhiteNoiseMiddleware` inserted after `SecurityMiddleware`; `STATICFILES_DIRS`, `STATIC_ROOT` (added per review fix), and `STORAGES` (WhiteNoise compressed-manifest backend, redundant `default` key removed per review fix) added
- `app/templates/layout/base.html` — `{% load static %}` + `<link>` to `static/css/tokens.css` in `<head>`
- `requirements.txt` — `Django==5.2.16`, `psycopg[binary]==3.3.4`, `whitenoise==6.12.0`, `gunicorn==26.0.0`, `pytest-django==4.14.0` added
- `pytest.ini` — `DJANGO_SETTINGS_MODULE = app.settings` added
- `.gitignore` — `db.sqlite3.bak`, `staticfiles/` (review fix) added
- `.dockerignore` — `staticfiles/` added (review fix)
- `docker-compose.yml` — `${POSTGRES_PASSWORD:?...}` required-var guard added (review fix)
- `Dockerfile` — comment added explaining `binutils` (review fix)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story status tracking; stale header comment synced (review fix)

**Deleted:**
- `routes/migrations/0001_initial.py` through `routes/migrations/0007_alter_busstation_transmilenio_id.py` (7 files; `__init__.py` kept)

**Renamed (filesystem, untracked):**
- `db.sqlite3` → `db.sqlite3.bak`
