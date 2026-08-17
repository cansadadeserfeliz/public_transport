---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/relaunch-prd.md
  - _bmad-output/planning-artifacts/relaunch-product-brief.md
  - _bmad-output/planning-artifacts/relaunch-implementation-readiness-report-2026-08-05.md
  - _bmad-output/project-context.md
workflowType: 'architecture'
project_name: 'public_transport'
user_name: 'Vera'
date: '2026-08-05'
lastStep: 8
status: 'complete'
completedAt: '2026-08-17'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

20 FRs across 6 categories. The load-bearing group is **Nearby Route & Stop Discovery (FR1–FR4)** — a geolocation-anchored, multi-route "nearby" query that is the PRD's core differentiator; everything else (Route & Stop Browsing FR5–FR8, Live Bus Tracking FR9–FR10, Data Currency FR11–FR13, Trust & Transparency FR14–FR16, Sharing FR17–FR18, Localization/Accessibility FR19–FR20) supports or surrounds it. FR1–FR4 require spatial querying against route/stop geometry that does not exist in the current schema (`routes/models.py` stores `latitude`/`longitude` as plain `DecimalField`, no PostGIS, no spatial index).

**Non-Functional Requirements:**

13 NFRs across Performance, Security, Reliability & Monitoring, and Accessibility. The ones that will directly drive architecture:

- **NFR2** (<1s nearby-query response, local static dataset) + **NFR5** (geolocation coordinates never logged or persisted server-side) together sharpen the PRD's own unresolved question — client-side vs. server-side computation of the nearby-routes query — into the first real architectural decision to make.
- **NFR6** (transmiapp credentials/headers server-side only, never in client JS) forces live bus tracking through a backend proxy; the browser can never call transmiapp directly.
- **NFR8–NFR10** (pipeline failure alerts, live-tracking failure alerts, static/live availability fully decoupled) mean the GTFS refresh pipeline and the live-tracking service must be architecturally separate components that fail independently, not one integrated service.
- **NFR11–NFR13** (WCAG AA contrast, readable fonts, keyboard nav) are UI-implementation constraints, not backend architecture, but need to be carried into any component/template decisions later.

**Scale & Complexity:**

- Primary domain: Full-stack web — server-rendered MPA (per PRD's explicit choice) with a spatial query backend and a live-tracking integration layer
- Complexity level: Medium (per PRD's own classification) — driven by the live-position dependency on an undocumented third-party API and a GTFS refresh pipeline that must tolerate ongoing route restructuring, not by domain regulation or team scale
- Estimated architectural components: ~5 — (1) static GTFS data store + refresh pipeline, (2) spatial nearby-query service, (3) live-tracking proxy/isolation layer, (4) monitoring/alerting, (5) server-rendered web frontend

### Technical Constraints & Dependencies

- **Brownfield:** existing Django 4.2.4 / SQLite / Scrapy 2.10.1 codebase (dormant since Sep 2023) must be evolved, not replaced wholesale — `routes/`, `crawler/`, `transmiapp/`, `telegram_bot/` apps already exist and the running app must stay operable through the migration.
- **Near-zero-cost ceiling:** map tiles, hosting, and a geospatial-capable database all need to fit a free/near-free tier — a hard constraint on technology choices, not a preference.
- **Solo, nights-and-weekends maintainer:** monitoring/alerting must be low-effort to build and to actually notice (ties to NFR8–NFR9), and the stack should avoid operational complexity that a single part-time person can't sustain.
- **Unofficial live-tracking dependency:** `transmiapp/services.py` calls an undocumented, ToS-fragile third-party API (spoofed headers, hardcoded appid) that is expected to break without warning — this is a confirmed, accepted risk (official GTFS-Realtime endpoints return 404), not something to design around fixing.
- **GTFS static data replaces the old scraper** as the source of truth for routes/stations/schedules — the existing `crawler/` (Scrapy) pipeline that scraped TransMilenio's HTML is being superseded, not extended.

### Cross-Cutting Concerns Identified

- **Client-vs-server nearby-query placement** — affects privacy guarantee strength (NFR5/FR16), query performance (NFR2), and frontend architecture (how much routing/comparison logic lives in JS vs. server templates). Unresolved; first decision to make.
- **Third-party API isolation** — transmiapp fragility must not propagate into static route/stop browsing (NFR10); needs a clear boundary/circuit-breaker-style pattern, independently monitored.
- **Geospatial data modeling migration** — moving from ad-hoc lat/lng decimals to a proper spatial schema (likely PostGIS) touches the data model, the refresh pipeline, and the nearby-query implementation all at once.
- **Solo-maintainer operability** — logging, alerting, and deployment simplicity are cross-cutting design pressures on every component, not just the pipeline (ties to the brief's "doesn't die the way v1 did" success criterion).
- **Always-visible trust UI** (non-affiliation disclaimer, attribution, location-use disclosure — FR14–FR16) — needs to be structurally guaranteed (e.g., base template) rather than left to be repeated per-page.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web (server-rendered MPA) — brownfield.

**Adaptation note:** No starter template applies here — this is a brownfield rebuild, not a greenfield bootstrap. The existing Django app *is* the starter. This section documents what the codebase already fixes vs. the new-component decisions made in this step.

### Already Fixed by the Existing Codebase (not re-decided here)

- Python 3.11, Django 4.2.4, SQLite (dev) — `app/settings.py`
- Mapbox GL JS already wired into 3 templates (`base.html`, `route_detail.html`, `busstation_detail.html`) — superseded by the decision below
- `routes/`, `crawler/` (Scrapy), `transmiapp/`, `telegram_bot/` Django apps exist; `crawler/` is superseded by the GTFS refresh pipeline

### New Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Django version target | **Django 5.2 LTS** | Current LTS as of Aug 2026 (4.2 LTS support ends April 2026); satisfies PRD's "current Django/Python versions" modernization requirement. |
| Geospatial database | **PostgreSQL + PostGIS**, via GeoDjango | Standard Django-native geospatial stack; replaces SQLite + plain `DecimalField` lat/lng. Docker image: `postgis/postgis:17-3.5` — PostgreSQL 17 paired with PostGIS 3.5 (stable pairing, avoiding the bleeding-edge `18-3.6` tag for a solo-maintained production server). |
| Map rendering library | **MapLibre GL JS** (v6.x, currently 6.3.0) replacing Mapbox GL | Open-source, no usage cap, no vendor billing account — matches the non-commercial/no-cost-ceiling stance more directly than Mapbox's free-tier model. **Caveat:** MapLibre GL JS v6 requires **WebGL2** (dropped WebGL1 support) — WebGL2 has shipped in Android Chrome since ~2017, so this should be safe against the PRD's "mid-range Android" target, but very old/low-end devices are the edge case to watch. |
| Deployment platform | **Docker on the existing DigitalOcean Linux server** (self-managed, not a PaaS) | Zero incremental hosting cost since the server is already owned; deployed via Docker on that server. |
| Local development environment | **Docker Compose** | Runs Django + PostGIS (and any supporting services) locally with one command, mirroring the production container topology — keeps local/prod parity for a solo maintainer. |

### Architectural Implications Carried Forward

- A **data migration path** is now implied: existing `BusStation.latitude`/`longitude` (`DecimalField`) → PostGIS `PointField`, and `Route`/`RouteStations` geometry needs to be populated from GTFS shapes, not the old scraper.
- Self-managed Docker-on-VPS means **the maintainer owns monitoring/alerting infrastructure end-to-end** (ties to NFR8–NFR9) — no managed-platform health checks to lean on; this should be an explicit component in later architecture steps, not an afterthought.
- **Note:** the Django 4.2.4 → 5.2 upgrade and SQLite → PostgreSQL/PostGIS migration should be the **first implementation story** — everything else (GTFS pipeline, nearby-query, live tracking) depends on this foundation being in place first.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Nearby-query computation placement (server-side PostGIS)
- GTFS refresh trigger model (manual, not scheduled) — conflicts with PRD FR11/NFR8 as written; see note below
- Live-tracking proxy caching strategy
- API framework (DRF)

**Important Decisions (Shape Architecture):**
- Caching backend (Django local-memory)
- Frontend build approach (no-build)
- CI/CD split (CI automated, CD manual)
- Monitoring/error-reporting tool (Sentry)

**Deferred Decisions (Post-MVP):**
- Redis or other shared cache backend — only needed if the app outgrows a single process/single VPS
- Automated GTFS refresh scheduling — explicitly deferred per this step's decision; revisit if manual sync becomes a maintenance burden

### Data Architecture

- **Database:** PostgreSQL + PostGIS via GeoDjango (decided in Starter Template Evaluation), Docker image `postgis/postgis:17-3.5`.
- **Nearby-query computation (FR1–FR4):** **Server-side**, using PostGIS `ST_DWithin`. Coordinates are sent from the client to the backend on each request but are never logged or persisted (NFR5) — this is a **policy-level guarantee enforced in code**, not an architectural guarantee by construction (contrast with the client-side alternative that was considered and not chosen). Concretely: the view/serializer handling this query must exclude the raw coordinate values from Django's request logging, and — since Sentry is also in the stack — from Sentry's captured request data (see Infrastructure & Deployment below).
- **GTFS refresh strategy (FR11):** **Full replace inside a single DB transaction** per sync — each run rebuilds routes/stops/schedules from scratch and atomically swaps in the new dataset, rather than diffing/upserting. Avoids stale-record edge cases from partial updates.
- **GTFS refresh trigger model:** **Manually invoked** (a Django management command run by the maintainer), **not a scheduled/cron job**. ⚠️ **This deviates from FR11 as currently written** ("recurring schedule... without manual intervention") and from NFR8 ("alert within 24 hours of a missed or failed scheduled run" — there is no "scheduled run" to miss if it's manual). This was an explicit, informed decision (not an oversight): confirmed with the user, who will update the PRD (FR11/NFR8) to match after this architecture document is complete, via `bmad-edit-prd` or `bmad-correct-course`. **Action item, not yet done.**
- **Caching backend:** Django's local-memory cache (in-process, no separate cache service/container). Chosen for zero added infrastructure at friends-and-family scale; revisit only if the app grows beyond a single worker process.

### Authentication & Security

- **No user accounts, authentication, or authorization** (NFR4) — no auth middleware, no session-based user state beyond Django's default CSRF protection.
- **HTTPS-only in production; no secrets committed to version control** (NFR7) — continues the existing `python-dotenv` pattern already in the codebase.
- **transmiapp credentials (NFR6):** spoofed User-Agent, hardcoded appid, and any other transmiapp-specific headers live **only** in server-side code (the live-tracking proxy view/service), never serialized to any client-facing response or exposed in client-side JS.
- **Geolocation privacy (NFR5):** coordinates received by the server-side nearby-query endpoint must not appear in: application logs, Django's default request logging, or Sentry's captured request context (`send_default_pii=False`, plus explicit scrubbing of the relevant query params via Sentry's `before_send` hook if needed). This is a concrete code-review checklist item, not a one-time setting.

### API & Communication Patterns

- **API framework:** Django REST Framework (all new JSON endpoints — nearby-query, live-position, route/stop GeoJSON — go through DRF serializers/views consistently, rather than mixing DRF with raw `JsonResponse`). Verified: DRF 3.17.1 (latest, PyPI) supports Django 5.2.
- **Live-tracking proxy behavior (NFR6, NFR13):** **On-demand per client request**, backed by a short-TTL (~15–30s) entry in the same Django local-memory cache — not a persistent background poller process. Rationale: avoids running an extra long-lived process (memory constraint on the VPS), and naturally bounds request volume to the unofficial transmiapp API to roughly one call per TTL window regardless of concurrent users, which is also the named risk mitigation (avoid drawing attention to the reverse-engineered endpoint) from the PRD.
- **Error handling:** Exceptions (including transmiapp response-format changes, per NFR13) are captured by Sentry automatically via its Django integration (`sentry-sdk[django]`, current major version 2.x).

### Frontend Architecture

- **No-build, script tags.** MapLibre GL JS (v6.x) loaded via `<script>`/CDN, custom JS shipped as plain ES modules through Django's static files app — no npm build pipeline, no bundler. Matches the PRD's explicit "no SPA framework/build pipeline unless genuinely needed" stance and keeps local dev/deploy simple for a solo maintainer.
- **Routing:** server-rendered Django URLs (MPA), MapLibre map instances initialized per-page against the DRF JSON endpoints.
- **Progressive enhancement:** core route/stop content renders server-side and works without JS; the map/live-tracking layer loads as an enhancement on top (per PRD Web App Specific Requirements).

### Infrastructure & Deployment

- **Hosting:** Docker containers on the existing, already-owned DigitalOcean Linux VPS (decided in Starter Template Evaluation) — zero incremental hosting cost.
- **Local development:** Docker Compose (Django + PostGIS, mirroring production container topology).
- **CI:** GitHub Actions runs `pytest` (with coverage, per existing `pytest.ini` config) and lint (`black`, `flake8`) on every push.
- **CD:** **Manual** — a bash script on the VPS pulls new images and replaces the running containers. No automated deploy-on-merge for now.
- **Monitoring & error reporting (NFR8, NFR9):** **Sentry** (free tier) captures exceptions from both the GTFS refresh command and the live-tracking proxy. Because GTFS sync is manual (see Data Architecture above), NFR8's "missed scheduled run" alerting doesn't apply as originally written — the maintainer already knows a sync happened because they triggered it, and Sentry surfaces any error during that run immediately. NFR9 (transmiapp failures/format changes) is satisfied more directly: any exception raised by the live-tracking proxy is captured and visible in Sentry without needing a separate scheduled health check. **No email/cron-based alerting** — Sentry's own issue dashboard is the maintainer's monitoring surface.
- **Scaling strategy:** None planned — single VPS, single Docker Compose stack, sized for friends-and-family MVP scale.

### Decision Impact Analysis

**Implementation Sequence:**
1. Django 4.2.4 → 5.2 upgrade + SQLite → PostgreSQL/PostGIS migration (foundation; blocks everything else)
2. GTFS data model + manual refresh management command (full-replace-in-transaction)
3. Server-side nearby-query endpoint (DRF + PostGIS `ST_DWithin`), with coordinate-logging exclusions in place from the start
4. Live-tracking proxy (on-demand + short-TTL cache), replacing direct client calls if any exist today
5. Sentry integration, configured with PII scrubbing before any endpoint that touches geolocation goes live
6. Frontend: MapLibre GL (no-build) map views wired to the new endpoints
7. GitHub Actions CI; manual CD script

**Cross-Component Dependencies:**
- The nearby-query endpoint's privacy guarantee (NFR5) depends on Sentry PII scrubbing being configured *before* that endpoint is exposed — sequencing matters, not just component presence.
- The live-tracking proxy's cache TTL and the frontend's polling/refresh behavior are coupled — the frontend should not poll more frequently than the cache TTL, or it gains nothing while still adding client-side complexity.
- GTFS refresh (manual) and Sentry error capture together are what stand in for the PRD's originally-scheduled, auto-alerting pipeline — both must be in place before FR11/NFR8 can be considered satisfied under the revised (to-be-updated) requirement wording.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 6 areas where different implementers (or AI agents across sessions) could diverge — API endpoint naming, GeoJSON vs. plain-JSON response shape, the live-tracking "unavailable" contract, where business logic lives, logging/error-handling boundaries, and JSON field casing.

### Naming Patterns

**Database Naming:**
- Django default conventions throughout — no manual overrides. Table names auto-derive as `<app_label>_<modelname>` lowercase (e.g. `routes_route`, `routes_busstation`), matching the existing schema.
- Columns: snake_case, Django default (e.g. `route_type`, `transmilenio_id`).
- Foreign keys: Django default `<field_name>_id` (e.g. `route_id`, `bus_station_id`), as already used in `RouteStations`.
- New PostGIS geometry fields: name by what they represent, not by type — `location` (`PointField`) on `BusStation`, `path` (`LineStringField` or `MultiLineStringField`) on `Route`, not `geom` or `the_geog`.
- Spatial indexes: let GeoDjango auto-create the GiST index (default behavior for geometry fields) — no manual index naming needed.

**API Naming:**
- URL segments: kebab-case for multi-word paths, plural nouns for collections — continues the existing `bus-stations/` precedent. New endpoints: `stops/nearby/`, `routes/<id>/live-positions/`.
- Django URL pattern `name=`: snake_case (`bus_station_detail`, `route_buses`), matching existing `urls.py`/`api_urls.py`.
- Query parameters: snake_case (`lat`, `lng`, `radius_m`), not camelCase — matches Python/Django convention throughout the stack.
- DRF view naming: `<Model><Action>View` for template views (existing pattern: `RouteDetailView`), `<Model><Action>View(generics.XxxAPIView)` for DRF endpoints — migrate existing ad-hoc `RouteBusesAPIView`/`RouteStationsAPIView` (currently `DetailView` subclasses with a manual `get()`) to real DRF generic views (`RetrieveAPIView`/`ListAPIView`) rather than ViewSets+routers, since each endpoint is already explicitly declared in `api_urls.py` — no reason to add router indirection for a small, fixed endpoint set.

**Code Naming:**
- Continues `project-context.md`'s existing rules: snake_case functions/variables, PascalCase classes, one import per line, 79-char line length via `black`, Google-style docstrings on public service functions, `@dataclass` for typed in-memory value objects (e.g. a `NearbyStop` result object, a `BusPosition` value from the transmiapp proxy) rather than passing raw dicts between layers.
- File naming: snake_case module names (`nearby_service.py`, `live_tracking.py`), matching existing `services.py` precedent.

### Structure Patterns

**Project Organization:**
- Business logic (spatial queries, GTFS parsing, transmiapp proxy calls) lives in each app's `services.py`, not in views — continues the existing `transmiapp/services.py` precedent. Views/DRF endpoints stay thin: parse input, call a service function, serialize the result.
- New Django apps follow the existing flat-per-domain structure (`routes/`, `transmiapp/`) rather than a nested `apps/` package — e.g. a GTFS-refresh management command lives inside `routes/management/commands/`, not a new top-level app, since it operates on `routes` models.
- `crawler/` (Scrapy) is retired once the GTFS pipeline replaces it — not extended with new spiders.

**File Structure:**
- Tests: `tests/` subdirectory per app, `test_<module>.py` files — matches the existing `crawler/tests/test_utils.py` precedent. No co-located `*.test.py` files.
- Static assets: standard per-app Django `static/<app_name>/` directories for the no-build JS/CSS (MapLibre init scripts, map styles).
- Config/secrets: `.env` + `python-dotenv`, continuing the existing pattern — never a new config format introduced alongside it.

### Format Patterns

**API Response Formats:**
- **Map/geometry endpoints** (routes, stops, nearby-query results): standard **GeoJSON** (`FeatureCollection` / `Feature`, RFC 7946) — not a custom wrapper. This is a real, existing spec MapLibre GL consumes natively; inventing a custom shape here would be pure downside.
- **Non-geometry endpoints** (e.g. live-position list without map rendering): plain DRF serializer output, unwrapped (no `{data: ...}` envelope) — DRF's default.
- **Errors:** DRF's default `{"detail": "..."}` shape for standard HTTP errors; extend with a `"code"` field only for app-specific error conditions the frontend needs to branch on (see live-tracking "unavailable" contract below) — not for generic 4xx/5xx.
- **Dates/times:** ISO 8601 strings, DRF's default — no custom date formatting.
- **JSON field casing:** snake_case everywhere, including inside GeoJSON `properties` objects — matches Python/Django convention project-wide; no camelCase translation layer.

**Live-Tracking "Unavailable" Contract (FR10) — must be explicit, not inferred:**
- When the transmiapp proxy cannot get a live position (upstream down, format changed, cache miss with failed refetch), the API returns **HTTP 200** (not a 5xx — this is an expected, routine state, not a server error) with an explicit field: `"status": "unavailable"` on that route/bus entry, distinct from a normal `"status": "live"` entry with position data. The frontend renders these two states differently (per FR10). **Never**: omit the bus from the response, return `null` for position silently, or return stale cached data past its TTL without marking it unavailable.

### Communication Patterns

**Event Systems:** Not applicable — no pub/sub or event bus in this architecture (single Django process, request/response + one manual management command). Do not introduce Django signals for cross-app communication where a direct service-function call is simpler; reserve signals only for genuine Django-lifecycle hooks (e.g. `post_save` if ever needed), not as a general messaging pattern.

**State Management (Frontend):** No JS framework, no global state store (per the no-build decision in Core Architectural Decisions). State lives in the DOM and small per-page vanilla-JS modules; each page's map/live-tracking widget owns its own state, fetched fresh from the DRF/GeoJSON endpoints — no shared client-side cache between pages.

**Logging:**
- Standard Python `logging`, `logger = logging.getLogger(__name__)` per module — no third-party logging framework beyond Sentry's Django integration.
- Levels: `ERROR` for unhandled exceptions (auto-captured by Sentry), `WARNING` for expected-but-notable degraded states (transmiapp unavailable, GTFS refresh partially stale), `INFO` for routine operational events (GTFS sync started/completed, row counts) — not `DEBUG`-level noise in production.

### Process Patterns

**Error Handling:**
- `try/except` boundaries sit at **external-integration points only** — the transmiapp HTTP call, the GTFS file fetch/parse — not scattered through internal service logic. Internal code trusts its own data once past that boundary (continues the project's existing "trust internal code" philosophy).
- Uncaught exceptions propagate to Sentry automatically via the Django integration — don't hand-roll a parallel error-reporting path.
- User-facing error messages (if any surface directly, e.g. a failed nearby-query request) stay in plain-language Spanish, consistent with FR19 — no raw exception text or stack traces ever reach the client.

**Loading States:**
- No global loading state. Each map/live-tracking widget shows a local, minimal placeholder (e.g. a text label, not a spinner-heavy UI) while its own fetch is in flight — consistent with the "lean payloads, minimal JS" performance stance (NFR1) and progressive enhancement (page content is usable before the widget resolves at all).

### Enforcement Guidelines

**All implementers (human or AI agent) MUST:**
- Use GeoJSON for any endpoint that returns geometry, and DRF's default plain shape otherwise — never invent a third response shape.
- Implement the three-state live-position contract (`"live"` / `"unavailable"`, HTTP 200 either way) exactly as specified above — this is the concrete mechanism behind FR10 and easy to get subtly wrong.
- Put business logic in `services.py`, not views — views stay thin.
- Never log or send geolocation coordinates to Sentry/logs (ties back to NFR5 in Core Architectural Decisions) — this is re-stated here because it's a pattern violation risk, not just a one-time config setting.

**Pattern Enforcement:**
- Verified via code review against this document before merge (solo maintainer — self-review checklist, not automated).
- Pattern violations or necessary exceptions get noted directly in this document (a new dated note under the relevant section), not silently overridden.
- This document is the source of truth for "how we do things here" going forward — update it deliberately, don't let implementation drift ahead of it.

### Pattern Examples

**Good Examples:**
- `GET /api/stops/nearby/?lat=4.65&lng=-74.05&radius_m=400` → `FeatureCollection` of stop `Feature`s, each with `properties.routes` listing route codes serving that stop.
- `GET /api/routes/12/live-positions/` → `{"buses": [{"id": "...", "status": "live", "location": {...}}, {"id": "...", "status": "unavailable"}]}`.

**Anti-Patterns:**
- Returning HTTP 503 for a routine "transmiapp is currently down" state (that's an expected, designed-for condition per NFR3/FR10, not a server error).
- A view function that calls `requests.get()` directly against transmiapp instead of going through `transmiapp/services.py`.
- camelCase creeping into any JSON response because a snippet was copied from a non-Python reference.

## Project Structure & Boundaries

### Complete Project Directory Structure

```
public_transport/
├── README.md
├── manage.py
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── .flake8
├── .editorconfig
├── .pre-commit-config.yaml
├── .env                          # gitignored; secrets (transmiapp headers, Sentry DSN, DB creds)
├── .env.example                  # NEW — documents required vars without values
├── .gitignore
├── Dockerfile                    # NEW — app image (Python 3.11, GDAL/GEOS system deps for GeoDjango)
├── docker-compose.yml            # NEW — local dev: app + postgis/postgis:17-3.5
├── deploy.sh                     # NEW — manual CD: pulls new images, replaces containers on the DO VPS
├── .github/
│   └── workflows/
│       └── ci.yml                # NEW — pytest + black + flake8 on push
├── app/                          # Django project config
│   ├── __init__.py
│   ├── settings.py                # UPDATED — PostGIS DB engine, DRF, Sentry init, LANGUAGE_CODE='es', cache config
│   ├── urls.py                    # UPDATED — mounts routes.urls, routes.api_urls, transmiapp.api_urls
│   ├── asgi.py / wsgi.py
│   └── templates/
│       └── layout/
│           └── base.html          # UPDATED — always-visible footer: non-affiliation (FR14), attribution (FR15), location-use notice (FR16)
├── routes/                       # Core domain app: routes, stops, nearby-query, browsing
│   ├── __init__.py
│   ├── apps.py
│   ├── admin.py
│   ├── models.py                  # UPDATED — BusStation.location (PointField), Route.path (geometry), replaces lat/lng DecimalFields
│   ├── serializers.py             # NEW — DRF serializers (GeoJSON for stops/routes, plain for lists)
│   ├── views.py                   # UPDATED — existing template views kept; ad-hoc APIViews migrated to DRF generics
│   ├── urls.py                    # existing template-view URLs (home, route_detail, bus-stations/)
│   ├── api_urls.py                # UPDATED — + stops/nearby/, routes/<id>/stations/ as DRF endpoints
│   ├── services/                  # NEW — business logic, thin views call into here
│   │   ├── __init__.py
│   │   ├── nearby.py               # FR1–FR4: PostGIS ST_DWithin query logic
│   │   └── gtfs_refresh.py         # FR11: parses official GTFS feed, full-replace-in-transaction
│   ├── management/
│   │   └── commands/
│   │       ├── load_bus_stations.py  # existing
│   │       └── refresh_gtfs.py       # NEW — manually-invoked management command (FR11)
│   ├── migrations/                # existing 0001–0007 + new PostGIS migration(s)
│   ├── templates/routes/          # existing: home, route_detail, busstation_list, busstation_detail
│   └── tests/                     # NEW — no tests exist for this app today
│       ├── __init__.py
│       ├── test_nearby.py
│       ├── test_gtfs_refresh.py
│       └── test_views.py
├── transmiapp/                   # Live-tracking isolation boundary (NFR6, NFR10, NFR13)
│   ├── __init__.py
│   ├── services.py                # UPDATED — adds short-TTL cache wrapper around existing proxy calls
│   ├── serializers.py             # NEW — "live" / "unavailable" contract (see Implementation Patterns)
│   ├── api_urls.py                # NEW — routes/<id>/live-positions/ (or mounted under routes/ URLs)
│   ├── views.py                   # NEW — DRF view calling transmiapp.services, never exposes credentials
│   └── tests/                     # NEW
│       ├── __init__.py
│       └── test_live_positions.py
├── telegram_bot/                 # UNCHANGED — dormant, out of scope for v1 (Phase 2 revival)
│   ├── __init__.py
│   ├── run.py
│   └── services.py
├── crawler/                      # RETIRED — Scrapy scraper superseded by routes/services/gtfs_refresh.py
│   └── ...                        # left in place until GTFS pipeline is confirmed working, then removed
├── data/                         # existing seed geojson files (from transmidata) — candidate input for initial GTFS migration/seed, not the ongoing refresh source
│   ├── Estaciones_Troncales_de_TRANSMILENIO.geojson
│   ├── Paraderos_Zonales_del_SITP.geojson
│   ├── Rutas_Zonales_SITP.geojson
│   └── Trazados_Troncales_de_TRANSMILENIO.geojson
└── static/                       # NEW (project-level) or per-app static/routes/, static/transmiapp/
    └── js/
        ├── map-init.js            # MapLibre GL setup, no-build ES module
        └── live-tracking.js       # polls live-positions endpoint, renders "unavailable" state
```

**Note:** `db.sqlite3` and all `__pycache__/` directories are dev artifacts, not part of the structure going forward — SQLite is replaced by PostGIS per Core Architectural Decisions.

### Architectural Boundaries

**API Boundaries:**
- `routes/api_urls.py` — DRF endpoints for stops/routes/nearby-query (GeoJSON responses).
- `transmiapp/api_urls.py` — DRF endpoint(s) for live-position data (`"live"`/`"unavailable"` contract). Kept in its own app/URL namespace, not merged into `routes/`, so the isolation boundary from NFR10 is visible in the codebase structure itself, not just in prose.
- No authentication boundary — no user accounts (NFR4).

**Component Boundaries:**
- Frontend: no shared client-side state between pages — each template's map/live-tracking widget is self-contained JS talking only to its own page's endpoints (per Implementation Patterns).
- `routes/services/nearby.py` and `routes/services/gtfs_refresh.py` are the only code paths allowed to run raw PostGIS spatial queries — views/serializers never construct spatial queries directly.
- `transmiapp/services.py` is the **only** module allowed to import `requests` and call the transmiapp host — enforced as a code-review rule (see Implementation Patterns anti-pattern), not (yet) a lint rule.

**Data Boundaries:**
- `routes` app owns `Route`, `RouteStations`, `BusStation` models and their PostGIS geometry — the single source of truth for static data.
- `transmiapp` app owns no persistent models — live positions are cache-only (short TTL), never written to the database, consistent with treating live data as inherently transient/unreliable (NFR10).
- Django's local-memory cache is process-local — not shared across multiple app instances if the deployment ever scales beyond one process (documented as a deferred concern in Core Architectural Decisions).

### Requirements to Structure Mapping

**FR Category Mapping:**
- **Nearby Route & Stop Discovery (FR1–FR4):** `routes/services/nearby.py`, `routes/api_urls.py` (`stops/nearby/`), `routes/serializers.py` (GeoJSON), `static/js/map-init.js`
- **Route & Stop Browsing (FR5–FR8):** `routes/views.py`, `routes/urls.py`, `routes/templates/routes/` (existing, largely unchanged)
- **Live Bus Tracking (FR9–FR10):** `transmiapp/` app in full — services, serializers, views, tests
- **Data Currency (FR11–FR13):** `routes/services/gtfs_refresh.py`, `routes/management/commands/refresh_gtfs.py`, Sentry integration in `app/settings.py`
- **Trust & Transparency (FR14–FR16):** `app/templates/layout/base.html` footer
- **Sharing (FR17–FR18):** existing `routes/urls.py` per-route/per-stop URL patterns (already shareable; no new structure needed)
- **Localization & Accessibility (FR19–FR20):** `app/settings.py` (`LANGUAGE_CODE='es'`), template-level markup/CSS (no new app)

**Cross-Cutting Concerns:**
- **Geolocation privacy (NFR5):** `app/settings.py` (Sentry `before_send` scrubbing), `routes/services/nearby.py` (no coordinate logging) — spans config and service layer together.
- **Solo-maintainer operability:** `.github/workflows/ci.yml`, `deploy.sh`, Sentry config — the three artifacts that together replace the "team of one" with automated checks + one manual step.

### Integration Points

**Internal Communication:** Direct Python function calls between views → services → models within a single Django process. No internal message queue or event bus (per Implementation Patterns — not applicable at this scale).

**External Integrations:**
- Official GTFS static feed (ArcGIS Hub / Datos Abiertos Bogotá) — pulled by `routes/services/gtfs_refresh.py`, manually triggered.
- transmiapp unofficial API — called only by `transmiapp/services.py`.
- Sentry — error/exception reporting from anywhere in the app via the Django integration.
- Map tiles — MapLibre GL JS fetches vector tiles from a tile provider at runtime (client-side); no server-side tile proxying.

**Data Flow:**
1. Maintainer runs `refresh_gtfs` manually → GTFS feed parsed → full-replace transaction into `routes` PostGIS tables.
2. Rider's browser sends coordinates to `stops/nearby/` → `routes/services/nearby.py` runs `ST_DWithin` → GeoJSON response → MapLibre renders.
3. Rider's browser requests `routes/<id>/live-positions/` → `transmiapp/services.py` checks short-TTL cache → cache miss triggers a transmiapp call → response normalized into `"live"`/`"unavailable"` → served to client.

### File Organization Patterns

**Configuration Files:** Root-level, following existing convention (`.env`, `pyproject.toml`, `pytest.ini` already there) — `.env.example` added so required variables are documented without exposing values.

**Source Organization:** Per-Django-app, each app owning its full vertical slice (models → services → serializers → views → urls → templates → tests) — no separate top-level `services/` or `api/` package spanning apps.

**Test Organization:** `tests/` subdirectory per app, `test_<module>.py` naming (per Implementation Patterns) — `routes/tests/` and `transmiapp/tests/` are net-new; `crawler/tests/` is retired alongside `crawler/`.

**Asset Organization:** Per-app `static/<app_name>/` for JS/CSS (no-build, per Core Architectural Decisions); `data/` retained at root as one-time/seed input, not runtime-read application data.

### Development Workflow Integration

**Development Server Structure:** `docker-compose up` runs the Django dev server + PostGIS container together; `manage.py runserver` inside the app container, matching Django convention.

**Build Process Structure:** No frontend build step (no-build JS decision). Backend "build" is the Docker image build (`Dockerfile`), which must install GDAL/GEOS system packages for GeoDjango — a real, easy-to-forget requirement worth calling out explicitly here.

**Deployment Structure:** `docker-compose.yml` (or a production variant) defines the container topology; `deploy.sh` on the DigitalOcean VPS pulls the latest built image(s) and restarts the stack. GitHub Actions runs CI (tests + lint) on push but does not trigger deployment — deploy remains a manual, maintainer-run step.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** All technology choices verified compatible — Django 5.2 LTS + DRF 3.17.1 (confirmed Django 5.2-compatible) + PostGIS via `postgis/postgis:17-3.5` + GeoDjango is a standard, well-trodden combination. MapLibre GL JS v6 (WebGL2-only) has one flagged-but-accepted caveat (very old/low-end Android devices), not a conflict with anything else decided. No contradictory technology choices found.

**Pattern Consistency:** Implementation Patterns (Step 5) and Core Architectural Decisions (Step 4) are aligned — e.g., the GeoJSON-for-geometry / plain-DRF-otherwise split matches the DRF decision; the "services.py owns logic" pattern matches the `routes/services/`, `transmiapp/services.py` structure defined in Step 6. No pattern contradicts a Step 4 decision.

**Structure Alignment:** Project Structure (Step 6) correctly instantiates every Step 4/5 decision into concrete files — `routes/services/nearby.py` for the server-side query, `transmiapp/` as its own app for the isolation boundary, `routes/tests/` and `transmiapp/tests/` for the previously-nonexistent test coverage. Boundaries (who owns spatial queries, who owns transmiapp calls) are stated both in prose (Architectural Boundaries) and enforced by file placement.

### Requirements Coverage Validation

**Functional Requirements Coverage (20/20 traced):**

| FR | Architectural Support | Status |
|---|---|---|
| FR1–FR4 (nearby discovery) | `routes/services/nearby.py`, PostGIS `ST_DWithin`, GeoJSON endpoint | ✅ |
| FR5–FR8 (browsing) | Existing `routes/views.py`/templates, retained | ✅ |
| FR9 (live BRT positions) | `transmiapp/` proxy + views | ✅ |
| FR10 (unavailable state) | Explicit `"live"`/`"unavailable"` contract (Implementation Patterns) | ✅ |
| FR11 (recurring GTFS refresh) | `refresh_gtfs` command exists, but **manually triggered, not recurring** | ⚠️ Deviation — see Validation Issues |
| FR12 (alert on pipeline failure) | Sentry captures exceptions during manual runs | ⚠️ Partial — see Validation Issues |
| FR13 (alert on live-tracking failure) | Sentry captures transmiapp proxy exceptions | ✅ (with same silent-failure caveat as FR12) |
| FR14–FR16 (trust/transparency) | `app/templates/layout/base.html` footer | ✅ |
| FR17–FR18 (sharing) | Existing per-route/per-stop URLs (unchanged) | ✅ |
| FR19 (Spanish-only) | `LANGUAGE_CODE='es'` in settings | ✅ |
| FR20 (contrast/keyboard nav) | Noted as a constraint; no concrete component-level decision made here | ⚠️ Deferred — see Gap Analysis |

**Non-Functional Requirements Coverage (13/13 traced):**

| NFR | Architectural Support | Status |
|---|---|---|
| NFR1 (3s page load, weak 3G) | No mechanism decided until this validation pass | ⚠️ → Resolved below (WhiteNoise) |
| NFR2 (<1s nearby-query) | PostGIS spatial index + local-memory cache | ✅ |
| NFR3 (no fixed live-latency target) | Unavailable-state contract, not a latency SLA | ✅ |
| NFR4 (no auth) | Explicitly no auth system | ✅ |
| NFR5 (geolocation never logged/persisted) | Sentry PII scrubbing, logging exclusions (policy-enforced) | ✅ |
| NFR6 (transmiapp creds server-side only) | `transmiapp/services.py` sole owner of the credentials | ✅ |
| NFR7 (HTTPS-only, no committed secrets) | No TLS component existed until this validation pass | ⚠️ → Resolved below (Nginx + Certbot) |
| NFR8 (pipeline failure alert ≤24h) | Weakened by manual trigger — see FR11/FR12 note | ⚠️ Known deviation, PRD update pending |
| NFR9 (live-tracking failure alert, same-day) | Sentry, immediate rather than same-day (better than the bar) | ✅ |
| NFR10 (static/live availability decoupled) | Separate `routes`/`transmiapp` apps, transmiapp owns no persistent models | ✅ |
| NFR11–NFR13 (WCAG AA contrast, fonts, keyboard nav) | Noted in Project Context Analysis; no component-level architecture decision made | ⚠️ Deferred — see Gap Analysis |

### Implementation Readiness Validation

**Decision Completeness:** All critical/important decisions (Step 4) carry a verified version where applicable (Django 5.2, DRF 3.17.1, PostGIS `17-3.5`, MapLibre 6.x). Four gaps surfaced only during this validation pass (TLS, tile source, static-asset serving, data migration) — now resolved, see below.

**Structure Completeness:** Step 6's tree is concrete (real filenames, not placeholders) and every FR category maps to a specific file/directory. Two additions needed post-validation: a reverse-proxy/TLS layer and a tile-source config value — folded into the resolutions below.

**Pattern Completeness:** Naming, structure, format, communication, and process patterns (Step 5) cover every conflict point identified for this stack. No additional pattern gaps found during validation.

### Gap Analysis Results

**Critical Gaps (block a real production deploy):**
- **NFR7 — no TLS/reverse-proxy component was defined.** The Docker Compose topology (Step 6) had only the app and PostGIS containers.

**Important Gaps:**
- **Map tile source unspecified** — MapLibre GL JS was chosen (Step 3) but not what feeds it tiles; directly relevant to the brief's named "running costs aren't bounded yet" risk.
- **No SQLite → PostGIS data migration strategy** — "swap the DB engine" was implied but not a real plan for the existing scraped data.
- **NFR1 had no concrete mechanism** — "lean payloads, minimal JS" was a PRD-level aspiration, not an architectural decision with a specific technique.

**Minor / Deferred Gaps:**
- **FR20/NFR11–13 (accessibility)** — correctly a UX-design-level concern per the Implementation Readiness Report's own finding that no UX document exists yet. Not resolved here; flagged as a dependency for `bmad-create-ux-design`, not a gap in this document's scope.
- **FR12/NFR8 partial coverage** — a logic error that succeeds without raising an exception (e.g., a GTFS parse that silently imports zero routes) would not trigger a Sentry alert. Not resolved here — noted as a known limitation of the manual-trigger + exception-only monitoring approach, consistent with the already-flagged FR11/NFR8 deviation.

### Validation Issues Addressed

1. **TLS/HTTPS termination (NFR7):** Resolved — **Nginx + Certbot**, already running on the target DigitalOcean VPS outside the `docker-compose.yml` app stack (existing server-level infrastructure, not a new container). Nginx reverse-proxies to the Django/Gunicorn container; Certbot manages Let's Encrypt renewal. `deploy.sh` and `Dockerfile`/`docker-compose.yml` in Project Structure (Step 6) are understood to sit behind this existing Nginx config, not replace it.
2. **Map tile source:** Resolved — **OpenFreeMap**. No API key, no usage cap, free — matches the non-commercial/no-cost-ceiling stance most directly of the options considered. Configured as a style URL in `static/js/map-init.js`.
3. **Static asset serving / NFR1 mechanism:** Resolved — **WhiteNoise** middleware in `app/settings.py`, giving gzip/Brotli compression and far-future cache headers on Django's static files with zero added infrastructure (no CDN, no extra container).
4. **SQLite → PostGIS data migration:** Resolved — **no in-place migration**. Since the GTFS static feed supersedes the scraped data as source of truth (per Core Architectural Decisions), the new PostGIS database is populated fresh via `refresh_gtfs` rather than dumped/converted from `db.sqlite3`. The legacy SQLite file is archived (kept for reference/rollback), not upgraded in place.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified (including TLS and tile source, resolved in this step)
- [x] Integration patterns defined
- [x] Performance considerations addressed (NFR1 mechanism resolved in this step)

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION, with two carried-forward action items outside this document's scope (see below).

**Confidence Level:** High — every FR and NFR has been explicitly traced to an architectural decision or a deliberately-scoped deferral; all four gaps found during validation were resolved with concrete decisions, not left open.

**Key Strengths:**
- The client/server-vs-privacy tension the PRD explicitly flagged as unresolved was resolved with a concrete, code-enforceable mitigation (Sentry PII scrubbing + logging exclusions), not left vague.
- The live-tracking "unavailable" contract (FR10) is specified precisely enough that two different implementers would build the same thing.
- Cost constraints (hosting, tiles, cache, monitoring) were resolved with genuinely free/zero-marginal-cost choices throughout, consistent with the brief's near-zero-cost ceiling.
- Solo-maintainer operability was treated as a first-class architectural constraint (manual GTFS trigger, manual CD, Sentry-over-cron-email), not bolted on.

**Areas for Future Enhancement:**
- Redis/shared cache backend if the app ever outgrows a single VPS process.
- Automated GTFS refresh scheduling, if manual sync becomes a maintenance burden (ties to the pending PRD update).
- A UX design document to give FR20/NFR11–13 (accessibility) and the map/comparison-view interaction patterns real component-level specification.

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented in this file.
- Use implementation patterns (Step 5) consistently — especially the GeoJSON/plain-DRF split and the `"live"`/`"unavailable"` contract, which are easy to implement subtly wrong.
- Respect project structure and boundaries (Step 6) — spatial queries only in `routes/services/`, transmiapp calls only in `transmiapp/services.py`.
- Refer to this document for all architectural questions; update it deliberately (dated note) if an exception becomes necessary rather than silently drifting from it.

**Outstanding Action Items (not blocking, but not yet done):**
1. Update PRD FR11/NFR8 to reflect the manual (not scheduled/recurring) GTFS refresh trigger model — via `bmad-edit-prd` or `bmad-correct-course`.
2. Run `bmad-create-ux-design` before or alongside epic creation — FR20/NFR11–13 and the nearby-comparison interaction patterns need real UX-level specification this document deliberately did not attempt.

**First Implementation Priority:**
Django 4.2.4 → 5.2 upgrade + SQLite → PostgreSQL/PostGIS foundation (fresh-populated via `refresh_gtfs`, per the resolved migration strategy above) — everything else in this document depends on this being in place first.