d# Story 1.2: GTFS-Ready Data Model

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want the routes/stops data model to match the real TM/SITP structure (`BusStop` with `stop_type`, `Route` with `route_mode`/`service_tier`, `Corridor`, `RouteSchedule`, UUID primary keys),
so that the app can represent real transit data accurately instead of the old scraper-shaped schema.

## Acceptance Criteria

1. **Given** the `service_tier`, `day_type`, and natural-key (`gtfs_route_id`/`gtfs_stop_id`) field definitions were marked provisional in `relaunch-architecture.md`, **when** this story begins, **then** verification against a real, current GTFS static feed is already complete — see Dev Notes → Real-Feed Verification Findings below for the confirmed mappings this story implements against (not the provisional guesses the architecture doc flagged as blocking).
2. **Given** the confirmed model definitions below, **when** this story lands, **then** `BusStation` is renamed `BusStop` with a `stop_type` discriminator (`estacion_troncal`/`paradero_zonal`/`estacion_cable`) and a matching 3-way `CheckConstraint`; `Route.route_type` splits into `route_mode` (`transmilenio`/`transmizonal`/`transmicable`) and `service_tier` (`troncal`/`alimentador`/`urbano`/`complementario`/`especial`/`dual`/`cable`); `Corridor` and `RouteSchedule` are new models; all five models (`BusStop`, `Route`, `RouteStations`, `RouteSchedule`, `Corridor`) use UUID primary keys.
3. **And** a single fresh `0001_initial` migration is generated against these models and applies cleanly to the empty PostGIS database from Story 1.1.
4. **And** `RouteStations.bus_station` is renamed `bus_stop`, with corresponding renames throughout `routes/api_urls.py` (`bus-stations/`→`bus-stops/`), `routes/urls.py` (`bus_station_detail`→`bus_stop_detail`, `bus_stations_list`→`bus_stops_list`), `routes/views.py`, `routes/admin.py`, and templates (`busstation_*.html`→`bus_stop_*.html`) — the app must still run (`manage.py check` clean, every existing page renders without error) after the rename, not just the model file in isolation.
5. **And** `Route.unique_together = ('code', 'name')` is **dropped** — verified against the real feed that real `(code, name)` pairs are not unique (252 duplicate `route_short_name` values found across 1024 routes, e.g. two unrelated routes both coded `"G45"`). `gtfs_route_id` is the only field the natural-key refresh (Story 1.3) can safely rely on for uniqueness.
6. **And** `Route.route_mode`/`Route.service_tier` explicitly support **TransMiCable** (`route_mode=transmicable`, `service_tier=cable`) and `BusStop.stop_type` explicitly supports `estacion_cable` — a real, present-in-the-feed mode the architecture doc didn't anticipate. Confirmed with Vera: model it now (unlike Metro/Regiotram, which stay deferred) rather than silently drop it.
7. **And** `Route.service_tier` explicitly supports **`dual`** (`Transmilenio-Dual` in the feed, 26 routes — hybrid trunk/feeder routes, e.g. code `"M86-K86"`) as its own value, distinct from `troncal`/`alimentador`. Confirmed with Vera: don't force-fit it into either existing tier. It is correctly excluded from the MVP trunk-only nearby-query filter (`service_tier=troncal`, used starting Story 1.5) by construction — a documented scoping gap, not a defect.

## Tasks / Subtasks

- [x] Task 1: Rename `BusStation` → `BusStop`; add `stop_type`, `gtfs_stop_id`, `location`, UUID PK (AC: #1, #2, #6)
  - [x] 1.1 `stop_type` choices: `STOP_TYPE_TRUNK='estacion_troncal'`, `STOP_TYPE_ZONAL='paradero_zonal'`, `STOP_TYPE_CABLE='estacion_cable'` (new)
  - [x] 1.2 `gtfs_stop_id = models.CharField(max_length=50, unique=True)` — the refresh natural key (GTFS `stops.txt` `stop_id`)
  - [x] 1.3 `location = gis_models.PointField()` (from `django.contrib.gis.db.models`, **not** plain `django.db.models` — see Model definitions code block below for the exact import) replaces `latitude`/`longitude` `DecimalField`s
  - [x] 1.4 Zonal-only fields stay nullable: `cenefa`, `zona_sitp`, `audio`. Trunk-only fields stay nullable: `transmilenio_id`, `numero_vagones`, `numero_accesos`, `biciestacion`. Cable stops (`estacion_cable`) leave **both** sets null — the feed carries no cenefa/transmilenio_id-equivalent identifier for them (see Dev Notes)
  - [x] 1.5 **Drop the existing `code` field entirely** — `BusStop` has no rider-facing short-code equivalent in the real data (architecture's model sketch never included one; the old `BusStation.code` was scraper-invented). `cenefa`/`transmilenio_id`/`gtfs_stop_id` cover identity needs instead
  - [x] 1.6 3-way `CheckConstraint` (`busstop_type_specific_fields_consistent`): zonal rows require `cenefa` set + `transmilenio_id` null; trunk rows require `transmilenio_id` set + `cenefa` null; cable rows require both null
  - [x] 1.7 `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - [x] 1.8 `__str__` returns `self.name` (not `self.code`, since `code` no longer exists); `get_absolute_url()` reverses `routes:bus_stop_detail`

- [x] Task 2: Split `Route.route_type` → `route_mode`/`service_tier`; add `gtfs_route_id`, `is_active`, `ciclovia_affected`, `corridor`, `path`, UUID PK; drop `unique_together` (AC: #1, #2, #5, #6, #7)
  - [x] 2.1 `route_mode` choices: `ROUTE_MODE_TRUNK='transmilenio'`, `ROUTE_MODE_ZONAL='transmizonal'`, `ROUTE_MODE_CABLE='transmicable'` (new)
  - [x] 2.2 `service_tier` choices: `troncal`, `alimentador`, `urbano`, `complementario`, `especial`, `dual` (new), `cable` (new) — 7 values total
  - [x] 2.3 `gtfs_route_id = models.CharField(max_length=50, unique=True)` — refresh natural key (GTFS `routes.txt` `route_id`, confirmed 100% unique across all 1024 rows, unlike `code`)
  - [x] 2.4 `corridor = models.ForeignKey('routes.Corridor', null=True, related_name='routes', on_delete=models.SET_NULL)` — required **only** for `service_tier=troncal` (not the whole `route_mode=transmilenio` bucket — refined from the architecture sketch; see Dev Notes for why). `CheckConstraint` `route_corridor_required_for_troncal_only`: `service_tier=troncal` ⟹ `corridor` set; any other `service_tier` ⟹ `corridor` null
  - [x] 2.5 `is_active = models.BooleanField(default=True)`; `ciclovia_affected = models.BooleanField(default=False)` — schema only, no derivation logic (Story 1.3 computes it on every sync)
  - [x] 2.6 `path = gis_models.MultiLineStringField(null=True)` — new geometry field for GTFS shape data, unpopulated by this story
  - [x] 2.7 `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - [x] 2.8 **Drop** `unique_together = ('code', 'name')` from `Meta` — do not replace it with any other uniqueness constraint on `code`/`name`; `gtfs_route_id` is the only safe unique key (verified — see AC #5)

- [x] Task 3: Create `Corridor` model — schema only, no data (AC: #2)
  - [x] 3.1 `id` UUID PK; `name` (unique, e.g. "Calle 26"); `zone_letter`; `color`; `pdf_link`
  - [x] 3.2 `CheckConstraint` `corridor_color_valid_hex`: `color` matches `^#[0-9A-Fa-f]{6}$`
  - [x] 3.3 Do **not** populate any corridor rows or build the corridor-mapping fixture in this story — that's Story 1.3's job (`routes/fixtures/corridors.py` + `gtfs_refresh.py` lookup)

- [x] Task 4: Create `RouteSchedule` model with the real, verified `day_type` value set (AC: #1, #2)
  - [x] 4.1 `day_type` choices — **replace the architecture's provisional 2-value `L-S`/`D-F` guess** with the 7 real weekday patterns confirmed active in `calendar.txt` (see Dev Notes table): `L-V` (Mon–Fri), `SAB` (Sat only), `L-S` (Mon–Sat), `DOM` (Sun only), `L-V-D` (Mon–Fri + Sun, no Sat), `SAB-DOM` (weekend), `DIARIO` (daily). `max_length=10` (longest value `SAB-DOM` is 7 chars)
  - [x] 4.2 `start_time`/`end_time` as `DurationField` (not `TimeField` — GTFS times can exceed 24:00:00 for trips spanning midnight; see architecture Dev Notes)
  - [x] 4.3 `route = models.ForeignKey('routes.Route', related_name='schedules', on_delete=models.CASCADE)`
  - [x] 4.4 `id` UUID PK
  - [x] 4.5 No ingestion logic here — Story 1.3's `gtfs_refresh.py` populates rows from `trips.txt`/`stop_times.txt`/`frequencies.txt` and rejects any future `service_id` weekday pattern that doesn't match one of the 7 known values, per the existing "reject, don't guess" precedent

- [x] Task 5: Rename `RouteStations.bus_station` → `bus_stop`; UUID PK (AC: #4)
  - [x] 5.1 `bus_stop = models.ForeignKey('routes.BusStop', related_name='route_stations', on_delete=models.PROTECT)`
  - [x] 5.2 `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - [x] 5.3 `route` FK also switches to a UUID target automatically once `Route.id` is UUID — no field change needed on `RouteStations.route` itself, just confirm it still resolves correctly post-migration

- [x] Task 6: Fix every app-wide reference to the renamed model/fields so the app keeps running (AC: #4)
  - [x] 6.1 `routes/admin.py`: rename `BusStationAdmin` → `BusStopAdmin`, registered against `BusStop`; `search_fields`/`list_display` drop `code`, add `cenefa`/`gtfs_stop_id`; `RouteAdmin.list_display` replaces `route_type` with `route_mode`, `service_tier`; `RouteStationsAdmin.list_display`/`list_select_related` replace `bus_station` with `bus_stop`
  - [x] 6.2 `routes/views.py`: `BusStationsListView`/`BusStationsDetailView` → `BusStopsListView`/`BusStopsDetailView`, each with an explicit `template_name` (`routes/bus_stop_list.html`/`routes/bus_stop_detail.html` — Django's default template-name resolution would otherwise look for `routes/busstop_list.html`, not matching AC #4's `bus_stop_*.html` naming); `RouteStationsAPIView`'s coordinate lookup changes from `route_station.bus_station.longitude`/`.latitude` to `route_station.bus_stop.location.x`/`.location.y` (GeoDjango `Point.x`=longitude, `.y`=latitude)
  - [x] 6.3 `routes/urls.py`: `bus_station_detail`→`bus_stop_detail`, `bus_stations_list`→`bus_stops_list`, URL segment `bus-stations/`→`bus-stops/`; view class names updated to match Task 6.2
  - [x] 6.4 `routes/api_urls.py`: no URL pattern changes needed (`route/<pk>/buses/` and `/stations/` don't reference `bus_station` in the path itself), but confirm imports still resolve after Task 6.2's view renames
  - [x] 6.5 Rename templates: `busstation_list.html`→`bus_stop_list.html`, `busstation_detail.html`→`bus_stop_detail.html`. Update field references inside: drop the `code`/`Code` column entirely (field no longer exists); `bus_station`→`bus_stop` context var name; `longitude`/`latitude`→`location.x`/`location.y` in the detail page's map marker script
  - [x] 6.6 `routes/templates/routes/route_detail.html`: `route_station.bus_station.code` column removed (no replacement — `bus_stop` has no short-code field); `route_station.bus_station.get_absolute_url`/`.name` → `route_station.bus_stop.get_absolute_url`/`.name`
  - [x] 6.7 `routes/templates/routes/home.html`: `route.get_route_type_display` → `route.get_service_tier_display` (more informative than `route_mode` for this listing — matches the granularity riders actually care about)
  - [x] 6.8 `app/templates/layout/base.html`: nav link `{% url 'routes:bus_stations_list' %}` → `{% url 'routes:bus_stops_list' %}`; label "Bus stations" → "Bus stops"
  - [x] 6.9 Do **not** touch `crawler/pipelines.py`, `crawler/items.py`, `crawler/spiders/sitp_spider.py`, or `routes/management/commands/load_bus_stations.py` — see Dev Notes → Scope Guardrails for why this is a safe, deliberate deferral, not an oversight

- [x] Task 7: Generate the fresh `0001_initial` migration; apply to the empty PostGIS database (AC: #3)
  - [x] 7.1 `docker compose run --rm app python manage.py makemigrations routes` — must run inside the `app` container (GDAL/GEOS required for `django.contrib.gis` fields, per Story 1.1's Dev Notes)
  - [x] 7.2 Inspect the generated migration: confirm it's a single `0001_initial.py` creating all 5 models with the constraints from Tasks 1–5, no stray operations
  - [x] 7.3 `docker compose run --rm app python manage.py migrate` against Story 1.1's empty PostGIS database — must apply cleanly with zero errors
  - [x] 7.4 `docker compose run --rm app python manage.py check` — must report no issues

- [x] Task 8: Model + constraint tests (Testing Standards)
  - [x] 8.1 `routes/tests/test_models.py` (new, `@pytest.mark.django_db`): each `CheckConstraint` is exercised both ways — a valid row per `stop_type`/`service_tier` saves; an invalid combination (e.g. zonal `BusStop` with `transmilenio_id` set, or `service_tier=troncal` `Route` with `corridor=None`) raises `IntegrityError`
  - [x] 8.2 UUID PK sanity test: a created `Route`/`BusStop` row's `.id` is a `uuid.UUID` instance, not an int
  - [x] 8.3 Uniqueness regression tests: `gtfs_route_id` and `gtfs_stop_id` reject duplicates; **explicitly assert** that two `Route` rows with the same `(code, name)` but different `gtfs_route_id` save successfully — a regression guard against re-adding the dropped `unique_together` (AC #5)
  - [x] 8.4 `RouteSchedule.day_type`: all 7 real values (`L-V`, `SAB`, `L-S`, `DOM`, `L-V-D`, `SAB-DOM`, `DIARIO`) are valid choices; an unrecognized value is rejected by `full_clean()`
  - [x] 8.5 `Corridor.color` `CheckConstraint`: `#4f7a5b` (valid hex) saves; `green` or `#4f7a5` (5 hex digits) raise `IntegrityError`

### Review Findings

**Code review (2026-08-23)** — 3-layer adversarial review (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against the working-tree diff, scoped to this story's files.

- [x] [Review][Patch] `Corridor` deletion is silently broken for any `Corridor` referenced by a `service_tier=troncal` `Route` — `on_delete=models.SET_NULL` conflicts with `route_corridor_required_for_troncal_only`, so Django's SET_NULL cascade raises `IntegrityError` instead of a clean `ProtectedError` [routes/models.py]. **Fixed:** changed `on_delete` to `models.PROTECT`, matching `RouteStations`' existing FK convention. Verified: `test_corridor_deletion_is_protected_when_referenced_by_a_troncal_route` confirms `ProtectedError` (not `IntegrityError`) is raised.
- [x] [Review][Patch] `RouteSchedule.day_type` has no DB-level enforcement — only Python `choices` + `full_clean()`; a raw `.save()`/`bulk_create()` (a common bulk-ingestion pattern Story 1.3 may use) bypasses validation entirely [routes/models.py]. **Fixed:** added `routeschedule_day_type_valid` `CheckConstraint` (`day_type__in=[...7 values...]`). Verified: `test_route_schedule_day_type_constraint_catches_raw_save_bypass` confirms a raw `.save()` bypassing `full_clean()` now still raises `IntegrityError`.
- [x] [Review][Patch] No constraint orders `RouteSchedule.start_time`/`end_time` — `end_time < start_time` saves silently [routes/models.py]. **Fixed:** added `routeschedule_end_after_start` `CheckConstraint` (`end_time__gt=F('start_time')`). Verified both sides: `test_route_schedule_rejects_end_time_before_start_time`, `test_route_schedule_accepts_end_time_after_start_time`.
- [x] [Review][Patch] No cross-field constraint between `Route.route_mode` and `Route.service_tier` — 21 mode×tier combinations are DB-legal though the real feed (Dev Notes §1) only produces 7 [routes/models.py]. **Fixed:** added `route_mode_service_tier_valid_combination` `CheckConstraint` enumerating exactly the 7 real pairs from the verified `agency_id` table. Verified both sides: `test_route_mode_service_tier_constraint_rejects_invalid_combination` and a 7-way parametrized `test_route_mode_tier_accepts_all_seven_valid_combinations`.
- [x] [Review][Patch] Admin forms require `BusStop.cenefa`/`.transmilenio_id`/`.numero_vagones`/`.numero_accesos`/`.biciestacion` and `Route.corridor` — all `null=True` but missing `blank=True`, so Django's auto-generated `ModelForm` marks them required, making it impossible to create most stop/route combinations through `/admin/` [routes/models.py]. **Fixed:** added `blank=True` to all 6 fields.
- [x] [Review][Patch] `BusStop` has no `Meta.ordering` (unlike `Route`) — `BusStopsListView`'s pagination over an unordered UUID-keyed queryset risks skipped/duplicated rows across pages [routes/models.py]. **Fixed:** added `ordering = ['name']` to `BusStop.Meta`, matching `Route`'s existing `ordering = ['code']` convention.
- [x] [Review][Patch] `numero_vagones`/`numero_accesos`/`biciestacion` are documented as trunk-only but not covered by `busstop_type_specific_fields_consistent` — the comment doesn't explain why (real source data has known-incomplete capacity values, per `docs/transit-data-guide.md`'s `Estaciones_Troncales` note — enforcing non-null here would break real refresh data) [routes/models.py]. **Fixed:** expanded the comment to state explicitly why these three fields are deliberately excluded from the constraint (real source data flags them incomplete) rather than tightening the constraint, which would reject legitimate refresh data.
- [x] [Review][Patch] Vestigial `{% if bus_stop.location %}` null-check in the detail template against a field that's no longer nullable (`location` is a required `PointField`) [routes/templates/routes/bus_stop_detail.html]. **Fixed:** removed the conditional, marker now always renders unconditionally.
- [x] [Review][Patch] Missing trailing newline in 2 renamed template files [routes/templates/routes/bus_stop_detail.html, routes/templates/routes/bus_stop_list.html]. **Fixed.**

- [x] [Review][Defer] `Corridor.color` has a hex-format `CheckConstraint`; the pre-existing `Route.color` field (same shape) does not — deferred, pre-existing field not introduced by this story; see `deferred-work.md` for detail.

**Dismissed (4, false positive or by-design, not defects):** migration being a fresh `0001_initial` with `dependencies=[]` (Blind Hunter lacked the context that Story 1.1 deliberately deleted the old migration history and started the database empty — this is exactly correct, not a data-loss risk); `RouteSchedule` gaining `created_at`/`updated_at` beyond the spec's minimal code block (intentional, consistent with every other model's house style); `BusStopAdmin.list_display` showing `stop_type` instead of literal `cenefa`/`gtfs_stop_id` (reasonable admin UX choice, not tied to any AC); `crawler`/`load_bus_stations.py` still referencing the removed model (already documented as a deliberate deferral in this story's own Scope Guardrails, not a new gap).

## Dev Notes

### Real-Feed Verification Findings (resolves AC #1 — the architecture's blocking verification item)

Verified directly against `data/GTFS-2026-04-29/` (`routes.txt`, `stops.txt`, `calendar.txt`, `calendar_dates.txt`, `agency.txt`, `trips.txt`) — a real, current TransMilenio GTFS static feed pulled since the architecture doc was written — cross-checked against the freshly re-pulled `data/Estaciones_Troncales_de_TRANSMILENIO.geojson` and the still-current (per its own source portal) `data/Paraderos_Zonales_del_SITP.geojson`.

**1. `service_tier`/`route_mode` sourcing** — **not** `route_desc` as the architecture guessed. The real source is `agency_id` (routes.txt) joined against `agency.txt`:

| `agency_id` | `agency_name` | route count | → `route_mode` | → `service_tier` |
|---|---|---|---|---|
| 1 | Transmilenio-Troncal | 109 | `transmilenio` | `troncal` |
| 2 | Transmilenio-Alimentadores | 158 | `transmilenio` | `alimentador` |
| 6 | Transmilenio-Dual | 26 | `transmilenio` | `dual` (new) |
| 3 | Zonal-Urbano | 717 | `transmizonal` | `urbano` |
| 4 | Zonal-Complementario | 9 | `transmizonal` | `complementario` |
| 5 | Zonal-Especial | 4 | `transmizonal` | `especial` |
| 7 | TransMiCable | 1 | `transmicable` (new) | `cable` (new) |

(GTFS's own `route_type` column is 1023× `3` [Bus] + 1× `6` [Aerial Lift, the TransMiCable route] — consistent with the above, confirms `route_type=6` as the cable signal if `gtfs_refresh.py` wants a second cross-check.)

**2. `gtfs_route_id` vs `code`** — confirmed **not equal**, exactly as the architecture warned. `route_id` (e.g. `"12238"`) is a small internal integer-string, 100% unique across all 1024 rows (verified). `code` maps to `route_short_name` (e.g. `"T40"`, `"GA547"`) — **not unique**: 252 duplicate values found (only 649 distinct codes across 1024 routes; e.g. two unrelated routes both use code `"G45"`). `route_long_name` often encodes both directions separated by `" || "` (e.g. `"A547 Centro || G547 Bosa San Diego"`).

**3. `gtfs_stop_id` vs `cenefa`/`transmilenio_id`** — confirmed via `stops.txt`'s `location_type` field, which splits stops into three real tiers the architecture's flat model didn't anticipate:
   - `location_type=1` (152 rows): trunk **stations** — `stop_id` (e.g. `"10000"`) matches the freshly re-pulled Estaciones geojson's **`cod_nodo`** field (148/150 exact match; **not** `num_est`, a different code). Use `cod_nodo` as the confirmed value for `BusStop.transmilenio_id`.
   - `location_type=0` with `parent_station` set (774 rows): individual trunk **platforms** within a station (e.g. `stop_code="B096"`, `parent_station="2000"`). GTFS `trips.txt`/`stop_times.txt` reference these platform-level IDs, not the station directly. **Design decision (applies to Story 1.3, not this story's schema):** `BusStop` rows are created at the **station** level only (`location_type=1`) — platform rows are resolved internally by `gtfs_refresh.py` (platform `stop_id` → its `parent_station` → the matching `BusStop`) when building `RouteStations`, never stored as their own `BusStop` rows. Matches UX-DR6's station-level halo-ring marker (no platform-level pins).
   - `location_type=0` with no `parent_station`, has `stop_code` (7379 rows): zonal **paraderos**. `stop_code` minus its `_TM` suffix matches `cenefa` in `Paraderos_Zonales_del_SITP.geojson` for 6924/7379 stops (93.8%) — the remainder is explained by that file's confirmed staleness (portal's own latest listing is from 2020; some paraderos have been added/renumbered since). Use `stop_code.removesuffix('_TM')` as the confirmed value for `BusStop.cenefa`.
   - `location_type=0`, no `parent_station`, **no** `stop_code` (4 rows): TransMiCable stations (e.g. `stop_id="cable_jpablo"`, `stop_name="Juan Pablo II"`, `zone_id="0"`) — no cenefa/transmilenio_id-equivalent identifier at all. `BusStop.stop_type=estacion_cable` rows leave both fields null (Task 1.4/1.6).

**4. `day_type`/calendar semantics** — the architecture's provisional 2-value guess (`L-S`/`D-F`, taken from 2 samples of the unofficial live JSON API) is **wrong**. The real `calendar.txt` currently has **7 distinct active weekday patterns**:

| `service_id` | Mon–Fri | Sat | Sun | → `day_type` |
|---|---|---|---|---|
| 1 | ✓ | | | `L-V` |
| 2 | | ✓ | | `SAB` |
| 3 | ✓ | ✓ | | `L-S` |
| 4 | | | ✓ | `DOM` |
| 5 | ✓ | | ✓ | `L-V-D` |
| 6 | | ✓ | ✓ | `SAB-DOM` |
| 7 | ✓ | ✓ | ✓ | `DIARIO` |

`calendar_dates.txt` (126 rows) uses only the two standard GTFS `exception_type` values (`1`=service added, `2`=service removed for a specific date — e.g. a holiday removing the Mon–Fri pattern and/or adding the Sunday pattern) — no unrecognized exception semantics found, so no special handling needed beyond standard GTFS precedence (an explicit date exception overrides that date's `calendar.txt` weekly pattern).

**5. Ciclovía-affected routes are already distinct GTFS routes** — the architecture assumed `ciclovia_affected` would need a hand-maintained corridor/service_tier rule (no structured source found at the time). The real feed **already encodes this**: 127 of 1024 routes (12.4%) have `"Ciclovía"` directly in `route_long_name` (e.g. `"K86 Portal Eldorado Ciclovía"`). **This simplifies Story 1.3's implementation** (a text match on the feed itself, not a maintained fixture) but does **not** change this story's schema — `ciclovia_affected` stays a plain `BooleanField(default=False)`; the derivation logic is still entirely Story 1.3's job.

**6. Corridor** — confirmed: GTFS `routes.txt` has no native corridor field at all (matches the architecture's known gap). The maintained-fixture approach stands unchanged for Story 1.3. This story only creates the empty `Corridor` table (Task 3).

**7. Candidate secondary source found (not used as system of record): `data/Servicios_(Rutas_Troncales_y_Zonales).geojson`** — a separate official dataset (last edited 2026-07-17, newer than the GTFS pull), 682 route-direction rows with real `MultiLineString` geometry and free-text hours (`hor_habil`/`hor_sab`/`hor_fest` — a 3-bucket weekday/Saturday/holiday framing, different again from GTFS's 7-value `calendar.txt` model). Its `cod_linea` overlaps GTFS `route_short_name` for only 411/542 distinct values (76%) — a partial cross-reference, not a clean natural key. Per the architecture's existing precedent for the live JSON API ("a useful cross-check... not itself the system of record — GTFS remains it"), the same treatment applies here: **this story's `day_type`/schema design stays GTFS-derived (the 7 values above), unchanged by this file.** Flagged for Story 1.3 as a possible simpler source for `Route.path` geometry than parsing `shapes.txt`+`trips.txt` — worth evaluating there, out of scope for this schema-only story.

### Model definitions (concrete, as implemented by this story)

```python
import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.urls import reverse


class BusStop(models.Model):  # renamed from BusStation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STOP_TYPE_TRUNK = 'estacion_troncal'
    STOP_TYPE_ZONAL = 'paradero_zonal'
    STOP_TYPE_CABLE = 'estacion_cable'
    STOP_TYPES = (
        (STOP_TYPE_TRUNK, 'Estación troncal'),
        (STOP_TYPE_ZONAL, 'Paradero zonal'),
        (STOP_TYPE_CABLE, 'Estación de cable'),
    )

    name = models.CharField(max_length=150)
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    gtfs_stop_id = models.CharField(max_length=50, unique=True)
    location = gis_models.PointField()
    address = models.CharField(max_length=255, default='')
    link = models.URLField(default='')

    # Zonal-only — null when stop_type != paradero_zonal
    cenefa = models.CharField(max_length=50, null=True, unique=True)
    zona_sitp = models.CharField(max_length=10, blank=True)
    audio = models.CharField(max_length=255, blank=True)

    # Trunk-only — null when stop_type != estacion_troncal
    transmilenio_id = models.IntegerField(null=True, unique=True)
    numero_vagones = models.PositiveSmallIntegerField(null=True)
    numero_accesos = models.PositiveSmallIntegerField(null=True)
    biciestacion = models.BooleanField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('routes:bus_stop_detail', args=[self.id])

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(stop_type='paradero_zonal', cenefa__isnull=False, transmilenio_id__isnull=True)
                    | models.Q(stop_type='estacion_troncal', transmilenio_id__isnull=False, cenefa__isnull=True)
                    | models.Q(stop_type='estacion_cable', cenefa__isnull=True, transmilenio_id__isnull=True)
                ),
                name='busstop_type_specific_fields_consistent',
            ),
        ]


class Corridor(models.Model):  # NEW
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    zone_letter = models.CharField(max_length=5)
    color = models.CharField(max_length=50)
    pdf_link = models.URLField(default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(color__regex=r'^#[0-9A-Fa-f]{6}$'),
                name='corridor_color_valid_hex',
            ),
        ]


class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROUTE_MODE_TRUNK = 'transmilenio'
    ROUTE_MODE_ZONAL = 'transmizonal'
    ROUTE_MODE_CABLE = 'transmicable'
    ROUTE_MODES = (
        (ROUTE_MODE_TRUNK, 'TransMilenio'),
        (ROUTE_MODE_ZONAL, 'TransMiZonal'),
        (ROUTE_MODE_CABLE, 'TransMiCable'),
    )
    SERVICE_TIER_TRUNK = 'troncal'
    SERVICE_TIER_FEEDER = 'alimentador'
    SERVICE_TIER_DUAL = 'dual'
    SERVICE_TIER_URBAN = 'urbano'
    SERVICE_TIER_COMPLEMENTARY = 'complementario'
    SERVICE_TIER_SPECIAL = 'especial'
    SERVICE_TIER_CABLE = 'cable'
    SERVICE_TIERS = (
        (SERVICE_TIER_TRUNK, 'Troncal'),
        (SERVICE_TIER_FEEDER, 'Alimentador'),
        (SERVICE_TIER_DUAL, 'Dual'),
        (SERVICE_TIER_URBAN, 'Urbano'),
        (SERVICE_TIER_COMPLEMENTARY, 'Complementario'),
        (SERVICE_TIER_SPECIAL, 'Especial'),
        (SERVICE_TIER_CABLE, 'Cable'),
    )

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    gtfs_route_id = models.CharField(max_length=50, unique=True)
    route_mode = models.CharField(max_length=20, choices=ROUTE_MODES)
    service_tier = models.CharField(max_length=20, choices=SERVICE_TIERS)
    color = models.CharField(max_length=50, default='')
    corridor = models.ForeignKey(
        'routes.Corridor', null=True, related_name='routes', on_delete=models.SET_NULL,
    )
    path = gis_models.MultiLineStringField(null=True)
    is_active = models.BooleanField(default=True)
    ciclovia_affected = models.BooleanField(default=False)

    map_link = models.URLField(default='')
    details_link = models.URLField(default='')
    publication_date = models.DateTimeField(null=True)
    last_update = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(service_tier='troncal', corridor__isnull=False)
                    | (~models.Q(service_tier='troncal') & models.Q(corridor__isnull=True))
                ),
                name='route_corridor_required_for_troncal_only',
            ),
        ]


class RouteSchedule(models.Model):  # NEW — replaces Route.schedule free-text CharField
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    DAY_TYPE_WEEKDAY = 'L-V'          # service_id 1: Mon-Fri
    DAY_TYPE_SATURDAY = 'SAB'         # service_id 2: Sat only
    DAY_TYPE_WEEKDAY_SATURDAY = 'L-S' # service_id 3: Mon-Sat
    DAY_TYPE_SUNDAY = 'DOM'           # service_id 4: Sun only
    DAY_TYPE_WEEKDAY_SUNDAY = 'L-V-D' # service_id 5: Mon-Fri + Sun (no Sat)
    DAY_TYPE_WEEKEND = 'SAB-DOM'      # service_id 6: Sat + Sun
    DAY_TYPE_DAILY = 'DIARIO'         # service_id 7: every day
    DAY_TYPES = (
        (DAY_TYPE_WEEKDAY, 'Lunes a viernes'),
        (DAY_TYPE_SATURDAY, 'Sábado'),
        (DAY_TYPE_WEEKDAY_SATURDAY, 'Lunes a sábado'),
        (DAY_TYPE_SUNDAY, 'Domingo'),
        (DAY_TYPE_WEEKDAY_SUNDAY, 'Lunes a viernes y domingo'),
        (DAY_TYPE_WEEKEND, 'Sábado y domingo'),
        (DAY_TYPE_DAILY, 'Diario'),
    )  # Confirmed against calendar.txt's 7 active service_id patterns — see
       # Real-Feed Verification Findings. Ingestion (Story 1.3) must reject
       # any future weekday combination that doesn't match one of these 7,
       # not guess the nearest bucket.

    route = models.ForeignKey('routes.Route', related_name='schedules', on_delete=models.CASCADE)
    day_type = models.CharField(max_length=10, choices=DAY_TYPES)
    start_time = models.DurationField()
    end_time = models.DurationField()


class RouteStations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    DIRECTION_1 = 1
    DIRECTION_2 = 2

    direction = models.PositiveSmallIntegerField(
        choices=((DIRECTION_1, 'Recorrido 1'), (DIRECTION_2, 'Recorrido 2')),
    )
    position = models.PositiveIntegerField()
    route = models.ForeignKey('routes.Route', related_name='route_stations', on_delete=models.PROTECT)
    bus_stop = models.ForeignKey('routes.BusStop', related_name='route_stations', on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['route', 'direction', 'position']
```

### Refinement beyond the architecture doc's sketch (flag for review)

The architecture's `Corridor` `CheckConstraint` scoped the requirement to `route_mode=transmilenio` (i.e. would also require `alimentador` and now `dual` routes to carry a corridor). Real feed data shows `alimentador`/`dual` routes don't have the same one-named-corridor identity troncal routes do (corridor is specifically the UX color system's Tier-2 concept for `service_tier=troncal`, per `relaunch-ux-design-specification.md`). This story scopes the constraint to `service_tier=troncal` instead — a correction, not a deviation from intent. Flagged here for the same reason Story 1.1 flagged its `STATIC_ROOT` fix: a real, verified difference from the written architecture, applied and documented rather than silently matched to the (looser-fitting) original wording.

### Scope guardrails — do NOT do these in this story

- **No `gtfs_refresh.py`, no data population.** This story only lands schema + migration. The database stays **empty** after `migrate` (matches Story 1.1's empty-DB-start policy) — Story 1.3's management command is the only path that populates real rows, including `Corridor` fixture data and `RouteSchedule` rows derived from `trips.txt`/`stop_times.txt`.
- **No `ciclovia_affected` derivation logic** — schema only (Task 2.5); Story 1.3 computes it.
- **No DRF, no nearby-query service, no `services.py` files** — those land with later Epic 1 stories.
- **Don't fix `crawler/pipelines.py`, `crawler/items.py`, `crawler/spiders/sitp_spider.py`, or `routes/management/commands/load_bus_stations.py`.** All four reference the pre-amendment `BusStation`/`Route.ROUTE_TYPE_*` API and will raise `ImportError`/`AttributeError` if actually invoked after this story lands. **This is safe and deliberate**, not an oversight: none of them are imported by Django's app registry, `manage.py check`, or the test suite — verified directly (`crawler/` has no `models.py`; `crawler/tests/test_utils.py` only imports from `crawler/utlis.py`, never `pipelines`/`items`; Django management commands are only imported when invoked by exact name, not during command discovery). They're dead code pending Story 1.3's `refresh_gtfs` (which supersedes `load_bus_stations.py`) and eventual `crawler/` retirement — fixing them now would be doing that story's job.
- **No DRF migration of `RouteBusesAPIView`/`RouteStationsAPIView` to real DRF generic views, and no `DIRECTION_2` fix** — both explicitly Story 2.3's job (see `relaunch-epics.md` Story 2.3 AC). This story only patches these two views' *field references* (Task 6.2) so they keep running with the renamed model — their `DetailView`-based structure and the `DIRECTION_2`-commented-out bug are untouched.

### Current-state facts that affect this story

- `routes/models.py` currently has 3 models (`Route`, `RouteStations`, `BusStation`), all integer-PK, no UUID, no PostGIS geometry fields, no `django.contrib.gis` field usage yet (Story 1.1 added the `INSTALLED_APPS` entry but no model uses it).
- `routes/migrations/` currently contains only `__init__.py` (Story 1.1, Task 6, deliberately left this way — this story generates the first real migration against it).
- `BusStation.code` (current field, `max_length=30`) is used by `routes/templates/routes/busstation_detail.html` (`Code: {{ bus_station.code }}`) and `route_detail.html` (`route_station.bus_station.code`) — both break once `code` is dropped (Task 1.5); Task 6.5/6.6 covers the template fix.
- `routes/views.py`'s `RouteStationsAPIView` currently reads `route_station.bus_station.longitude`/`.latitude` directly — the single place in active (non-crawler) code that needs the `location.x`/`.y` fix (Task 6.2).
- `data/Estaciones_Troncales_de_TRANSMILENIO.geojson` and `data/Trazados_Troncales_de_TRANSMILENIO.geojson` were freshly re-pulled (2026-08-19) and used for this story's verification. `data/Paraderos_Zonales_del_SITP.geojson` and `data/Rutas_Zonales_SITP.geojson` remain the older 2023-09-03 vintage — the zonal routes dataset's underlying source has since moved to a REST API rather than a static GeoJSON download; **out of scope for this story** (no route/stop data is populated here), relevant when Story 1.3 designs its ingestion inputs. `data/Trazados_cable.geojson` (TransMiCable line geometry) is new, not previously in the repo.
- `data/GTFS-2026-04-29/` (the real feed used for this story's verification) is a large, uncommitted local directory (`stop_times.txt` alone is ~496MB, 9.6M rows) — **not** meant to be committed to git; it's the maintainer's local downloaded-feed working copy, matching the "local file path, no automatic fetch" GTFS acquisition contract Story 1.3 implements.
- `data/Servicios_(Rutas_Troncales_y_Zonales).geojson` (new, 2026-08-19 pull) — a candidate secondary source for route geometry/hours, not used by this story; see Real-Feed Verification Findings item 7.

### Testing Standards

- `pytest` + `pytest-django` (wired in by Story 1.1) — new tests need `@pytest.mark.django_db`.
- Test file convention: `routes/tests/test_models.py` (new), matching the existing `routes/tests/test_foundation.py` precedent from Story 1.1.
- Constraint tests must exercise both the accepting and rejecting side of every `CheckConstraint` (Task 8.1) — a constraint with only a happy-path test can't prove it actually rejects bad data.

### Project Structure Notes

New files this story creates:
- `routes/migrations/0001_initial.py` (fresh, against the amended models)
- `routes/tests/test_models.py`

Renamed files:
- `routes/templates/routes/busstation_list.html` → `routes/templates/routes/bus_stop_list.html`
- `routes/templates/routes/busstation_detail.html` → `routes/templates/routes/bus_stop_detail.html`

No new Django apps — all changes stay inside the existing `routes` app, per the architecture's flat-per-domain structure.

### References

- [Source: _bmad-output/planning-artifacts/relaunch-epics.md#Story 1.2: GTFS-Ready Data Model] — story statement and original AC text
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Data Model Amendment (2026-08-17)] — full rationale for every model change, `Proposed Data Models` code sketch, the "Verification still needed" blocking note this story resolves
- [Source: data/GTFS-2026-04-29/{routes,stops,calendar,calendar_dates,agency,trips}.txt] — real feed verification performed directly for this story (2026-08-19); see Real-Feed Verification Findings above for the full analysis
- [Source: data/Estaciones_Troncales_de_TRANSMILENIO.geojson] — freshly re-pulled (2026-08-19), used to confirm `cod_nodo`↔GTFS `stop_id` mapping for trunk stations
- [Source: data/Paraderos_Zonales_del_SITP.geojson] — used to confirm `cenefa`↔GTFS `stop_code` mapping for zonal stops (93.8% match rate)
- [Source: routes/models.py, routes/views.py, routes/urls.py, routes/api_urls.py, routes/admin.py, routes/management/commands/load_bus_stations.py, routes/templates/routes/*.html, app/templates/layout/base.html] — current-state code read directly for this story to identify every reference needing a rename
- [Source: _bmad-output/implementation-artifacts/1-1-foundation-django-5-2-postgresql-postgis-upgrade.md] — previous story; empty-DB-start policy, Docker-only command execution (GDAL/GEOS), `routes/tests/` convention established there

## Change Log

- 2026-08-21: Implemented all 8 tasks. `routes/models.py` rewritten to 5 models (`BusStop`, `Route`, `Corridor`, `RouteSchedule`, `RouteStations`) with UUID PKs, the 3 CheckConstraints, and the real-feed-verified field choices from Dev Notes. Fixed a class-scoping bug found during implementation (a nested `Meta` class can't see its enclosing model class's attributes by bare name — constraints now reference literal string values instead). Generated a single fresh `0001_initial` migration, applied cleanly to the empty PostGIS database. Fixed every app-wide reference to the renamed model/fields (admin, views, urls, api_urls, templates, base nav) so the app runs end-to-end. Also updated `<int:pk>` → `<uuid:pk>` in `routes/urls.py`/`routes/api_urls.py` (a necessary consequence of the UUID PK change the task list didn't spell out as its own line item, but which the architecture doc's own Data Model Amendment explicitly calls for). Added `routes/tests/test_models.py` (23 tests) covering every constraint from both the accepting and rejecting side, UUID PK sanity, natural-key uniqueness, and the dropped-`unique_together` regression guard. Status moved to `review`.
- 2026-08-23: Code review (3-layer adversarial: Blind Hunter, Edge Case Hunter, Acceptance Auditor) found 9 patch-worthy issues and 1 deferrable inconsistency — most notably a real `Corridor` deletion foot-gun (`SET_NULL` conflicting with the troncal-corridor constraint) and admin forms silently unusable for 6 of 7 stop/route combinations (`blank=True` missing). All 9 patches applied and re-verified: regenerated a single fresh `0001_initial` (collapsing what would otherwise have been a `0002` migration, since this story hasn't shipped and the DB policy is empty-until-`refresh_gtfs`), added 12 new tests (35 total in `test_models.py`), full suite green (45 passed, same 3 pre-existing unrelated `crawler/` failures). 1 item deferred to `deferred-work.md` (retrofitting `Corridor.color`'s hex constraint onto the pre-existing `Route.color` field — needs a decision on the `default=''` case first, not caused by this story). Status moved to `done`.

### Debug Log References

- `docker compose run --rm app python manage.py makemigrations routes` — first attempt failed with `NameError: name 'SERVICE_TIER_TRUNK' is not defined` inside `Route.Meta`'s `CheckConstraint` (and the same pattern in `BusStop.Meta`) — a nested class body doesn't have implicit access to its enclosing class's names in Python, unlike nested functions. Fixed by using literal string values (`'troncal'`, `'paradero_zonal'`, etc.) directly in both constraints instead of the class-level constants; re-ran successfully.
- `docker compose run --rm app python manage.py makemigrations routes` (retry) — succeeded: single `0001_initial.py`, all 5 models, all 3 constraints present (2 embedded in `CreateModel` options, 1 as a separate `AddConstraint` due to the `Route`→`Corridor` FK dependency ordering) — inspected the generated file directly to confirm.
- `docker compose run --rm app python manage.py migrate` — applied cleanly against Story 1.1's empty PostGIS database, zero errors.
- `docker compose run --rm app python manage.py check` — no issues.
- `docker compose run --rm app python -m pytest routes/tests/test_models.py -v` — all 23 new tests passed; noticed a `RemovedInDjango60Warning` on `CheckConstraint.check` — updated all 3 constraints to the non-deprecated `condition=` kwarg (`makemigrations --check --dry-run` confirmed this required no new migration — Django serializes both forms identically).
- `docker compose run --rm app ruff check routes/` / `ruff format --check routes/` — found 5 trailing-newline issues across newly written files; fixed via `ruff check --fix` + `ruff format`. Re-ran both — clean.
- `docker compose run --rm app python -m pytest -q` (full suite) — 33 passed, 3 pre-existing failures in `crawler/tests/test_utils.py` (`parse_schedule` weekday parsing) — same 3 failures Story 1.1 already documented as out-of-scope; confirmed `crawler/` untouched by this story, not a regression.
- Manual end-to-end smoke test via `manage.py shell` + Django's test `Client`: created a temporary `Corridor`/`Route`/`BusStop`/`RouteStations` row set, hit `/`, `/bus-stops/`, `/route/<uuid>/`, `/bus-stops/<uuid>/`, and `/api/route/<uuid>/stations/` — all returned 200, including the API view's `location.x`/`.y` coordinate serialization. Deleted all rows afterward — confirmed the database is empty again (matches the empty-DB-start policy from Story 1.1; `refresh_gtfs` in Story 1.3 is the only path meant to populate real data).
- **Review-fix pass (2026-08-23):** `docker compose run --rm app python manage.py makemigrations routes` after applying all 9 patches produced a `0002_alter_...` migration (Meta/field/constraint changes) — deleted it along with the original `0001_initial.py` and regenerated a single fresh `0001_initial` instead, since this story hasn't shipped and the architecture's policy is an empty database populated only by `refresh_gtfs`. Ran `docker compose down -v` to force a genuinely fresh Postgres volume before re-migrating — necessary because Django tracks applied migrations by `(app, name)` in `django_migrations`, not file content, so simply overwriting `0001_initial.py` in place would have made `migrate` silently skip re-applying it against the already-recorded old schema. Re-ran `manage.py migrate`, `manage.py check`, `manage.py migrate --check`, the full test suite (45 passed, same 3 pre-existing `crawler/` failures), and `ruff check`/`ruff format --check` — all clean.

### Completion Notes List

- All 7 ACs implemented and verified against a running PostGIS container, not just code review — see Debug Log References above for the actual commands run.
- The real-feed verification (AC #1) was completed during story creation (see Dev Notes → Real-Feed Verification Findings) and implemented as-designed; no changes to that analysis were needed during development.
- Found and fixed one implementation-time bug not visible during story authorship: nested `Meta` classes can't reference their enclosing model's class-level constants by bare name (Python scoping, not a Django quirk) — both `CheckConstraint`s were adjusted to use literal string values.
- `<int:pk>` → `<uuid:pk>` URL converter changes in `routes/urls.py`/`routes/api_urls.py` were required (UUID PKs don't match the `int` converter at all) and applied, even though not enumerated as a separate story task — matches the architecture doc's own explicit "URL patterns move from `<int:pk>` to `<uuid:pk>`" note.
- Scope guardrails from Dev Notes were followed: no `gtfs_refresh.py`, no data population, no `ciclovia_affected` derivation logic, no DRF migration of `RouteBusesAPIView`/`RouteStationsAPIView`, no `DIRECTION_2` fix, and `crawler/`/`load_bus_stations.py` were left untouched (verified this doesn't break `manage.py check`, the test suite, or the running app).
- Database confirmed empty after all verification work — no real GTFS data was loaded by this story.
- Review-fix pass: all 9 patch findings from the 3-layer code review applied and re-verified (see Change Log); 1 finding deferred to `deferred-work.md` (pre-existing `Route.color` field, not introduced by this story).

### File List

**Added:**
- `routes/migrations/0001_initial.py` (regenerated after the review-fix pass — single fresh migration, not a `0001`+`0002` pair, per the empty-DB policy)
- `routes/tests/test_models.py` (35 tests: 23 from initial implementation + 12 added during the review-fix pass)

**Modified:**
- `routes/models.py` — full rewrite: `BusStation`→`BusStop` (+ `stop_type`, `gtfs_stop_id`, `location` PointField, dropped `code`), `Route.route_type` split into `route_mode`/`service_tier` (+ `gtfs_route_id`, `is_active`, `ciclovia_affected`, `corridor`, `path` MultiLineStringField, dropped `unique_together`), new `Corridor` and `RouteSchedule` models, `RouteStations.bus_station`→`bus_stop`; all 5 models on UUID PKs. Review-fix additions: `Route.corridor` `on_delete` SET_NULL→PROTECT + `blank=True`; new `route_mode_service_tier_valid_combination` constraint on `Route`; `RouteSchedule.Meta` added with `routeschedule_day_type_valid` + `routeschedule_end_after_start` constraints; `BusStop.Meta.ordering = ['name']`; `blank=True` added to `BusStop.cenefa`/`.transmilenio_id`/`.numero_vagones`/`.numero_accesos`/`.biciestacion`; clarifying comment on why capacity fields are excluded from the type-consistency constraint
- `routes/admin.py` — `BusStationAdmin`→`BusStopAdmin`; `RouteAdmin`/`RouteStationsAdmin` field references updated
- `routes/views.py` — `BusStationsListView`/`BusStationsDetailView`→`BusStopsListView`/`BusStopsDetailView` (explicit `template_name`); `RouteStationsAPIView` coordinate lookup updated to `location.x`/`.y`
- `routes/urls.py` — `bus_station_detail`→`bus_stop_detail`, `bus_stations_list`→`bus_stops_list`, `bus-stations/`→`bus-stops/`, `<int:pk>`→`<uuid:pk>`
- `routes/api_urls.py` — `<int:pk>`→`<uuid:pk>`
- `routes/templates/routes/home.html` — `route.get_route_type_display`→`route.get_service_tier_display`
- `routes/templates/routes/route_detail.html` — `bus_station`→`bus_stop`, dropped the `code` column
- `app/templates/layout/base.html` — nav link and label updated to bus stops
- `_bmad-output/implementation-artifacts/deferred-work.md` — added the `Route.color` deferral entry

**Renamed:**
- `routes/templates/routes/busstation_list.html` → `routes/templates/routes/bus_stop_list.html` (field references updated inside; review-fix: trailing newline added)
- `routes/templates/routes/busstation_detail.html` → `routes/templates/routes/bus_stop_detail.html` (field references updated inside; review-fix: vestigial null-check removed, trailing newline added)
