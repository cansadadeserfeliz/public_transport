# TransMilenio & SITP Data Guide

A map of what's in `data/`, what each file actually means in the real TM/SITP system, and how the files connect to each other. Written for navigating the domain, not as an implementation spec — for that, see `_bmad-output/implementation-artifacts/1-2-gtfs-ready-data-model.md`, which cites this research directly.

All findings below were verified empirically against the files in `data/` on 2026-08-19 (counts, joins, and match rates are real numbers from those files, not assumptions).

---

## 1. The system, in plain terms

**SITP** (Sistema Integrado de Transporte Público) is Bogotá's whole integrated bus system. **TransMilenio** is the trunk/BRT operator — one part of SITP, not a synonym for it. Within SITP, every route belongs to one of these families:

| Family | What it is | Where it runs |
|---|---|---|
| **Troncal** | Trunk/BRT — the red articulated buses everyone calls "TransMilenio" | Exclusive busway corridors, station-to-station |
| **Alimentador** (feeder) | Connects neighborhoods to trunk portals/stations, one integrated fare | Regular streets, feeding into the trunk network |
| **Dual** | Hybrid: part of the route runs on the exclusive busway, part on regular streets | Both — a real, distinct category (see §5) |
| **Urbano** | Zonal service crossing multiple zones on main roads (blue buses) | Regular streets |
| **Complementario** | Zonal service operating within a single zone only | Regular streets |
| **Especial** | Special-purpose zonal service | Regular streets |
| **TransMiCable** | Aerial cable car, same integrated fare, physically separate infrastructure | Cable line over Ciudad Bolívar |

"Zonal" as a catch-all term covers Alimentador/Urbano/Complementario/Especial — anything that isn't on the exclusive busway. Dual and TransMiCable don't fit the old troncal-vs-zonal binary at all; they were the two real surprises this research turned up (see §5).

---

## 2. Three kinds of physical stops

The data distinguishes three genuinely different kinds of infrastructure, not two:

1. **Estación troncal** (trunk station) — the big platform structures on the busway (Alcalá, Portal Norte, etc.). ~150 of them. Each station is actually a small hierarchy: the station itself, plus individual **boarding platforms** inside it that specific routes stop at. The data model treats the station as the unit riders see; platforms are an internal ingestion detail (see §4).
2. **Paradero zonal** — an ordinary curbside stop with a pole/sign, identified by a **cenefa** code (e.g. `001A00`). ~7,600–7,900 of them, by far the majority of stops in the system.
3. **Estación de cable** — TransMiCable's 4 stations. Structurally distinct from both of the above; carries none of the trunk-station or paradero-specific attributes.

---

## 3. Data source inventory

### `data/GTFS-2026-04-29/` — the official GTFS static feed (system of record)

A real, standard GTFS feed downloaded from TransMilenio's open-data portal (ArcGIS Hub, `datosabiertos-transmilenio.hub.arcgis.com`, published as a new dated release roughly quarterly). This is the authoritative source — everything else in `data/` is a cross-check or supplementary source, never a substitute for it.

| File | Rows | What it holds |
|---|---|---|
| `agency.txt` | 7 | The 7 operating entities — this is the real source for route family (§5), not a route-text field |
| `routes.txt` | 1,024 | One row per route: id, short/long name, color, agency, GTFS `route_type` |
| `stops.txt` | 8,309 | Every stop/station/platform, with `location_type` distinguishing the tiers in §2 |
| `trips.txt` | 181,544 | Individual scheduled trips, linking a route to a service pattern and a shape |
| `stop_times.txt` | 9,600,553 | Per-trip, per-stop arrival/departure times — this is where actual schedules live (huge; not meant to be read whole) |
| `shapes.txt` | 941,753 pts | Route geometry (the physical path each shape follows) |
| `calendar.txt` | 7 | The weekly service patterns in current use (§6) |
| `calendar_dates.txt` | 126 | Dated exceptions to those patterns (holidays: service added/removed for a specific date) |
| `frequencies.txt` | 15 | Headway-based scheduling — only used for TransMiCable trips in the current feed; everything else is scheduled via explicit `stop_times.txt` rows |
| `fare_attributes.txt` | 1 | A single fare definition (TransMiCable's, `$3,550 COP`) |
| `feed_info.txt` | 1 | Feed metadata: publisher, version, valid date range (2026-01-01 to 2026-12-31) |

**Note:** this whole directory is a local, uncommitted working copy (`stop_times.txt` alone is ~496 MB) — it's not meant to go into git. It's exactly the kind of maintainer-downloaded archive the refresh pipeline is designed to read from a local path.

### GeoJSON files — Bogotá open-data portal exports (supplementary / cross-check sources)

| File | Rows | Freshness | What it holds | Role |
|---|---|---|---|---|
| `Estaciones_Troncales_de_TRANSMILENIO.geojson` | 150 | Fresh (2026-08-19 pull) | Trunk station points, with platform counts, bike-parking, node code (`cod_nodo`) | Confirms `cod_nodo` ↔ GTFS `stop_id` for stations (§4) |
| `Trazados_Troncales_de_TRANSMILENIO.geojson` | 20 | Fresh (2026-08-19 pull) | Trunk corridor line geometry, one row per named corridor (e.g. "Autopista Norte", zone letter `B`) | Candidate source for `Corridor` data — GTFS itself has no corridor concept |
| `Trazados_cable.geojson` | 3 | Fresh (2026-08-19 pull) | TransMiCable line segments | New in the repo — first time cable data has been pulled |
| `Servicios_(Rutas_Troncales_y_Zonales).geojson` | 682 | Very fresh (portal-side last edit 2026-07-17) | Route-direction geometry **plus free-text hours** (`hor_habil`/`hor_sab`/`hor_fest` — weekday/Saturday/holiday) | Candidate source for route geometry, simpler to parse than GTFS `shapes.txt`+`trips.txt`. Its `cod_linea` overlaps GTFS `route_short_name` for only 76% of values — a cross-check, not a clean join |
| `Paraderos_Zonales_del_SITP.geojson` | 7,623 | Stale — portal's own listing dates to 2020 | Zonal stop points with `cenefa`, address, audio-announcement text | Confirms `cenefa` ↔ GTFS `stop_code` for ~94% of zonal stops (§4). No newer version exists to pull — this appears to be the ceiling on paradero data freshness |
| `Rutas_Zonales_SITP.geojson` | 838 | Stale (2023-09-03) | Zonal route lines with a `tipo_operacion` day-type field (e.g. `"DOM-FEST"`) | Superseded — the portal now serves this dataset as a REST API instead of a static download; this file is a leftover snapshot, not actively used |

---

## 4. How the sources connect: the natural-key map

This is the part that isn't obvious from any single file — each dataset uses its *own* identifier scheme, and only some of them line up.

```
                    GTFS stops.txt (location_type)
                    ┌─────────────┬─────────────────┬──────────────────┐
                    │ =1 (station)│ =0, has parent  │ =0, no parent    │
                    │             │ (platform)      │                  │
                    ▼             ▼                 ▼
              stop_id "10000"  stop_id "61235"   stop_id "51975"
              152 rows         774 rows           has stop_code "_TM"
                    │                              7379 rows
                    │ matches (148/150)                  │ matches, minus
                    ▼                                     │ "_TM" suffix
        Estaciones_Troncales.geojson                     │ (6924/7379, 94%)
          cod_nodo (int, e.g. 7103)                       ▼
                                                Paraderos_Zonales.geojson
                                                     cenefa (e.g. "001A00")

              stop_id "cable_jpablo" (no parent, no stop_code, 4 rows)
              → TransMiCable stations, no cross-reference dataset exists
```

Concretely:

- **Trunk stations**: GTFS `stop_id` (e.g. `"10000"`) = Estaciones geojson's `cod_nodo` field (verified match on 148 of 150 stations). **Not** `num_est`, which is a different, unrelated code on the same rows — easy to grab the wrong field here.
- **Trunk platforms**: `stop_id`s with a `parent_station` pointing back to a station's `stop_id`. These are what `trips.txt`/`stop_times.txt` actually reference when a route visits a station — the station-level `stop_id` itself never appears directly in a trip's stop sequence. Any code that walks a trip's stops needs to resolve platform → parent station.
- **Zonal paraderos**: GTFS `stop_code` (e.g. `"513A09_TM"`) with the `_TM` suffix stripped = `cenefa` in the Paraderos geojson (e.g. `"513A09"`). Match rate is 94%, not 100% — the remaining 6% is explained by the paraderos file's staleness (new/renumbered stops since 2020 that the GTFS feed knows about and the geojson doesn't).
- **TransMiCable stations**: no cross-reference source exists at all. GTFS is the only place these 4 stations are described.
- **Routes**: GTFS `route_id` (e.g. `"12238"`) is the only reliable unique identifier — confirmed unique across all 1,024 routes. `route_short_name` (the rider-facing code, e.g. `"T40"`) is **not** unique on its own (252 duplicate values found — two different real routes can share a code). `Servicios_(Rutas_Troncales_y_Zonales).geojson`'s `cod_linea` cross-references `route_short_name` for about three-quarters of routes, useful as a sanity check but not as a join key.

---

## 5. Route classification: what `agency_id` actually tells you

The clean, verified way to classify any route is its GTFS `agency_id` (joined against `agency.txt`) — **not** any text-parsing of the route's name or description, which was the earlier (wrong) assumption.

| `agency_id` | Agency name | Routes | Family |
|---|---|---|---|
| 1 | Transmilenio-Troncal | 109 | Trunk |
| 2 | Transmilenio-Alimentadores | 158 | Feeder |
| 6 | **Transmilenio-Dual** | 26 | Hybrid trunk/feeder |
| 3 | Zonal-Urbano | 717 | Zonal, cross-zone |
| 4 | Zonal-Complementario | 9 | Zonal, single-zone |
| 5 | Zonal-Especial | 4 | Zonal, special |
| 7 | **TransMiCable** | 1 | Cable car |

The two bolded rows are the real discoveries from this research — neither "Dual" nor "TransMiCable" appear anywhere in the original data-model planning, because nobody had looked at a real feed yet:

- **Dual routes** (e.g. code `"M86-K86"`) genuinely run part of their trip on the exclusive busway and part on regular streets — TransMilenio's own agency naming (`Transmilenio-Dual`) treats them as a real third category, not a data artifact.
- **TransMiCable** is its own GTFS `route_type` (`6` — "Aerial Lift, Suspended Cable Car" in the GTFS spec, vs. `3` — "Bus" for everything else). One route, four stations, its own fare (`$3,550 COP` — see `fare_attributes.txt`), scheduled by headway (`frequencies.txt`) rather than explicit stop times like the rest of the system.

---

## 6. Schedule model: what "day type" really means here

Before this research, the working assumption (from a secondary live API, not GTFS itself) was that every route's schedule fell into one of two buckets: weekday-ish (`L-S`, "Lunes a Sábado") or weekend-ish (`D-F`, "Domingos y Festivos"). The real `calendar.txt` shows **7 distinct weekly patterns** actually in use:

| Pattern | Mon–Fri | Sat | Sun | Meaning |
|---|:---:|:---:|:---:|---|
| `L-V` | ✓ | | | Weekdays only |
| `SAB` | | ✓ | | Saturday only |
| `L-S` | ✓ | ✓ | | Weekdays + Saturday |
| `DOM` | | | ✓ | Sunday only |
| `L-V-D` | ✓ | | ✓ | Weekdays + Sunday, **no Saturday** — an unusual but real combination |
| `SAB-DOM` | | ✓ | ✓ | Weekend only |
| `DIARIO` | ✓ | ✓ | ✓ | Every day |

On top of the weekly pattern, `calendar_dates.txt` carries 126 dated exceptions — holidays where a specific date's service is explicitly added or removed, overriding that date's weekly pattern. This is standard GTFS behavior, nothing unusual found there.

Separately, `Servicios_(Rutas_Troncales_y_Zonales).geojson` describes hours using yet a *third* framing — three free-text fields, `hor_habil` (weekday), `hor_sab` (Saturday), `hor_fest` (holiday) — which doesn't map cleanly onto the 7-pattern GTFS model above. Worth knowing about if cross-referencing schedules by hand, but GTFS is the system of record.

---

## 7. Known gaps and staleness, at a glance

- **Paraderos zonal data cannot get any fresher** — the source portal itself only has a 2020 dataset. The 94% GTFS cross-match is the best available confidence check.
- **`Rutas_Zonales_SITP.geojson` is a dead end** — its source has moved to a REST API; the file in the repo is a static 2023 snapshot, not being refreshed.
- **No corridor data in GTFS at all** — `Trazados_Troncales_de_TRANSMILENIO.geojson`'s 20 named corridors are the best available source for that concept; it has to be maintained separately from whatever GTFS provides.
- **TransMiCable has no cross-reference dataset** — GTFS is the only description of its 4 stations and 1 route that exists in `data/`.
- **`Servicios_(Rutas_Troncales_y_Zonales).geojson`'s route-code overlap with GTFS is partial (76%)** — treat it as a secondary check, not a join key.

---

## 8. Glossary

| Term | Meaning |
|---|---|
| SITP | Sistema Integrado de Transporte Público — the whole integrated system; TransMilenio is one part of it |
| Troncal | Trunk/BRT service on the exclusive busway; also the name for a corridor grouping itself (e.g. "Calle 26") |
| Zonal | Non-trunk service on regular streets — covers Alimentador/Urbano/Complementario/Especial |
| Alimentador | Feeder route connecting neighborhoods to trunk portals/stations |
| Dual | Hybrid route, partly on the busway and partly on regular streets (agency `Transmilenio-Dual`) |
| Estación | Trunk station — the larger platform infrastructure |
| Paradero | Zonal stop — a simple curbside stop, identified by its cenefa |
| Cenefa | SITP's official alphanumeric code for a paradero (e.g. `001A00`) |
| Cod_nodo | The node code used for trunk stations in the Bogotá open-data GeoJSON exports — matches GTFS `stop_id` for stations |
| GTFS | General Transit Feed Specification — the standard format the official static feed is published in |
| `service_id` | GTFS's internal key for a weekly schedule pattern (see §6) |