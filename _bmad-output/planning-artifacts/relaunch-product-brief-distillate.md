---
title: "Product Brief Distillate: public_transport"
type: llm-distillate
source: "relaunch-product-brief.md"
created: "2026-08-02"
purpose: "Token-efficient context for downstream PRD creation"
---

# Distillate: Bogotá Transit Route Guide relaunch

## Existing Codebase (as of relaunch decision, dormant since 2023-09-03)

- **Stack**: Django 4.2.4 monolith, SQLite, Scrapy 2.10.1 crawler wired directly into Django models via `scrapy-djangoitem` (no separate scraped-data schema), Mapbox GL JS 2.14.1 for maps, server-rendered Django templates, `python-telegram-bot` 20.4. Tooling already in place: black, flake8, pre-commit, pytest+coverage — reasonably disciplined for a solo project, worth keeping the habit in the rebuild.
- **Repo structure**: `app/` = actual Django project settings; `routes/` = core Django app (models/views/templates/admin, the real product logic); `crawler/` = Scrapy spiders/items/pipelines; `telegram_bot/` = bot entrypoint (minimal); `transmiapp/` = NOT Django settings, it's a small `requests`-based client for an unofficial third-party API.
- **Existing data model** (`routes/models.py`) is a reasonable starting point, not necessarily final: `Route` (name, code e.g. "19-1", route_type enum: transmilenio/alimentador/urbano/complementario/especial, color, schedule as free-text string, map_link, details_link, publication_date/last_update), `BusStation` (name, code, link, address, transmilenio_id unique, cenefa = SITP's official stop code, audio, lat/lon), `RouteStations` join table (route, bus_station, direction 1/2, position = ordered stop sequence per direction).
- **Existing GeoJSON API endpoints** (`routes/api_urls.py`, added Sep 2023): `route/<pk>/stations/` → LineString of stop coords; `route/<pk>/buses/` → live FeatureCollection of bus positions, proxying `transmiapp.services.get_buses_by_route_name`.
- **Historical scraper target** (now presumed broken/fragile): `www.transmilenio.gov.co/loader.php`, an internal AJAX/DataTables endpoint (`lServicio=Rutas&lFuncion=lstRutasAjax`) returning HTML fragments parsed via CSS selectors, with a hardcoded literal timestamp param (`_: 1642795202244`) and regex-scraped JS for detail-page URLs. Classic "breaks silently on redesign" pattern — the exact failure mode that ended v1.
- **"Transmidata"**: static GeoJSON datasets already committed under `data/` (largest ~26MB): `Estaciones_Troncales_de_TRANSMILENIO`, `Trazados_Troncales_de_TRANSMILENIO`, `Paraderos_Zonales_del_SITP`, `Rutas_Zonales_SITP`. Field names (`objectid`, `globalid`, `cenefa`, `troncal_estacion`) and CRS metadata (`OGC:1.3:CRS84`) indicate an ArcGIS/open-data-portal export, bulk-imported once (Sept 2023) via `load_bus_stations` management command matched to `BusStation` rows by `cenefa`.
- **Unofficial live-position source** (currently what the app uses): `transmiapp/services.py`, `get_buses_by_route_name`, calls an undocumented Google App Engine endpoint `tmsa-transmiapp-shvpc.uc.r.appspot.com/location/ruta`, reverse-engineered from the official mobile app, sends a spoofed iOS User-Agent and a hardcoded `appid` header. Fragile, unofficial, could break or be blocked anytime — confirmed still the only working live-position path (see Research below).
- **Telegram bot current state**: essentially non-functional — only `/start` (greeting), `/help` (static text), and an echo handler. Doesn't call `routes` or `transmiapp` services at all. A real rebuild target for phase 2, not a resurrection of existing code.
- **Known incomplete/stubbed code**: `parse_schedule` in `crawler/utlis.py` always returns hardcoded default times — weekday parsing was never implemented despite the docstring showing real schedule formats (e.g. "L-S | 04:00 AM - 11:00 PM"). Two TODOs in `sitp_spider.py` (route terminus names, last-updated dates) were never done.
- **Secrets/config**: `.env` had exactly one key, `TELEGRAM_BOT_API_KEY`. No Mapbox token found hardcoded — likely needs to be reintroduced.
- **No CI config found.** Minimal test coverage (`crawler/tests/test_utils.py` only).

## Research: Bogotá Transit Data Source Landscape (as of 2026-08)

- **Official static GTFS is real and current**: TransMilenio runs an open-data portal on ArcGIS Hub (`datosabiertos-transmilenio.hub.arcgis.com`) publishing dated GTFS static feed dumps roughly quarterly (confirmed dumps dated 2025-07-23 and 2025-10-28). Also listed on Bogotá's main open-data portal `datosabiertos.bogota.gov.co` (org=transmilenio, tag "GTFS"/"SITP") and mirrored on World Bank Data Catalog / energydata.info. There's also a direct feed reference at `gis.transmilenio.gov.co/gtfs/` context (see real-time note below — that specific host is stale).
- **Legal basis for reuse is explicit and favorable**: TransMilenio publishes this data under Colombia's Transparency Law (Ley 1712 de 2014), explicitly permitting reuse including commercial/value-added apps. This is a genuine strategic shift from 2023 — scraping raw HTML is very likely unnecessary now for static route/station/schedule data.
- **GTFS-Realtime: investigated directly, confirmed dead.** `gis.transmilenio.gov.co/gtfs/` is a page branded "GTFS Tiempo Real TRANSMILENIO S.A." (credited to ESRI Colombia) advertising three GTFS-RT `.pb` endpoints: `vehiclepos.pb`, `serviceAlerts.pb`, `tripupdate.pb`. Direct testing (2026-08-02): **all three return HTTP 404.** The page itself uses a visibly dated template (jQuery 3.4.1, Bootstrap 3.4.1, free w3schools theme) and has no Wayback Machine snapshot newer than **January 2021** — strong evidence this has been abandoned for years, not actively maintained alongside the newer ArcGIS Hub static portal. **Conclusion: no working official real-time feed exists today.** Worth a periodic recheck (e.g., every 6-12 months) in case it's revived, but not worth blocking design decisions on.
- **Zonal (SITP feeder) GTFS coverage completeness is unverified** — not yet confirmed whether the official static feed covers all 345 zonal routes as thoroughly as trunk/BRT routes. Flagged as an open validation task before fully trusting the "stable foundation" framing for the whole network.
- **Legacy aggregators are dead ends**: transitfeeds.com's Bogotá "SIMUR" feed listing is deprecated (shutting down Dec 2025, unmaintained since ~Jan 2021) — don't use it. **MobilityDatabase.org** is the modern successor aggregator (6000+ feeds) and the recommended place to cross-check/discover a current versioned Bogotá feed instead.
- **System scale** (as of ~2024 figures found): 99 BRT trunk routes, 107 feeder routes, 345 zonal routes (~550+ total). Zonal routes are described by riders/commentary as even more confusing than trunk routes.
- **Active restructuring in progress**: new TransMiZonal routes launched through late 2025/into 2026 (e.g. Bosa–Portal Américas, Ciudad Bolívar–Portal Sur, EG48 Soacha–CAD, LH803/HA601/LA856); explicit stated operator intent to reduce zonal routings and connect them to trunk lines. Unified fare across trunk/TransMiZonal/TransMiCable rose to $3,550 COP for 2026. This means even official GTFS needs an ongoing refresh pipeline, not a one-time import — the system will keep changing under any static snapshot.
- **TransMiCable Ciudad Bolívar** had a scheduled maintenance closure Oct 4–19, 2025, with substitute routes and "digital channels" activated — a signal the operator does invest somewhat in digital comms during disruptions.

## Competitive Landscape (from research)

- **TransMiApp** (official, also called "Transmilenio y SITP") — canonical source for route/schedule changes and suspensions via press bulletins; not necessarily intuitive for casual route discovery.
- **Moovit** — community favorite among locals, lets riders filter to just "T" (red Transmilenio) buses on a map without a specific query; crowdsourced so coverage/accuracy is uneven, no offline mode.
- **Google Maps** — broadest baseline static coverage (ingests any public GTFS), reliable fallback, but explicitly weak on Bogotá real-time accuracy.
- **MoviliXa / TransmiSitp** — an older small third-party trip-planner app found on iOS App Store; evidence this developer isn't the first to attempt an independent Bogotá transit app.
- Citymapper/Waze: no meaningful Bogotá-specific transit feature evidence found.
- **Core competitive gap identified**: discoverability — "which bus do I actually need" — not the ride itself. Direct quote from research: "if you can find which bus you need in the app, it's certainly a good way to travel."
- Broader context: recurring operational disruption is framed as a "crisis" in local press (El Tiempo), and TransMilenio runs an active PQRS (complaints) channel — reliability/trust issues extend beyond just route info.

## Scope Signals (explicit user decisions during discovery)

- **MVP channel**: web app first; Telegram bot revival is a real phase-2 candidate, not v1.
- **Real-time tracking**: explicitly confirmed as core to v1 value prop, accepted as the highest-risk piece (no official feed — confirmed dead, see above), despite being a solo nights-and-weekends effort. This tension is deliberately named as a risk in the brief, not silently scoped down.
- **Effort model**: solo, nights & weekends — favors a lean, low-maintenance MVP; scope was sized down accordingly (native app, full trip planning, all-345-zonal-routes real-time, and any commercial/partnership work are explicitly out for v1).
- **Success bar**: qualitative and personal — "people I know actually use it for real trips," tracked informally (direct check-ins) rather than analytics, deliberately consistent with the "no data harvesting" principle. User explicitly chose to keep this qualitative rather than set a numeric target when offered the choice.
- **Positioning choice**: user explicitly chose to keep the personal/friends-and-family narrative as primary, with the civic-infrastructure/open-data-community framing kept as a light aside (in Vision) rather than elevated to a co-equal narrative.
- **Technical modernization wishlist** (from user, captured but not detailed in the exec brief): upgrade Django/Python versions, containerize with Docker, reconsider database choice (current is SQLite; needs to suit geospatial data + a recurring refresh pipeline), install/expand pytest coverage properly. No specific target versions or DB engine were chosen during this session — open for architecture/PRD phase.

## Rejected / Out of Scope for v1 (with rationale, so downstream work doesn't re-propose them)

- **Telegram bot revival** — not rejected outright, deliberately deferred to phase 2 since it's currently non-functional and effort is constrained.
- **Real-time coverage of all 345 zonal routes** — deferred; start with trunk/BRT only, expand deliberately once the pattern is proven.
- **Official partnership / licensing conversation with TransMilenio** — explicitly out of scope; project remains independent, non-commercial, unaffiliated.
- **Native mobile app** — out of scope; web app only for v1.
- **Trip planning / multi-leg itinerary routing** — explicitly separated out as "a bigger, separate problem" from route discovery + live position, which is the v1 focus.
- **Analytics/usage tracking** — implicitly rejected in favor of informal adoption tracking, to stay consistent with the stated "no data harvesting" principle.

## Open Questions Surfaced But Not Resolved

- Exact database engine and hosting choice for the geospatial + refresh-pipeline needs (mentioned as a goal, not decided).
- Whether the official static GTFS feed's zonal-route coverage is as complete as trunk — needs a validation spike before fully trusting it as the "stable foundation."
- No running-cost ceiling set yet for map tiles / geospatial DB / any infrastructure (flagged as a risk in the brief, not resolved).
- Target language(s) for the UI — not explicitly discussed; Spanish-primary is the implicit assumption given the audience (Bogotá riders, friends/family) but was never confirmed with the user.
- No concrete timeline or phased build-order was set (deliberately, given effort is "nights and weekends" and self-paced) — worth revisiting at PRD/architecture stage if a rough sequencing would help avoid the scope-to-bandwidth mismatch the skeptic review flagged.
