---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/relaunch-prd.md
  - _bmad-output/planning-artifacts/relaunch-architecture.md
  - _bmad-output/planning-artifacts/relaunch-ux-design-specification.md
---

# public_transport - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for public_transport, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Nearby Route & Stop Discovery (core differentiator)**

- FR1: Rider can view all trunk (BRT/troncal) routes and stops near their current location on a single map, without selecting a specific route first. (Scoped to trunk/BRT for MVP per the PRD's Risk Mitigation Strategy simplification; zonal is Phase 2.)
- FR2: Rider can view all trunk (BRT/troncal) routes and stops near a location they choose (not just live GPS), to plan a trip before leaving home. (Same trunk/BRT MVP scoping as FR1.)
- FR3: Rider can compare live bus proximity across multiple nearby trunk stops simultaneously, to decide which stop to walk to.
- FR4: Rider can identify which trunk routes are shared across multiple nearby stops, to spot redundant or overlapping options.

**Route & Stop Browsing**

- FR5: Rider can browse the full list of routes.
- FR6: Rider can search for a specific route by name or number.
- FR7: Rider can view a route's full path and ordered stop sequence on a map.
- FR8: Rider can view a stop's details, including which routes serve it.

**Live Bus Tracking**

- FR9: Rider can see live positions of buses on trunk (BRT) routes overlaid on the map.
- FR10: Rider can distinguish an explicit "position unavailable" state from a normal live position, rather than seeing stale or wrong data when the live-tracking source is down.

**Data Currency (system capability)**

- FR11: System can refresh static route/stop/schedule data from the official GTFS source, triggered by the maintainer, and rider can see when that data was last successfully refreshed, so staleness is disclosed rather than presented as confidently current. (Manual, maintainer-triggered refresh — not an automatic recurring schedule; a deliberate solo-maintainer-operability decision confirmed in `relaunch-architecture.md`. No hard freshness SLA — the last-refreshed disclosure lets riders judge staleness themselves; refresh cadence is informal maintainer guidance, not system-enforced.)
- FR12: System can alert the maintainer when the GTFS refresh pipeline fails.
- FR13: System can alert the maintainer when the live-tracking source becomes unavailable or its response format changes.

**Trust & Transparency**

- FR14: Rider can see a clear, always-visible statement that the app is unaffiliated with TransMilenio/SITP.
- FR15: Rider can see attribution/credit for the official open-data source used.
- FR16: Rider can see a short, plain-language explanation of how their location is used and that it isn't stored or shared.

**Sharing**

- FR17: Rider can share a direct link to a specific route or stop with another person.
- FR18: A person opening a shared link sees that specific route/stop view directly, without additional navigation.

**Localization & Accessibility**

- FR19: Rider can use the entire app in Spanish, with no other language required.
- FR20: Rider can read all content with sufficient color contrast and readable font sizes, and navigate via keyboard where feasible.

### NonFunctional Requirements

**Performance**

- NFR1: Static route/stop/schedule pages load and render within 3 seconds on a mid-range Android device over a weak/3G-equivalent connection.
- NFR2: The nearby-routes/stops comparison query (FR1–FR4) returns results from the local static dataset in under 1 second.
- NFR3: No fixed latency target for live bus position updates (depends on an upstream third-party API outside project control) — staleness/unavailability must be surfaced explicitly (FR10) rather than hidden.

**Security**

- NFR4: No user accounts, authentication, or payment data in v1.
- NFR5: Geolocation coordinates are never logged or persisted server-side, regardless of client-side or server-side query computation.
- NFR6: Credentials/headers used to call the unofficial `transmiapp` live-tracking endpoint are kept server-side only, never exposed in client-side JS or committed to public repo history.
- NFR7: HTTPS-only in production; no secrets committed to version control.

**Reliability & Monitoring**

- NFR8: GTFS refresh pipeline failures are surfaced to the maintainer immediately (via Sentry) during a manually-triggered run. (No "scheduled run" to miss — the maintainer already knows a sync happened because they triggered it, so failure detection is immediate.)
- NFR9: Live-tracking source failures or response-format changes are detected and alert the maintainer within the same day, not discovered via silent user complaints.
- NFR10: Static route/stop data availability is fully decoupled from live-tracking availability — a live-tracking outage must never take down route/stop browsing.

**Accessibility**

- NFR11: Text meets WCAG 2.1 AA color contrast minimums (4.5:1 for normal text).
- NFR12: Font sizes are readable by default — no reliance on pinch-zoom for core content.
- NFR13: Core navigation (route search, stop details) is operable via keyboard, not just touch/mouse.

### Additional Requirements

Technical requirements from `relaunch-architecture.md` that affect epic/story creation:

**Foundation (blocks everything else — Epic 1 Story 1 candidate)**

- No starter template applies (brownfield rebuild) — the existing Django app is the starter. The Django 4.2.4 → 5.2 LTS upgrade + SQLite → PostgreSQL/PostGIS migration must be the first implementation story; every other component depends on it.
- Geospatial database: PostgreSQL + PostGIS via GeoDjango, Docker image `postgis/postgis:17-3.5`.
- Map rendering library: MapLibre GL JS v6.x (WebGL2-required), replacing Mapbox GL, loaded no-build via `<script>` tag.
- Deployment: Docker containers on the existing, already-owned DigitalOcean Linux VPS (self-managed, not a PaaS).
- Local development: Docker Compose (Django + PostGIS, mirrors prod container topology).
- No in-place SQLite → PostGIS data migration — the new PostGIS database is populated fresh via `refresh_gtfs`; legacy SQLite archived, not upgraded in place.
- Existing Django migration history (`routes/migrations/0001`–`0007`) deleted; a single fresh `0001_initial.py` generated against the new models.

**Data model rework**

- `BusStation` renamed to `BusStop`, unified with a `stop_type` discriminator (`estacion_troncal` / `paradero_zonal`); type-specific fields stay nullable per type with a DB check constraint enforcing consistency.
- `location` (PostGIS `PointField`) replaces `latitude`/`longitude` `DecimalField`s.
- `gtfs_stop_id` (unique) is the refresh natural key — `cenefa`/`transmilenio_id` must NOT be assumed to equal it without verification against a real `stops.txt` pull.
- `Route.route_type` splits into `route_mode` (`transmilenio`/`transmizonal` — GTFS-ready seam for future rail modes, deliberately deferred) and `service_tier` (`troncal`/`alimentador`/`urbano`/`complementario`/`especial` — pending verification against actual GTFS `routes.txt`).
- New `Corridor` model (trunk-route corridor grouping: name, zone letter, color, PDF link) — promoted to a real model because `relaunch-ux-design-specification.md`'s Color System makes per-corridor trunk color a foundational Phase-1 requirement.
- `gtfs_route_id` (unique) is the refresh natural key for `Route` — `code` (rider-facing label) must NOT be assumed to equal it without verification against a real `routes.txt` pull.
- `is_active` boolean (default `true`) on `Route` — refresh sets `False` (never deletes) for routes absent from the new feed, keeping FR17–18 shared links resolvable after restructuring.
- New `RouteSchedule` model replaces the free-text `schedule` `CharField` — `day_type` choices (`L-S`/`D-F`, provisional/unconfirmed against full GTFS calendar semantics), `start_time`/`end_time` as `DurationField` (not `TimeField`, to allow times past 24:00:00). Blocking open items before implementation: full `tipoDia` value set unconfirmed; `calendar.txt`/`calendar_dates.txt` precedence unresolved; explicit reject-not-guess handling required for unrecognized day-type values.
- `ciclovia_affected` boolean on `Route` — advisory-only flag (no diversion geometry), derived/recomputed by `gtfs_refresh.py` on every sync from a version-controlled corridor/service_tier rule, never manually edited.
- UUID primary keys (`id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`) across `BusStop`, `Route`, `RouteStations`, `RouteSchedule`, `Corridor` — chosen because URL patterns are already being reworked in this same rebuild (cheaper to change public identifiers now than after links are shared).
- `RouteStations.bus_station` FK renamed to `bus_stop`; ripples through `routes/api_urls.py` (`bus-stations/` → `bus-stops/`), `routes/urls.py` (`bus_station_detail` → `bus_stop_detail`), and templates (`busstation_*.html` → `bus_stop_*.html`).
- Verification blocking item: pull actual GTFS `routes.txt`/`stops.txt`/`calendar.txt`/`calendar_dates.txt` from the `2025-10-28` static feed to confirm `service_tier` sourcing, natural-key mappings, and the full day-type value set before implementing `service_tier`/`schedule`/natural-key fields.

**GTFS refresh pipeline**

- Full replace inside a single DB transaction per sync, matched-and-replaced by GTFS natural key (`gtfs_route_id`/`gtfs_stop_id`), not truncate-and-reinsert by Django PK — preserves `is_active` semantics and stable URLs across refreshes.
- Trigger model: manually invoked Django management command (`refresh_gtfs`) run by the maintainer — not a scheduled/cron job (deliberate decision, ties to FR11/NFR8 as amended).

**Nearby-query & live-tracking**

- Nearby-query computation (FR1–FR4): server-side, PostGIS `ST_DWithin`. Coordinates sent from client but never logged or persisted — a policy-level guarantee enforced in code (view/serializer excludes coordinates from Django request logging and Sentry's captured request data), not by architecture alone.
- Caching backend: Django's local-memory cache (in-process) — no separate cache service/container at this scale.
- Live-tracking proxy: on-demand per client request, backed by a short-TTL (~15–30s) entry in the same local-memory cache — not a persistent background poller. Bounds transmiapp call volume to roughly one per TTL window regardless of concurrent users.
- Live-tracking "unavailable" contract (FR10): HTTP 200 always (never 5xx for a routine unavailable state), with an explicit `"status": "unavailable"` field distinct from `"status": "live"` with position data. Never omit the bus, return `null` silently, or serve stale cache past TTL unmarked.

**API & framework**

- API framework: Django REST Framework for all new JSON endpoints (nearby-query, live-position, route/stop GeoJSON) — DRF generic views (`RetrieveAPIView`/`ListAPIView`), not ViewSets+routers.
- Response formats: GeoJSON (`FeatureCollection`/`Feature`) for map/geometry endpoints; plain unwrapped DRF serializer output for non-geometry endpoints; DRF default `{"detail": "..."}` error shape, extended with `"code"` only for app-specific branchable conditions; ISO 8601 dates; snake_case JSON field casing throughout, including inside GeoJSON `properties`.
- URL/naming conventions: kebab-case URL segments, plural nouns (`stops/nearby/`, `routes/<id>/live-positions/`); snake_case Django URL pattern names and query params (`lat`, `lng`, `radius_m`).

**Security & privacy implementation**

- transmiapp credentials (spoofed User-Agent, hardcoded appid) live only in `transmiapp/services.py`, the sole module allowed to import `requests`/call the transmiapp host — enforced as a code-review rule.
- Geolocation coordinates excluded from application logs, Django's default request logging, and Sentry's captured request context (`send_default_pii=False`, plus explicit scrubbing via Sentry's `before_send` hook if needed) — a concrete code-review checklist item, sequenced to be in place *before* the nearby-query endpoint goes live.
- Avoid publicizing the reverse-engineered transmiapp endpoint's details (headers, spoofed User-Agent, URL structure) in any public-facing surface (docs, README, error messages, client-visible network calls).

**Infrastructure & monitoring**

- CI: GitHub Actions runs `pytest` (with coverage) and lint (`black`, `flake8`) on every push.
- CD: Manual — a bash script (`deploy.sh`) on the VPS pulls new images and replaces running containers; no automated deploy-on-merge.
- Monitoring/error reporting: Sentry (free tier) captures exceptions from both the GTFS refresh command and the live-tracking proxy; no email/cron-based alerting — Sentry's dashboard is the sole monitoring surface.
- TLS/HTTPS termination: Nginx + Certbot, already running on the target VPS outside the `docker-compose.yml` app stack (existing server-level infra, not a new container).
- Map tile source: OpenFreeMap — no API key, no usage cap, free.
- Static asset serving / NFR1 mechanism: WhiteNoise middleware (gzip/Brotli compression, far-future cache headers), zero added infrastructure.
- `crawler/` (Scrapy) app is retired once the GTFS pipeline is confirmed working — left in place until then, not extended with new spiders.

**Structural/organizational patterns**

- Business logic (spatial queries, GTFS parsing, transmiapp proxy calls) lives in each app's `services.py` — views/DRF endpoints stay thin (parse input, call service, serialize result).
- `routes/services/nearby.py` and `routes/services/gtfs_refresh.py` are the only code paths allowed to run raw PostGIS spatial queries.
- `transmiapp/` app owns no persistent models — live positions are cache-only, never written to the database.
- Always-visible trust UI (non-affiliation, attribution, location-use disclosure — FR14–16) structurally guaranteed via `app/templates/layout/base.html`, not repeated per-page.
- Tests: `tests/` subdirectory per app, `test_<module>.py` naming — `routes/tests/` and `transmiapp/tests/` are net-new (no test coverage exists today).
- `LANGUAGE_CODE='es'` in `app/settings.py` satisfies FR19.

### UX Design Requirements

- UX-DR1: Implement a lightweight custom design system as CSS custom properties (no framework, no build step) — color tokens, an 8-scale spacing system (4px–48px), a soft-curves border-radius scale (8px/14px/22px), and a type scale — loaded as a plain stylesheet through Django's static files app.
- UX-DR2: Implement the four-tier color system: (1) system identity — TransMilenio red base vs. SITP zonal blue; (2) corridor color — official per-corridor TM colors (A–M) as an accent stripe on trunk routes only, zonal routes rely on route code/chip instead; (3) app accent "Páramo" — a muted, desaturated moss-green reserved strictly for app chrome (location indicator, selection state, UI controls), deliberately never used for route identity; (4) semantic live/unavailable state — independent of the other three tiers, always paired with a shape/fill difference, never hue alone.
- UX-DR3: Typography — system font stack only (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`), no custom webfont; a monospace stack reserved for tabular data (live arrival times, distances, route codes) using `font-variant-numeric: tabular-nums` for column alignment.
- UX-DR4: Dark mode support — neutrals (paper/ink/line/muted) shift to a warm near-black rather than a flat inversion; route/system colors stay fixed across themes since they're an external real-world reference, not part of the app's own palette.
- UX-DR5: Build the Nearby Route Row component — route chip (code, system + corridor color), route/corridor name and destination, plain-language ETA sentence; states: live (green-worded ETA), no live data ("Sin datos en vivo," muted), tight margin ("— sal ya," caution tone), unreachable ("— no alcanzas," muted/struck, still shown not hidden), default resting state; entire row is a single tap target; state words are real text, not color-only.
- UX-DR6: Build the Map Marker Set component — three structurally distinct silhouettes: "Tu ubicación" (teardrop pin, app-accent color, anchored at point, never reused for anything else), SITP paradero (plain small dot, neutral at rest, fills with route color on selection), TM station (halo-ring marker, same states as paradero plus a route-count badge when unselected); bus marker (rounded capsule with pale windshield band marking front, rotates to heading; TM red with corridor stripe, SITP blue with no stripe); live = filled/full color, unavailable = dashed outline/muted/no heading claimed (stop markers have no live/unavailable state).
- UX-DR7: Build the Route Detail Panel component — route name/corridor, operating hours and days, a Ciclovía-alternate-routing tag when applicable, full stop list with per-stop ETA in the same plain-language format as the main list; tap a stop within the panel to see that stop's own detail; keyboard reachable and dismissible.
- UX-DR8: Build the Trust Footer component — non-affiliation statement, GTFS data source attribution, short plain-language location-use disclosure; single always-identical state, rendered on every page via the base template; community-toned copy, not legal boilerplate.
- UX-DR9: Build the Route Directory page/component (satisfies FR5/FR6) — a plain server-rendered list of all active (`is_active=True`) routes using the Nearby Route Row treatment minus ETA/distance columns, grouped/filterable by `route_mode`/`service_tier`; a plain-text filter input using a shareable `?q=` query param (server-rendered on submit, works without JS); reached via a low-emphasis link (e.g., from the Trust Footer), never a prominent homepage element — the homepage's "land on the comparison, not a search box" principle is unaffected.
- UX-DR10: Render overlapping/parallel routes that share a physical corridor as offset parallel strokes (a few pixels perpendicular to the shared path) so every corridor color stays visible — standard transit-cartography technique, not stacked/hidden lines.
- UX-DR11: Plain-language time display pattern — "Llega en X min · Y min caminando" as a sentence, never bare icon+number pairs; both figures derive from the stop's already-known straight-line distance (no new routing dependency); tight margin gets "sal ya," unreachable gets "no alcanzas" (both always shown, never hidden); routes without live tracking read "Sin datos en vivo" as a distinct case from timing.
- UX-DR12: Responsive layout — Split Stack (map block + list block stacked) on mobile reflows to Side-by-side on desktop/tablet via a single CSS breakpoint at 768px (`flex-direction: column` → `row`) — one fluid layout, not two separate designs or markup structures.
- UX-DR13: Empty state handling — if a manually placed pin or GPS location has no nearby routes/stops, show an explicit plain-language message explaining this rather than a blank map or a generic "no results."
- UX-DR14: Loading states — no global spinner or loading screen; each map/list widget shows a small local text placeholder while its own data fetch is in flight.
- UX-DR15: Error state pattern — two distinct, honestly-attributed messages: system-side ("our bug," acknowledged in-product, Sentry-captured, plain-language "estamos en eso" tone, no raw stack traces reach the rider) vs. upstream/external (explicitly named as a TransMilenio/SITP data or API issue outside the project's control) — never blame-shifting or hiding behind a generic error.
- UX-DR16: Accessibility implementation baseline — WCAG 2.1 AA (4.5:1 minimum contrast, including corridor colors against marker backgrounds); no state conveyed by color alone anywhere (live/unavailable shape difference, direction arrow + lightness variation, text-based feedback labels); real tap targets sized for touch on interactive rows (not just the visual chip); real semantic elements (`<button>`/`<a>`, not `<div onclick>`) so keyboard/screen-reader support comes from the platform; visible focus states by default (no `outline: none` without a real replacement); keyboard-operable core navigation (nearby list, route/stop panel open/dismiss, Route Directory filter and result links).
- UX-DR17: Geolocation UX — on load, map auto-centers on the rider's location and immediately renders nearby routes/stops within a fixed default walkable radius (15–20 min on foot) if geolocation is granted; if denied/unavailable, falls back to the last remembered browser-stored center (no account) or a citywide default, with manual pin placement offered as an equally first-class way to set "where," not a degraded fallback; tapping/dragging the map moves the center and re-runs the nearby query at the same fixed radius.
- UX-DR18: Panel/URL duality — each route/stop detail has its own real, server-rendered URL (supports FR17–18 shareable links); tapping from the nearby view opens the same content as an in-page panel (fast, no reload) while opening a panel updates the URL so a cold visit, refresh, share, or back-navigation all resolve to the identical content/state.
- UX-DR19: Manual testing protocol before each release — keyboard-only pass (tab through nearby list, open/dismiss a route panel, verify no traps); one Android TalkBack screen-reader pass before launch; a one-time color-blindness simulator spot-check of the corridor color set and live/unavailable states during Visual Foundation build-out. No dedicated automated accessibility CI step planned for v1.

### FR Coverage Map

FR1: Epic 1 - View all trunk/BRT routes/stops near current location on one map
FR2: Epic 1 - View all trunk/BRT routes/stops near a chosen (non-GPS) location
FR3: Epic 1 - Compare live bus proximity across multiple nearby trunk stops
FR4: Epic 1 - Identify trunk routes shared across multiple nearby stops
FR5: Epic 2 - Browse the full list of routes
FR6: Epic 2 - Search for a route by name or number
FR7: Epic 2 - View a route's full path and ordered stop sequence
FR8: Epic 2 - View a stop's details and which routes serve it
FR9: Epic 3 - See live BRT bus positions overlaid on the map
FR10: Epic 3 - Distinguish "position unavailable" from a normal live position
FR11: Epic 1 - Refresh static route/stop/schedule data from official GTFS source (rider-facing last-refreshed disclosure delivered in Epic 4, Story 4.1)
FR12: Epic 1 - Alert the maintainer when the GTFS refresh pipeline fails
FR13: Epic 3 - Alert the maintainer when the live-tracking source fails or changes
FR14: Epic 4 - Always-visible non-affiliation statement
FR15: Epic 4 - Attribution/credit for the official open-data source
FR16: Epic 4 - Plain-language explanation of location data usage
FR17: Epic 4 - Share a direct link to a specific route or stop
FR18: Epic 4 - Shared link opens directly to that route/stop view
FR19: Epic 5 - Entire app usable in Spanish, no other language required
FR20: Epic 5 - Sufficient color contrast, readable fonts, keyboard navigation

## Epic List

### Epic 1: Nearby Route & Stop Discovery (Foundation + Core Differentiator)
Riders can see every trunk (BRT/troncal) route and stop near a location (live GPS or manually chosen) at a glance, compared side by side against live bus proximity — the app's core differentiator, replacing route-by-route lookup. Scoped to trunk/BRT for MVP per the PRD's Risk Mitigation Strategy (query-performance simplification against ~550 system-wide routes; zonal expansion is Phase 2) — full-catalog browsing of both trunk and zonal routes is still covered, in Epic 2. Includes the Django 4.2.4→5.2 + SQLite→PostGIS foundation migration, the new data model (`BusStop`, `Route`, `Corridor`, `RouteSchedule`), and the manual GTFS refresh pipeline as enabling work, since nothing else can be built or demoed without real spatial data. Explicitly validated by the PRD as a standalone-viable MVP slice even without live tracking (Epic 3).
**FRs covered:** FR1, FR2, FR3, FR4, FR11, FR12
**Related NFRs:** NFR1, NFR2, NFR5, NFR8
**Implementation notes:** Server-side PostGIS `ST_DWithin` nearby-query filtered to `service_tier=troncal`/`stop_type=estacion_troncal` only (matches FR9's already-trunk-only live tracking), GTFS full-replace-by-natural-key refresh (manually triggered), UUID PKs, geolocation-coordinate logging exclusions from day one. Includes a real-feed verification pass (routes.txt/stops.txt/calendar.txt) before the data model lands, retirement of the stale `data/*.geojson` seed files (dated 2023-09-03) from the ongoing pipeline, and a README/setup-docs rewrite as the epic's closing story. UX: Nearby Route Row (UX-DR5), Map Marker Set (UX-DR6, stop markers only at this stage), four-tier color system (UX-DR2), geolocation UX with manual-pin fallback (UX-DR17), empty states (UX-DR13), plain-language time display (UX-DR11).

### Epic 2: Route & Stop Browsing
Riders can browse the full route catalog, search by name/code, and view any route's full path or any stop's full detail — independent of location, for planning ahead or out of curiosity. Works entirely off Epic 1's data foundation.
**FRs covered:** FR5, FR6, FR7, FR8
**Implementation notes:** Route Directory page with server-rendered `?q=` filter (UX-DR9), route/stop detail templates and their real per-item URLs (reused by Epic 4's sharing).

### Epic 3: Live Bus Tracking
Riders can see real live bus positions on trunk routes overlaid on the map, always able to tell live data from an honest "unavailable" state — and the maintainer is alerted the same day if the upstream source breaks. Layers directly onto Epic 1's map; no dependency on Epic 2.
**FRs covered:** FR9, FR10, FR13
**Related NFRs:** NFR3, NFR6, NFR9, NFR10
**Implementation notes:** `transmiapp` proxy isolation (sole module allowed to call the host), short-TTL (~15–30s) local-memory cache, explicit `"live"`/`"unavailable"` HTTP-200 contract, bus marker live/unavailable states (UX-DR6).

### Epic 4: Trust, Transparency & Sharing
Riders always see who built this app and how their location is used, trust the data's source, and can share a direct link to any route or stop that opens straight to that view for whoever receives it. Depends on Epic 2's detail pages existing for sharing; the trust footer itself has no other dependency.
**FRs covered:** FR14, FR15, FR16, FR17, FR18
**Implementation notes:** Trust Footer component (UX-DR8) on the base template; panel/URL duality (UX-DR18) so shared links and in-app panels resolve to the same state.

### Epic 5: Localization & Accessibility Hardening
Riders can use the entire app in Spanish with no other language required, and can read and navigate every page with sufficient contrast, readable text, and full keyboard operability. A hardening pass across everything built in Epics 1–4.
**FRs covered:** FR19, FR20
**Related NFRs:** NFR11, NFR12, NFR13
**Implementation notes:** `LANGUAGE_CODE='es'`, WCAG AA contrast/keyboard audit across all pages, manual testing protocol (UX-DR19: keyboard-only pass, Android TalkBack pass, colorblindness simulator spot-check).

## Epic 1: Nearby Route & Stop Discovery (Foundation + Core Differentiator)

Riders can see every trunk (BRT/troncal) route and stop near a location (live GPS or manually chosen) at a glance, compared side by side against live bus proximity — the app's core differentiator, replacing route-by-route lookup. Scoped to trunk/BRT for MVP per the PRD's Risk Mitigation Strategy; zonal expansion is Phase 2 (full-catalog browsing of both is still covered in Epic 2). Includes the Django 4.2.4→5.2 + SQLite→PostGIS foundation migration, the new data model, and the manual GTFS refresh pipeline as enabling work.

**FRs covered:** FR1, FR2, FR3, FR4, FR11, FR12 | **Related NFRs:** NFR1, NFR2, NFR5, NFR8 | **UX-DRs:** UX-DR2, UX-DR5, UX-DR6 (stop markers), UX-DR11, UX-DR13, UX-DR17

### Story 1.1: Foundation — Django 5.2 + PostgreSQL/PostGIS Upgrade

As a maintainer,
I want the app running on Django 5.2 LTS against a PostgreSQL+PostGIS database instead of Django 4.2.4/SQLite,
So that the rest of the product can be built on a modern, spatially-capable foundation instead of fighting an obsolete stack.

**Acceptance Criteria:**

**Given** the existing Django 4.2.4/SQLite codebase
**When** the upgrade is applied
**Then** the app runs on Django 5.2 LTS with a `postgis/postgis:17-3.5` PostgreSQL+PostGIS database via GeoDjango, started locally through Docker Compose
**And** the new `Dockerfile` pins **Python 3.11** as its base image (matches the architecture's "already fixed, not re-decided" call — not bumped as part of this modernization), with GDAL/GEOS system packages installed for GeoDjango
**And** WhiteNoise middleware is configured for static asset compression and cache headers (NFR1 mechanism)
**And** the legacy `db.sqlite3` is archived, not upgraded in place — the new database starts empty
**And** Gunicorn is configured to run with exactly **1 worker process** (`gunicorn --workers 1`, not Gunicorn's multi-core-scaling default) — required for Django's local-memory cache to behave as a single shared cache rather than one independent copy per worker, which would otherwise multiply calls to the fragile transmiapp API beyond the "one call per TTL window" bound Story 3.1 depends on (per `relaunch-architecture.md`'s Gunicorn worker count decision)

**Given** the old migration history (`routes/migrations/0001`–`0007`)
**When** the foundation lands
**Then** those migrations are deleted in preparation for a single fresh `0001_initial` to be generated once the amended models exist (Story 1.2)
**And** a base stylesheet defines the design token foundation as CSS custom properties — color palette, the 8-scale spacing system, the soft-curves border-radius scale, and the type scale — loaded through Django's static files app with no build step, so every component built in later stories pulls from tokens rather than hardcoded values (UX-DR1)

### Story 1.2: GTFS-Ready Data Model

As a maintainer,
I want the routes/stops data model to match the real TM/SITP structure (`BusStop` with `stop_type`, `Route` with `route_mode`/`service_tier`, `Corridor`, `RouteSchedule`, UUID primary keys),
So that the app can represent real transit data accurately instead of the old scraper-shaped schema.

**Acceptance Criteria:**

**Given** the `service_tier`, `day_type`, and natural-key (`gtfs_route_id`/`gtfs_stop_id`) field definitions are marked provisional in `relaunch-architecture.md`
**When** this story begins
**Then** a real `routes.txt`, `stops.txt`, `calendar.txt`, and `calendar_dates.txt` are pulled from the official 2025-10-28 GTFS static feed (ArcGIS Hub / Datos Abiertos Bogotá) to confirm `service_tier` sourcing, that `code`/`cenefa`/`transmilenio_id` do NOT simply equal `route_id`/`stop_id` (verify the actual mapping), and the full day-type value set plus `calendar.txt`/`calendar_dates.txt` precedence — this verification blocks the field definitions below, not just the amendment note

**Given** the amended model definitions in `relaunch-architecture.md`, confirmed against the real feed pull above
**When** this story lands
**Then** `BusStation` is renamed `BusStop` with a `stop_type` discriminator and the type-specific-fields check constraint; `Route.route_type` is split into `route_mode`/`service_tier`; `Corridor` and `RouteSchedule` are new models; all five models use UUID primary keys
**And** a single fresh `0001_initial` migration is generated against these models, applied cleanly to the empty PostGIS database from Story 1.1
**And** `RouteStations.bus_station` is renamed `bus_stop`, with corresponding renames in `routes/api_urls.py` (`bus-stations/`→`bus-stops/`), `routes/urls.py` (`bus_station_detail`→`bus_stop_detail`), and templates

### Story 1.3: Manual GTFS Refresh Pipeline

As a maintainer,
I want to run a management command that refreshes static route/stop/schedule data from the official GTFS feed,
So that riders never see data older than my last manual refresh.

**Acceptance Criteria:**

**Given** `refresh_gtfs` needs a GTFS static feed to run against
**When** I invoke the command
**Then** it takes a path to a locally downloaded GTFS feed archive as an argument — the maintainer downloads the current dated release from TransMilenio's open data portal (`datosabiertos-transmilenio.hub.arcgis.com`, published as a new dated document per release, e.g. "GTFS Estáticos 2025-11-25" — not a single fixed feed URL) and passes the local path in; the command itself does not reach out to the internet, keeping its failure surface limited to parsing/loading (matches `relaunch-architecture.md`'s "GTFS feed acquisition method" decision)
**And** the command's usage/README documents the portal name and how to invoke the command (feeds into Story 1.8)

**Given** a downloaded GTFS static feed
**When** I run `refresh_gtfs`
**Then** routes/stops/schedules are replaced inside a single DB transaction, matched by natural key (`gtfs_route_id`/`gtfs_stop_id`) rather than truncate-and-reinsert
**And** rows present before the refresh but absent from the new feed are set `is_active=False`, never deleted, so existing shared links (FR17–18) keep resolving
**And** `ciclovia_affected` is recomputed from the version-controlled corridor/service_tier rule on every run, never manually edited
**And** an unrecognized day-type value during schedule ingestion causes the row (or run, per the documented open decision) to be rejected, never silently misclassified
**And** no scheduled/cron trigger exists — the command only runs when the maintainer invokes it (FR11 as amended)

**Given** the legacy `data/*.geojson` files (dated 2023-09-03, superseded by the live GTFS feed as system of record)
**When** this story lands
**Then** they are removed from the ongoing pipeline's code path entirely — `refresh_gtfs` never reads from `data/` — and the directory is either deleted or clearly marked in the repo as historical/archived, not a live data source, so a future maintainer doesn't mistake it for current input

### Story 1.4: GTFS Refresh Failure Alerting

As a maintainer,
I want to be alerted via Sentry immediately if a GTFS refresh run fails,
So that I know right away instead of discovering stale or broken data later.

**Acceptance Criteria:**

**Given** Sentry is integrated into the Django app
**When** `refresh_gtfs` raises an exception
**Then** the exception is captured by Sentry with enough context to diagnose it, visible in the Sentry dashboard without any separate email/cron alerting mechanism
**And** Sentry's PII scrubbing (`send_default_pii=False`, `before_send` hook) is configured as part of this story, before any endpoint that touches geolocation goes live in a later story (NFR5 sequencing dependency)

### Story 1.5: Nearby Routes & Stops on the Map

As a rider,
I want to see all trunk (BRT/troncal) routes and stops near my current location, or near a location I choose myself, on one map,
So that I don't have to look up routes one at a time.

**Acceptance Criteria:**

**Given** I open the app and grant geolocation
**When** the page loads
**Then** the map auto-centers on my location and renders all trunk routes/stops (`service_tier=troncal` routes, `stop_type=estacion_troncal` stops — zonal is out of scope for this MVP query, per the PRD's Risk Mitigation Strategy) within a fixed default walkable radius (15–20 min) within 1 second (NFR2), via a server-side PostGIS `ST_DWithin` query
**And** my coordinates are never logged or persisted server-side (NFR5) — excluded from Django request logging and Sentry's captured request data

**Given** I deny or don't have geolocation
**When** the page loads
**Then** I can manually place a pin as an equally first-class way to set "where" (not a degraded fallback), or the map falls back to my last remembered center (browser-stored, no account) or a citywide default
**And** tapping or dragging the map moves the center pin and re-runs the nearby query at the same radius
**And** stops render using the Map Marker Set's station (halo-ring) treatment (UX-DR6) — the paradero marker is defined for zonal stops shown elsewhere (e.g. Epic 2 detail views) but never appears in this trunk-only nearby view; routes/stops use the system-identity and corridor color tiers (UX-DR2)

**Given** a manually placed pin lands somewhere with no nearby routes/stops
**When** the query returns empty
**Then** an explicit plain-language empty-state message explains this rather than showing a blank map (UX-DR13)

**Given** the nearby view on a mobile-width screen
**When** the viewport widens past 768px (desktop/tablet)
**Then** the layout reflows from Split Stack (map block above list block) to Side-by-side (map and list as permanent columns) via a single CSS breakpoint change, with no separate markup or distinct "desktop experience" (UX-DR12)

**Given** the map or nearby-list data is still being fetched
**When** the widget is loading
**Then** it shows a small local text placeholder rather than a global spinner, and the rest of the page remains usable in the meantime (UX-DR14)

### Story 1.6: Side-by-Side Stop Comparison

As a rider,
I want to compare multiple nearby stops side by side,
So that I can decide which one to walk to.

**Acceptance Criteria:**

**Given** the nearby query has returned results
**When** I view the comparison list
**Then** each row shows a route chip, name/destination, and a plain-language sentence ("Llega en X min · Y min caminando") rather than bare numbers (UX-DR11)
**And** when no live position data is available for a route, its row reads "Sin datos en vivo" rather than a blank, zero, or fabricated value — this is the default state until Epic 3 wires in real live positions, and the comparison view must work correctly in this state on its own
**And** rows for a tight walking margin or an unreachable option are still shown (never hidden), using the "sal ya"/"no alcanzas" phrasing once real live/walk-time data exists

### Story 1.7: Shared-Route Identification Across Nearby Stops

As a rider,
I want to see which routes are shared across multiple nearby stops,
So that I can spot redundant or overlapping options instead of treating each stop as unrelated.

**Acceptance Criteria:**

**Given** two or more nearby stops are served by the same route
**When** I view the comparison
**Then** that route is identifiable as shared across those stops (e.g., visually grouped or cross-referenced), rather than appearing as unrelated entries with no indication of overlap
**And** where routes share a physical corridor for a stretch on the map, their lines render as offset parallel strokes so each corridor color stays visible (UX-DR10)

### Story 1.8: Update README & Developer Setup Docs

As a maintainer,
I want the README and setup docs to describe the actual Docker/PostgreSQL/GTFS-refresh workflow,
So that I (or anyone else) can set up and run the project without following obsolete SQLite/Scrapy instructions.

**Acceptance Criteria:**

**Given** the current `README.md` describes the old `pip install` / `scrapy crawl sitp` / `load_bus_stations` / plain `runserver` workflow
**When** this story lands
**Then** it's rewritten to cover: Docker Compose setup (`docker-compose up`, app + PostGIS), and the new `refresh_gtfs` management command — including that the maintainer must first download the current dated GTFS release from `datosabiertos-transmilenio.hub.arcgis.com` (TransMilenio's open data portal; each release is published as a new dated document, e.g. "GTFS Estáticos 2025-11-25" — search the portal for the latest one rather than relying on a bookmarked link) before running `refresh_gtfs <path>` — and running the dev server inside the container
**And** all references to the retired `crawler`/Scrapy workflow and `load_bus_stations` are removed, not left alongside the new instructions as stale alternatives
**And** a `.env.example` documents required environment variables (DB creds, Sentry DSN, any transmiapp-related config) without real values, per the architecture's project structure

**Given** this story is the last one in Epic 1
**When** it's complete
**Then** a new contributor (or future-you) can go from a fresh clone to a running dev server using only the README — no tribal knowledge required

## Epic 2: Route & Stop Browsing

Riders can browse the full route catalog, search by name/code, and view any route's full path or any stop's full detail — independent of location, for planning ahead or out of curiosity. Works entirely off Epic 1's data foundation.

**FRs covered:** FR5, FR6, FR7, FR8 | **UX-DRs:** UX-DR9

### Story 2.1: Browse the Full Route List

As a rider,
I want to browse the full list of routes,
So that I can look one up even when I'm not near a stop.

**Acceptance Criteria:**

**Given** I visit the Route Directory page
**When** the page loads
**Then** I see a server-rendered list of all active (`is_active=True`) routes, each row using the Nearby Route Row treatment minus ETA/distance columns
**And** routes are grouped or filterable by `route_mode`/`service_tier` (TransMilenio trunk vs. TransMiZonal), not flattened into one undifferentiated list
**And** the page is reached via a low-emphasis link (e.g., from the Trust Footer), never a prominent homepage element — the homepage's "land on the comparison" principle is unaffected

### Story 2.2: Search Routes by Name or Number

As a rider,
I want to search for a specific route by name or number,
So that I can find it quickly instead of scanning the full list.

**Acceptance Criteria:**

**Given** I'm on the Route Directory page
**When** I type into the filter input and submit
**Then** the list narrows to routes matching my query by name or code, via a server-rendered `?q=` query param (works without JS, shareable URL)
**And** an empty-filter/no-match state ("no routes match") uses the same honest empty-state pattern established for the nearby view, rather than a blank list

### Story 2.3: View a Route's Full Path and Stop Sequence

As a rider,
I want to view a route's full path and ordered stop sequence on a map,
So that I can understand where it actually goes before boarding.

**Acceptance Criteria:**

**Given** I open a route's detail view (from the directory, the nearby comparison, or a direct link)
**When** the page/panel renders
**Then** I see the route's name/corridor, operating hours and days, a Ciclovía-alternate-routing tag when applicable, and its full geometry (`path`) drawn on the map with all stops in order, implementing the Route Detail Panel component (UX-DR7)
**And** directional indicators (arrows, distinct per-direction styling) are rendered along the line so the route's direction is unambiguous
**And** the panel is reachable and dismissible via keyboard (NFR13)

**Given** a route has stops/geometry recorded for both `RouteStations.DIRECTION_1` and `DIRECTION_2`
**When** the route's stop sequence and geometry are served to the frontend
**Then** both directions are included — this closes an existing bug, not a new requirement: today's `RouteStationsAPIView` (`routes/views.py`) only queries `DIRECTION_1`, with the `DIRECTION_2` block present but commented out (dead code), even though the existing template view (`RouteDetailView`) already correctly builds both as `route_station_groups = [route_1, route_2]`. The DRF migration of `RouteBusesAPIView`/`RouteStationsAPIView` (ad-hoc `DetailView` subclasses today, migrated to real DRF generic views per `relaunch-architecture.md`'s Implementation Patterns) is scoped as part of this story, and must restore `DIRECTION_2` rather than carry the omission forward — old endpoint paths are replaced by their DRF equivalents, not deleted with no replacement, per architecture's existing endpoint-naming decision (`routes/<id>/stations/`)
**And** a test (`routes/tests/test_views.py`, per the architecture's test-organization convention) asserts both directions are present in the endpoint's response for a route with stations in both directions, so this specific regression can't silently reappear

### Story 2.4: View a Stop's Details

As a rider,
I want to view a stop's details, including which routes serve it,
So that I can decide whether it's useful to me.

**Acceptance Criteria:**

**Given** I open a stop's detail view (from the map, a route's stop list, or a direct link)
**When** the page/panel renders
**Then** I see the stop's name, type (estación troncal vs. paradero zonal), and the full list of routes serving it, each shown in the same plain-language row format as the main comparison list
**And** tapping a route within the stop detail navigates to that route's own detail view

## Epic 3: Live Bus Tracking

Riders can see real live bus positions on trunk routes overlaid on the map, always able to tell live data from an honest "unavailable" state — and the maintainer is alerted the same day if the upstream source breaks. Layers directly onto Epic 1's map; no dependency on Epic 2.

**FRs covered:** FR9, FR10, FR13 | **Related NFRs:** NFR3, NFR6, NFR9, NFR10 | **UX-DRs:** UX-DR6 (bus marker states)

### Story 3.1: Live-Tracking Proxy & Live/Unavailable Contract

As a rider,
I want the app to fetch real bus positions from TransMilenio's live-tracking source on my behalf,
So that I never need to trust an app that exposes fragile third-party credentials or breaks silently.

**Acceptance Criteria:**

**Given** a request for a route's live positions
**When** the `transmiapp` proxy handles it
**Then** it checks a short-TTL (~15–30s) local-memory cache before calling the upstream host, bounding call volume to roughly one per TTL window regardless of concurrent users
**And** the transmiapp credentials (spoofed User-Agent, hardcoded appid) live only in `transmiapp/services.py`, the sole module allowed to call the host — never exposed in client-side JS or API responses (NFR6)

**Given** the upstream source is down, returns malformed data, or the cache lookup fails to refetch
**When** the proxy responds
**Then** it returns HTTP 200 with an explicit `"status": "unavailable"` field on that entry — never a 5xx, never a silently omitted bus, never `null` position, never stale cached data served past its TTL unmarked (FR10)
**And** this catch is narrowly scoped to the specific, known-expected failure modes of the transmiapp HTTP call (connection/read timeout, proxy error, empty response, JSON decode failure — matching the exception types already caught in today's `get_buses_by_route_name`) — **not** a blanket `except Exception`; any other, unanticipated exception is left to propagate uncaught rather than being folded into the "unavailable" response, so Story 3.3's Sentry capture can actually fire on it instead of being silently swallowed here

**Given** the upstream source is healthy
**When** the proxy responds
**Then** entries carry `"status": "live"` with position data — distinct and unambiguous from the unavailable case
**And** `transmiapp` owns no persistent models — live positions are cache-only, never written to the database (NFR10), so a live-tracking outage can never take down route/stop browsing (Epic 1/2 keep working)

**Given** the existing `routes.views.RouteBusesAPIView` calls `transmiapp.services.get_buses_by_route_name` directly today — with no TTL cache, no `"live"`/`"unavailable"` contract (it returns an empty list on any failure), and from the `routes` app rather than through `transmiapp`'s isolation boundary
**When** this story lands
**Then** `RouteBusesAPIView` is retired and its URL delegates to (or is replaced by) the new `transmiapp` proxy endpoint, so every live-position request — regardless of entry point — goes through the same short-TTL cache and `"live"`/`"unavailable"` contract; no code path is left calling `get_buses_by_route_name` (or any transmiapp function) directly outside `transmiapp/services.py`'s new cache wrapper
**And** the credential- and cache-isolation guarantees above (transmiapp host only ever called from `transmiapp/services.py`, cache bounding call volume) hold for 100% of live-position requests in the app, not just the ones reached through the new endpoint

### Story 3.2: Live Bus Positions on the Map

As a rider,
I want to see live positions of buses on trunk routes overlaid on the map, and clearly tell a live position apart from an unavailable one,
So that I never mistake stale data for a bus that's actually coming.

**Acceptance Criteria:**

**Given** the nearby comparison view or a route detail view is open
**When** live position data loads
**Then** buses render using the Map Marker Set's bus silhouette — TM buses red with a corridor-color stripe, SITP buses blue with no stripe — rotated to their heading
**And** a bus in the `"unavailable"` state renders as a dashed outline in a muted color with no heading claimed, using the same silhouette as a live bus so the shape stays learnable, never conveyed by color alone
**And** the Side-by-Side Stop Comparison rows from Story 1.6 now populate real ETAs where live data exists, replacing the "Sin datos en vivo" default for routes with live coverage
**And** no fixed latency target is enforced or implied — the UI surfaces staleness/unavailability explicitly rather than chasing a target the upstream source can't guarantee (NFR3)

**Given** the live-tracking source itself is down or returning errors (an upstream problem)
**When** I see the resulting "Sin datos en vivo" state
**Then** it is never phrased as the app's own failure — messaging is honestly attributed to the external TransMilenio/SITP source, distinct from a rare in-app error, which instead reads as an acknowledged "estamos en eso" tone with no raw stack trace ever reaching me (UX-DR15)

### Story 3.3: Live-Tracking Failure Alerting

As a maintainer,
I want to be alerted the same day if the live-tracking source becomes unavailable or its response format changes,
So that I catch the failure through monitoring instead of a friend telling me the bus icons disappeared.

**Acceptance Criteria:**

**Given** Sentry is integrated (per Story 1.4's configuration)
**When** the `transmiapp` proxy raises an exception (upstream down, response format changed, unexpected payload shape)
**Then** the exception is captured by Sentry automatically via the Django integration, visible in the dashboard the same day the failure occurs (NFR9)
**And** no separate scheduled health-check process is introduced — exception capture on the on-demand proxy calls is the entire monitoring mechanism, consistent with the solo-maintainer-operability stance

## Epic 4: Trust, Transparency & Sharing

Riders always see who built this app and how their location is used, trust the data's source, and can share a direct link to any route or stop that opens straight to that view for whoever receives it. Depends on Epic 2's detail pages existing for sharing; the trust footer itself has no other dependency.

**FRs covered:** FR14, FR15, FR16, FR17, FR18 | **Cross-epic:** FR11's rider-facing last-refreshed disclosure (core FR11 refresh capability is Epic 1) | **UX-DRs:** UX-DR8, UX-DR18

### Story 4.1: Always-Visible Trust Footer

As a rider,
I want to always see that this app is unaffiliated with TransMilenio/SITP, where its data comes from, and how my location is used,
So that I can trust it without wondering who's behind it.

**Acceptance Criteria:**

**Given** any page in the app
**When** it renders
**Then** the footer shows a clear non-affiliation statement (FR14), a data-source attribution line (e.g., "Datos de rutas: TransMilenio S.A. — Datos Abiertos") (FR15), and a short plain-language location-use disclosure (e.g., "Tu ubicación se usa solo para mostrarte rutas cercanas; no se guarda ni se comparte.") (FR16), rendered identically via `app/templates/layout/base.html` rather than repeated ad hoc per page
**And** the copy reads as an independent, community-toned effort, not corporate or government boilerplate, consistent with the app's non-affiliation stance

**Given** static route/stop data was populated by a `refresh_gtfs` run
**When** the footer renders
**Then** it also shows when that data was last successfully refreshed (e.g., "Datos actualizados: hace 3 meses" or an absolute date) (FR11) — computed as `MAX(updated_at)` across `Route`/`BusStop` at render time (no new stored field, per `relaunch-architecture.md`'s "Last-refreshed disclosure" note), so a rider can judge staleness for themselves rather than the data being presented as unconditionally current
**And** no numeric "stale" threshold or warning state is invented — the honest date itself is the disclosure, consistent with not asserting a freshness bound the project has no principled basis for setting

### Story 4.2: Share a Direct Link to a Route or Stop

As a rider,
I want to share a direct link to a specific route or stop with someone else,
So that they see exactly what I'm looking at without extra navigation.

**Acceptance Criteria:**

**Given** I'm viewing a route or stop's detail (in-page panel or full page)
**When** I copy the current URL
**Then** it's a real, stable, server-rendered URL for that specific route/stop, unaffected by whether I opened it as a panel or a cold page load (FR17)

**Given** someone else opens that shared URL
**When** the page loads
**Then** they see that exact route/stop view directly — no additional search or navigation required (FR18)
**And** opening a detail panel from the nearby view updates the browser URL to match, so refresh, back-navigation, and sharing from that state all resolve to the same content (UX-DR18)
**And** the URL keeps resolving correctly across a GTFS refresh, since routes/stops keep their UUID identity even when superseded data changes their attributes (relies on Story 1.2/1.3's natural-key refresh behavior)

## Epic 5: Localization & Accessibility Hardening

Riders can use the entire app in Spanish with no other language required, and can read and navigate every page with sufficient contrast, readable text, and full keyboard operability. A hardening pass across everything built in Epics 1–4.

**FRs covered:** FR19, FR20 | **Related NFRs:** NFR11, NFR12, NFR13 | **UX-DRs:** UX-DR3, UX-DR4, UX-DR16, UX-DR19

### Story 5.1: Spanish-Only UI

As a rider,
I want to use the entire app in Spanish,
So that I never hit an English label or operator-jargon term I don't understand.

**Acceptance Criteria:**

**Given** any page or component across Epics 1–4
**When** it renders
**Then** all UI text — labels, ETAs, error/empty states, trust footer, route directory — is in plain Spanish, with `LANGUAGE_CODE='es'` set in `app/settings.py`
**And** a pass across every component built so far confirms no leftover English or raw operator-jargon strings remain (e.g., "sal ya"/"no alcanzas" phrasing, not literal translations of internal API field names)

### Story 5.2: Visual Accessibility — Contrast, Fonts, No-Color-Alone States

As a rider,
I want sufficient color contrast and readable font sizes across the whole app, and to never depend on color alone to understand a state,
So that I can use the app comfortably regardless of lighting, screen quality, or color vision.

**Acceptance Criteria:**

**Given** any text or route/status color combination introduced in Epics 1–4
**When** audited
**Then** it meets WCAG 2.1 AA contrast (4.5:1 minimum for normal text), including corridor colors against their marker backgrounds (NFR11)
**And** font sizes are readable by default across the system font stack, with no reliance on pinch-zoom for core content (NFR12); the monospace stack with `tabular-nums` is used consistently for ETAs, distances, and route codes (UX-DR3)
**And** every state that was implemented using color as a signal (live/unavailable bus, route direction, tight-margin/unreachable rows) is verified to also carry a shape or text difference, not color alone (UX-DR16)
**And** dark mode renders correctly — neutrals shift to a warm near-black, route/system colors stay fixed (UX-DR4)

### Story 5.3: Keyboard-Operable Core Navigation

As a rider,
I want to navigate the app's core interactions using only a keyboard,
So that I'm not locked out if I can't or don't want to use touch/mouse.

**Acceptance Criteria:**

**Given** the nearby comparison list, route/stop detail panels, and the Route Directory's filter and result links
**When** I navigate using only Tab/Enter/Escape
**Then** every interactive element is reachable, operable, and dismissible without a mouse, with no keyboard traps (NFR13, FR20)
**And** focus states are visible by default on every interactive element (no `outline: none` without a real visible replacement)
**And** interactive rows/markers use real semantic elements (`<button>`/`<a>`), not `<div onclick>`, so this behavior comes from the platform rather than bolted-on ARIA

### Story 5.4: Pre-Launch Manual Accessibility Testing Pass

As a maintainer,
I want to run a manual accessibility testing pass before launch,
So that I catch what the plain-language and no-color-alone rules might have missed without needing an automated test suite I can't sustain solo.

**Acceptance Criteria:**

**Given** the app is feature-complete through Epics 1–4
**When** I run the pre-launch checklist
**Then** I've completed a keyboard-only pass (tab through the nearby list, open/dismiss a route panel, confirm no traps), one Android TalkBack screen-reader pass on the primary target device, and a one-time color-blindness simulator spot-check of the corridor color set and live/unavailable states
**And** any issues found are fixed before launch or explicitly logged as known follow-ups — this checklist is a manual pre-release gate, not an ongoing automated CI step (consistent with the architecture's existing pytest+black+flake8-only CI scope)
