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
- **The existing Django migration history (`routes/migrations/0001`–`0007`) should be deleted, not evolved**, once the models below land. There is no production data to preserve — the SQLite dev database is archived, not upgraded in place (per the SQLite → PostGIS resolution below), and the model changes here (`BusStation` → `BusStop` rename, `route_type` split, new fields) are extensive enough that writing incremental migrations against the old schema would just be churn against a schema being replaced wholesale. Regenerate a single fresh initial migration (`0001_initial.py`) against the new models as part of the Django 5.2/PostGIS foundation story (see Decision Impact Analysis, Implementation Sequence step 1). This is safe from Django's migration-table name collision (a fresh `0001_initial` silently treated as "already applied" if a DB already has a `routes.0001_initial` row) **only because the PostGIS database is provisioned fresh** (new Docker container, no reused database file) — this is not a general-purpose safeguard, and would need revisiting if this project ever migrates onto an already-provisioned Postgres instance instead of a brand-new one.
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
- **GTFS refresh strategy (FR11):** **Full replace inside a single DB transaction** per sync — each run rebuilds routes/stops/schedules from scratch and atomically swaps in the new dataset, rather than diffing/upserting. Avoids stale-record edge cases from partial updates. ⚠️ **Refined 2026-08-17** — see Data Model Amendment below: "full replace" means matched-and-replaced by GTFS natural key (`gtfs_route_id`/`gtfs_stop_id`), not truncate-and-reinsert by Django PK, so `is_active` and stable per-route/per-stop URLs (FR17–18) survive a refresh.
- **GTFS refresh trigger model:** **Manually invoked** (a Django management command run by the maintainer), **not a scheduled/cron job**. ⚠️ **This deviates from FR11 as currently written** ("recurring schedule... without manual intervention") and from NFR8 ("alert within 24 hours of a missed or failed scheduled run" — there is no "scheduled run" to miss if it's manual). This was an explicit, informed decision (not an oversight): confirmed with the user, who will update the PRD (FR11/NFR8) to match after this architecture document is complete, via `bmad-edit-prd` or `bmad-correct-course`. **Action item, not yet done.**
- **Caching backend:** Django's local-memory cache (in-process, no separate cache service/container). Chosen for zero added infrastructure at friends-and-family scale; revisit only if the app grows beyond a single worker process.

### Data Model Amendment (2026-08-17)

Pre-epics review surfaced that `routes/models.py` (`Route.route_type`, `BusStation`) predates this architecture document and was never re-validated against a current TM/SITP source. Live research against the official GTFS static feed (ArcGIS Hub, latest `2025-10-28`), the official GeoJSON open-data dumps already in `data/`, and TransMilenio's own `buscador-rutas.transmilenio.gov.co` tool (its backend, `ms-transmiapp-rm2xahnybq-uk.a.run.app`, was queried directly — unauthenticated, no spoofed headers, distinct from but same-family as the unofficial live-position `transmiapp` host) produced three model changes, decided collaboratively with Vera:

**1. `BusStation` → `BusStop`, unified with a `stop_type` discriminator.**
The two official stop datasets describe genuinely different infrastructure sharing no natural key beyond location: trunk **"Estación"** (149 rows — `troncal_estacion`, `numero_vagones_estacion`, `numero_accesos_estacion`, `biciestacion_estacion`, `tipo_estacion`) vs. zonal **"Paradero"** (7,618 rows — `cenefa`, `zona_sitp`, `via`, `direccion_bandera`, `localidad`, `consola`, `panel`, `audio`). The existing `BusStation.cenefa`/`.audio` fields are confirmed paradero-only (`routes/management/commands/load_bus_stations.py` populates them exclusively from `Paraderos_Zonales_del_SITP.geojson`) — the model has been zonal-shaped under a trunk-sounding name, with no loader ever written for the trunk-specific fields.
- Rename to `BusStop` (matches GTFS's single `stops.txt` convention).
- Add `stop_type` (`estacion_troncal` / `paradero_zonal`).
- Keep one table (not two related models) — type-specific fields (`numero_vagones`, `biciestacion` for stations; `cenefa`, `zona_sitp`, `audio` for paraderos) stay nullable, populated per `stop_type`. Chosen over a split-model approach to avoid join overhead in the FR1–FR4 nearby-query spatial service, which is latency-critical (NFR2, <1s).
- `location` (PointField) as already decided in Core Architectural Decisions supersedes both `latitude`/`longitude` DecimalFields, for both stop types.
- `gtfs_stop_id` (unique, sourced from the GTFS feed's `stops.txt` `stop_id` column): the natural key `gtfs_refresh.py` upserts on, so a `BusStop` row's identity — and any shared URL to it — survives a refresh. **Do not assume `cenefa` or `transmilenio_id` equal the feed's `stop_id`** — both are pre-GTFS identifiers (TM website scrape, SITP paraderos open-data export respectively) that predate this project's move to GTFS as system of record; the actual mapping needs verifying against a real `stops.txt` pull (same open item as `service_tier` below), not assumed 1:1.

**2. `Route.route_type` splits into `route_mode` + `service_tier`.**
The live API's actual route object (`GET /api/v1/rutas/{id}/{code}/`) returns `"tipo": "TransMiZonal"` or `"tipo": "TransMilenio"` — a 2-value mode split, not the current model's 5 values. The Troncal/Alimentador/Urbano/Complementario/Especial vocabulary is real and current (confirmed against `bogota.gov.co`, 2026) but is a finer TM-internal service-tier concept the live API doesn't expose directly on the route object — it needs re-sourcing from the GTFS feed's `route_desc`/naming convention, **not yet verified against an actual downloaded `routes.txt`** (flagged as an open verification item below).
- `route_mode`: `transmilenio` / `transmizonal` today. This is the GTFS-ready seam: Regiotram de Occidente (rail, under construction, ~2027 target, confirmed **not** fare-integrated with SITP — separate payment method per EFR, Feb 2024) and Metro de Bogotá Línea 1 (rail) both stay explicitly **out of scope** for this build, but would slot in as new `route_mode` values later without a structural rework, consistent with GTFS's own mode taxonomy (bus/rail/subway as sibling values). This is a deliberate documented deferral, not a silent gap.
- `service_tier`: revalidated `troncal`/`alimentador`/`urbano`/`complementario`/`especial` — kept because it's load-bearing: the PRD's MVP nearby-query scoping ("index and query only trunk/BRT stops and routes") and FR9 (live tracking is trunk-only) both depend on filtering by tier.
- Trunk routes additionally carry a `troncal` (corridor) grouping absent from the model today — corridor name (e.g. "Calle 26"), zone letter, corridor color, PDF diagram link. Deferred: not required for MVP FRs, noted here so it isn't rediscovered as a surprise later.
- `gtfs_route_id` (unique, sourced from `routes.txt` `route_id`): same rationale as `BusStop.gtfs_stop_id` above — the natural key `gtfs_refresh.py` upserts on. **Do not assume `code` (e.g. `"19-1"`, `"B309"`) equals the feed's `route_id`** — `code` is the rider-facing label (kept for URLs/search/FR6), `route_id` is the feed's internal identifier; the mapping between them needs verifying against a real `routes.txt` pull, not assumed.
- `is_active` (boolean, default `true`): the live API's search endpoint filters on an `activa` flag; the current model has no equivalent and would silently lose rows on route restructuring. Needed for the PRD's "survive a real TransMilenio route restructuring" success criterion and for keeping shared links (FR17–18) resolvable for retired routes rather than 404ing. Set by `gtfs_refresh.py`: rows matched by `gtfs_route_id` in the new feed stay `is_active=True`; rows present before the refresh but absent from the new feed are set `is_active=False`, never deleted (see refined GTFS refresh strategy in Data Architecture above).
- `schedule` becomes structured, replacing the free-text `CharField` the old scraper never reliably parsed (`crawler/utlis.py`'s `parse_schedule` returns a hardcoded stub today). The live API returns exactly this shape: a list of `{tipoDia, inicio, fin}` entries (e.g. `L-S 4:00 AM–9:00 PM`, `D-F 5:00 AM–10:00 PM`). **Correction:** the previous draft of this note treated the live API's `tipoDia` (`L-S`/`D-F`) as equivalent to `tipo_operacion` in `data/Rutas_Zonales_SITP.geojson` (e.g. `"DOM-FEST"`) — that was an unverified assumption, not a confirmed match; they may be different vocabularies from different systems (live route-finder API vs. the zonal-routes open-data export) describing overlapping but not necessarily identical day-type concepts. **Open items, all blocking before `RouteSchedule`/`service_tier` are implemented, not just observed:** (a) only `L-S`/`D-F` seen in the two live-API samples pulled — full `tipoDia` value set unconfirmed; (b) how GTFS `calendar.txt` (weekly service pattern) and `calendar_dates.txt` (dated exceptions, including holidays) resolve precedence against each other and against whatever day-type field is chosen; (c) explicit handling for an unrecognized day-type value during ingestion — reject the row, or fail the whole refresh — rather than silently misclassifying it into the nearest known bucket.

**3. Ciclovía: advisory flag, not diversion geometry.**
Confirmed (news coverage, 2026) that Ciclovía forces a **recurring weekly** diversion (every Sunday/holiday, 7am–2pm) for zonal and "dual" routes crossing its corridors, **plus** separate ad-hoc diversions for one-off events (marches, marathons) layered on top with no confirmed structured open-data source for either the standing weekly diversions or the ad-hoc ones. Given that, the route detail panel's Ciclovía note (already assumed by `ux-design-specification.md`, lines ~209/296/380/385) is specified as:
- A boolean/derived flag (`ciclovia_affected`, or derived from `service_tier` + known Ciclovía-corridor proximity) — **not** an attempt to store exact diverted paths, since no data source for those was found.
- Rendered as a static, honest, plain-language note ("esta ruta puede tener desvíos los domingos y festivos, 7am–2pm") — mirrors the FR10 `"live"`/`"unavailable"` precedent: explicit about what's known and unknown, never inventing precision the data doesn't support.
- Explicit unavailable/not-applicable case: routes with no Ciclovía exposure show no note at all, rather than an empty or null field.
- **Lifecycle (decided 2026-08-17, closing an open gap this amendment left when first written):** `ciclovia_affected` is **derived, not manually set** — recomputed by `gtfs_refresh.py` on every sync from a small, version-controlled corridor/service_tier rule (e.g. a maintained list of route codes or corridors known to cross Ciclovía streets), not edited directly on `Route` rows. This is a deliberate choice over a manually-maintained override: a manual flag would either get silently wiped by every full-replace-style refresh (nobody re-enters it) or silently go stale if refresh logic special-cased preserving it (nobody notices when the underlying corridor list changes). A rule recomputed fresh each sync can't drift out of sync with itself — it's only ever as current as the maintained rule list, which is a known, visible maintenance surface (a file in the repo) rather than a hidden one (data silently surviving or not surviving refreshes).

**4. UUID primary keys across all models.**
Decided 2026-08-17: `BusStop`, `Route`, `RouteStations`, and `RouteSchedule` all get an explicit `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`, replacing Django's default auto-increment integer PK. Raised initially as an enumeration-hardening suggestion and, on its own, not a strong fit for this project — there's no auth and no sensitive data (NFR4), so sequential IDs alone aren't a real exposure. The decision stands on different grounds: URL patterns are already being reworked in this same amendment (`bus_station_detail` → `bus_stop_detail`, `bus-stations/` → `bus-stops/`, per the ripple note below) — this is the point in the project's life where public identifiers can change cheaply, and the point where they get harder to change is once real links have been shared (FR17–18). Choosing opaque, stable-at-creation identifiers now avoids a second URL-scheme break later. Ripple: URL patterns move from `<int:pk>` to `<uuid:pk>` throughout `routes/urls.py`/`routes/api_urls.py`; `gtfs_route_id`/`gtfs_stop_id` (item 1/2 above) remain the *refresh-matching* key, distinct in purpose from the UUID *public-identity* key — a refresh upserts by `gtfs_route_id` and the row keeps its original UUID, so shared links keep resolving across syncs.

**Verification still needed before implementation** (not blocking this amendment, but blocking the stories that implement `service_tier`/`schedule`/the natural-key fields): pull an actual GTFS `routes.txt`/`stops.txt`/`calendar.txt`/`calendar_dates.txt` from the `2025-10-28` static feed to confirm `service_tier` sourcing, the `gtfs_route_id`/`gtfs_stop_id` mapping against existing `code`/`cenefa`/`transmilenio_id`, and the full day-type value set plus calendar-exception precedence. The live JSON API sampled above is a useful cross-check but is not itself the system of record — GTFS remains it, per Core Architectural Decisions.

#### Terminology & Sources

Spanish-language TM/SITP domain terms used above and elsewhere in this document, for readers (human or AI agent) implementing against them without independently re-deriving each one:

| Term | Meaning | Source |
|---|---|---|
| **SITP** | Sistema Integrado de Transporte Público — Bogotá's integrated system name; TransMilenio (trunk/BRT) is one component of it, zonal buses are another | [transmilenio.gov.co — Servicios del SITP](https://www.transmilenio.gov.co/publicaciones/146270/servicios_del_sitp/) |
| **Troncal** | Trunk/BRT service — articulated buses on exclusive busway corridors connecting stations/portals; also the name of the corridor grouping itself (e.g. "Calle 26") | [transmilenio.gov.co — tipos de rutas](https://bogota.gov.co/mi-ciudad/movilidad/tipos-de-buses-de-transmilenio-bogota-troncal-zonal-y-mas-datos); live API `troncal` object, sampled 2026-08-17 |
| **Zonal** | Non-trunk service operating on regular streets (covers Alimentador/Urbano/Complementario/Especial); `"tipo": "TransMiZonal"` in the live route API | Live API sample, 2026-08-17 |
| **Alimentador** (feeder) | Connects neighborhoods to trunk portals/stations under one integrated fare | [transmilenio.gov.co — ABCÉ del servicio de alimentación](https://www.transmilenio.gov.co/comunicaciones/noticias-de-transmilenio/comunicados-oficiales/abce-del-servicio-de-alimentacion-de-transmilenio) |
| **Urbano** | Zonal service crossing multiple zones on main roads, identified by blue buses | bogota.gov.co, as above |
| **Complementario** | Zonal service operating within a single zone only (contrast with Urbano) | bogota.gov.co, as above |
| **Especial** | Special-purpose zonal service | bogota.gov.co, as above |
| **Estación** | Trunk station — the larger platform infrastructure (149 in the official dataset), with attributes like platform count and bike-parking capacity that don't apply to zonal stops | `data/Estaciones_Troncales_de_TRANSMILENIO.geojson` (official, via ArcGIS Hub) |
| **Paradero** | Zonal stop — a simple curbside stop (7,618 in the official dataset), identified by `cenefa` | `data/Paraderos_Zonales_del_SITP.geojson` (official, via ArcGIS Hub) |
| **Cenefa** | SITP's official alphanumeric stop code for a paradero (e.g. `"001A00"`) — the natural key `load_bus_stations.py` already matches on | Same GeoJSON source |
| **Ciclovía** | Bogotá's weekly car-free-streets program (Sundays/holidays, 7am–2pm) that forces zonal/dual route diversions; separate from one-off event diversions (marches, marathons) | [bogota.gov.co — horarios y rutas de la Ciclovía](https://bogota.gov.co/mi-ciudad/cultura-recreacion-y-deporte/horarios-y-rutas-de-la-ciclovia-bogotana-los-domingos-y-festivos); news coverage, 2026 |

#### Proposed Data Models (concrete)

Field-level sketch for the implementation story — names/types illustrative (Django/GeoDjango conventions per Implementation Patterns), not final code:

```python
import uuid


class BusStop(models.Model):  # renamed from BusStation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STOP_TYPE_TRUNK = 'estacion_troncal'
    STOP_TYPE_ZONAL = 'paradero_zonal'
    STOP_TYPES = (
        (STOP_TYPE_TRUNK, 'Estación troncal'),
        (STOP_TYPE_ZONAL, 'Paradero zonal'),
    )

    name = models.CharField(max_length=150)
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    gtfs_stop_id = models.CharField(max_length=50, unique=True)  # stops.txt stop_id — refresh natural key
    location = models.PointField()                    # replaces latitude/longitude DecimalFields
    address = models.CharField(max_length=255, default='')
    link = models.URLField(default='')

    # Zonal-only (paradero) — null when stop_type=estacion_troncal
    cenefa = models.CharField(max_length=50, null=True, unique=True)
    zona_sitp = models.CharField(max_length=10, blank=True)
    audio = models.CharField(max_length=255, blank=True)

    # Trunk-only (estación) — null when stop_type=paradero_zonal
    transmilenio_id = models.IntegerField(null=True, unique=True)
    numero_vagones = models.PositiveSmallIntegerField(null=True)
    numero_accesos = models.PositiveSmallIntegerField(null=True)
    biciestacion = models.BooleanField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # zonal rows carry a cenefa and no trunk-only fields; trunk rows carry
            # transmilenio_id and no zonal-only fields — gtfs_refresh.py must reject
            # (not partially load) any row that violates this per stop_type
            models.CheckConstraint(
                check=(
                    models.Q(stop_type=STOP_TYPE_ZONAL, cenefa__isnull=False, transmilenio_id__isnull=True)
                    | models.Q(stop_type=STOP_TYPE_TRUNK, transmilenio_id__isnull=False, cenefa__isnull=True)
                ),
                name='busstop_type_specific_fields_consistent',
            ),
        ]


class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROUTE_MODE_TRUNK = 'transmilenio'
    ROUTE_MODE_ZONAL = 'transmizonal'
    ROUTE_MODES = (
        (ROUTE_MODE_TRUNK, 'TransMilenio'),
        (ROUTE_MODE_ZONAL, 'TransMiZonal'),
        # future: 'metro', 'regiotram' — deliberately not added yet, see amendment above
    )
    SERVICE_TIER_TRUNK = 'troncal'
    SERVICE_TIER_FEEDER = 'alimentador'
    SERVICE_TIER_URBAN = 'urbano'
    SERVICE_TIER_COMPLEMENTARY = 'complementario'
    SERVICE_TIER_SPECIAL = 'especial'
    SERVICE_TIERS = (
        (SERVICE_TIER_TRUNK, 'Troncal'),
        (SERVICE_TIER_FEEDER, 'Alimentador'),
        (SERVICE_TIER_URBAN, 'Urbano'),
        (SERVICE_TIER_COMPLEMENTARY, 'Complementario'),
        (SERVICE_TIER_SPECIAL, 'Especial'),
    )  # ⚠️ pending verification against actual GTFS routes.txt — see "Verification still needed" above

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    gtfs_route_id = models.CharField(max_length=50, unique=True)  # routes.txt route_id — refresh natural key
    route_mode = models.CharField(max_length=20, choices=ROUTE_MODES)
    service_tier = models.CharField(max_length=20, choices=SERVICE_TIERS)
    color = models.CharField(max_length=50, default='')
    path = models.MultiLineStringField(null=True)      # GTFS shape geometry
    is_active = models.BooleanField(default=True)       # survives route restructuring; keeps FR17–18 links resolvable
    ciclovia_affected = models.BooleanField(default=False)  # advisory only — see amendment above, no diversion geometry

    map_link = models.URLField(default='')
    details_link = models.URLField(default='')
    publication_date = models.DateTimeField(null=True)
    last_update = models.DateTimeField(null=True)        # maps to upstream `informacion.fechaActualizacion`

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        unique_together = ('code', 'name')


class RouteSchedule(models.Model):                       # NEW — replaces Route.schedule free-text CharField
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    DAY_TYPE_WEEKDAY_SATURDAY = 'L-S'
    DAY_TYPE_SUNDAY_HOLIDAY = 'D-F'
    DAY_TYPES = (
        (DAY_TYPE_WEEKDAY_SATURDAY, 'Lunes a sábado'),
        (DAY_TYPE_SUNDAY_HOLIDAY, 'Domingos y festivos'),
        # ⚠️ PROVISIONAL, not frozen — only these two observed in live-API samples.
        # Do not assume this equals GTFS calendar.txt/calendar_dates.txt's own
        # service-day model; see "Verification still needed" above before treating
        # this as final. Ingestion must reject an unrecognized day-type value
        # rather than guess the nearest bucket.
    )

    route = models.ForeignKey('routes.Route', related_name='schedules', on_delete=models.CASCADE)
    day_type = models.CharField(max_length=10, choices=DAY_TYPES)
    # DurationField (seconds-since-midnight), not TimeField: GTFS stop_times.txt/
    # frequencies.txt times can exceed 24:00:00 for a trip that starts before and
    # continues past midnight of the same service day (e.g. 25:30:00) — Python's
    # datetime.time (what TimeField stores) cannot represent that, so TimeField
    # would silently corrupt or reject valid late-night schedules. Sourced from
    # stop_times.txt/frequencies.txt; calendar.txt/calendar_dates.txt determine
    # which dates a service_id applies to, not these time values.
    start_time = models.DurationField()
    end_time = models.DurationField()


# RouteStations: otherwise unchanged in shape, FK target renamed BusStation → BusStop
class RouteStations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ...  # direction, position, route FK, bus_stop FK (renamed from bus_station)
```

`RouteStations.bus_station` FK renames to `bus_stop` for consistency — a ripple from the `BusStop` rename that touches `routes/api_urls.py` (`bus-stations/` → likely `bus-stops/`), `routes/urls.py` (`bus_station_detail` → `bus_stop_detail`), and `routes/templates/routes/busstation_*.html` → `bus_stop_*.html`. Not attempting a full URL/template rename plan here — flagged so the implementing story scopes it rather than discovering it mid-implementation.

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
- Django default conventions throughout — no manual overrides. Table names auto-derive as `<app_label>_<modelname>` lowercase (e.g. `routes_route`, `routes_busstop`), matching the existing schema convention (superseded name: `routes_busstation`, pre-2026-08-17 amendment).
- Columns: snake_case, Django default (e.g. `route_mode`, `service_tier`, `transmilenio_id`) — `route_type` is superseded, see Data Model Amendment (2026-08-17).
- Foreign keys: Django default `<field_name>_id` (e.g. `route_id`, `bus_stop_id`), as already used in `RouteStations` (renamed from `bus_station_id`) — values are UUIDs, not sequential integers, per the UUID primary key decision (item 4, Data Model Amendment, 2026-08-17).
- New PostGIS geometry fields: name by what they represent, not by type — `location` (`PointField`) on `BusStop`, `path` (`MultiLineStringField`) on `Route`, not `geom` or `the_geog`.
- Spatial indexes: let GeoDjango auto-create the GiST index (default behavior for geometry fields) — no manual index naming needed.

**API Naming:**
- URL segments: kebab-case for multi-word paths, plural nouns for collections — continues the existing `bus-stations/` precedent. New endpoints: `stops/nearby/`, `routes/<id>/live-positions/`.
- Django URL pattern `name=`: snake_case (`bus_stop_detail`, renamed from `bus_station_detail`; `route_buses`), matching existing `urls.py`/`api_urls.py`.
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
- `GET /api/routes/3fa85f64-5717-4562-b3fc-2c963f66afa6/live-positions/` (UUID `pk`, per Data Model Amendment item 4) → `{"buses": [{"id": "...", "status": "live", "location": {...}}, {"id": "...", "status": "unavailable"}]}`.

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
│   ├── models.py                  # UPDATED — BusStation renamed BusStop (+ stop_type), Route.route_type split into route_mode/service_tier, RouteSchedule (new), location/path as PostGIS geometry — see Data Model Amendment (2026-08-17)
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
│   │       ├── load_bus_stations.py  # UPDATED — needs stop_type-aware loading for both estación (trunk) and paradero (zonal) sources, not zonal-only as today
│   │       └── refresh_gtfs.py       # NEW — manually-invoked management command (FR11)
│   ├── migrations/                # 0001–0007 DELETED (no production data to preserve); fresh 0001_initial.py generated against the amended models
│   ├── templates/routes/          # existing: home, route_detail, busstation_list, busstation_detail — RENAMED to bus_stop_list/bus_stop_detail alongside the model rename
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
- `routes` app owns `Route`, `RouteSchedule`, `RouteStations`, `BusStop` (renamed from `BusStation`) models and their PostGIS geometry — the single source of truth for static data.
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