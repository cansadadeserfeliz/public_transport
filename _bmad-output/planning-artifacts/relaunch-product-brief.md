---
title: "Product Brief: public_transport"
status: "complete"
created: "2026-08-02"
updated: "2026-08-02"
inputs: ["user conversation", "codebase scan (crawler/, routes/, telegram_bot/, transmiapp/, data/)", "web research: Bogotá transit open-data landscape and competitor apps"]
---

# Product Brief: Bogotá Transit Route Guide (working title)

## Executive Summary

Bogotá's public transport network — 99 BRT trunk routes, 107 feeder routes, and 345 zonal routes, all under the TransMilenio/SITP umbrella — is too complex for most riders to hold in their heads. Existing tools only half-solve the problem: the official TransMiApp is the canonical source but not always intuitive, Moovit's crowdsourced coverage is uneven, and Google Maps has broad static coverage but weak real-time accuracy for Bogotá specifically. This project is a from-scratch relaunch of an independent, non-commercial app that helps riders — visitors, occasional users, and locals navigating an unfamiliar route alike — figure out which bus they need, see it on a clear map, and know where it actually is right now.

The original 2023 version stalled for a structural reason: it depended on scraping TransMilenio's website HTML and reverse-engineering an undocumented mobile API, both of which are fragile and broke as the source sites changed. This isn't a naive first attempt — it's a second try by someone who has already seen exactly how Bogotá transit data sources fail, and is designing around that scar tissue deliberately. The relaunch is timed well — TransMilenio now publishes official, reusable GTFS feeds on its own open-data portal under Colombia's Transparency Law, meaning the static route/station/schedule foundation no longer needs to be scraped at all. Live bus position tracking remains the one piece without an official feed, and stays the project's core differentiating bet — and its biggest open risk (see Key Risks).

## The Problem

A rider trying to get somewhere in Bogotá by bus faces two compounding problems: figuring out *which* of hundreds of routes serves their trip, and then figuring out *when* the bus will actually arrive. The scale of the system (550+ distinct routes across trunk, feeder, and zonal lines) makes the first problem genuinely hard, and zonal (SITP feeder) routes are described by riders as even more confusing than trunk routes. The second problem is worse: no product serving Bogotá today reliably shows *where a bus currently is*. The official app is the source of truth for schedule/service changes but isn't built around effortless route discovery. Moovit fills gaps with crowdsourced data of inconsistent quality. Google Maps ingests public GTFS well but is openly weak on Bogotá real-time. Riders today stitch together partial answers from multiple apps, or simply learn their one habitual route and avoid anything unfamiliar — a real cost for visitors, new residents, and anyone whose usual route gets restructured (which happens multiple times a year as the system evolves).

## The Solution

A web app that presents Bogotá's bus network the way a knowledgeable local friend would explain it: a clean, map-first view of routes and stations built on TransMilenio's official GTFS data, in plain language rather than raw operator codes and jargon, with live bus positions layered on top so a rider can see not just *that* a route exists but *where their bus is right now*. The static foundation (routes, stations, ordered stops, schedules) comes from official open data through a refresh pipeline that stays current as the system restructures — not a one-time import — replacing the fragile HTML-scraping approach that broke last time. Live tracking, which has no official feed, is treated as its own contained, monitored component so its inherent fragility doesn't take down the rest of the app when it breaks.

The real usage moment this is designed for is physical: someone standing at a stop, phone in hand, often on a mid-range Android device and sometimes with weak signal inside an enclosed BRT station. That means mobile-first, fast-loading, low-data-friendly design isn't a nice-to-have — it's the difference between the app working at the one moment it needs to. A shareable link to a specific route (the kind of thing a friend texts another friend) is treated as a first-class, low-effort growth path, since it maps directly onto how the primary success bar — friends and family actually using it — is likely to happen in practice.

## What Makes This Different

This isn't a commercial play, so the goal isn't a defensible moat — it's real value delivered honestly and sustainably. Three things distinguish this from what exists:

- **A stable data foundation.** Building on official, Transparency-Law-licensed GTFS data is a genuine strategic shift from 2023 and from what most small third-party efforts do — it means route and schedule accuracy isn't held hostage to an unmonitored scraper silently breaking. (Whether that GTFS feed's zonal-route coverage is as complete as its trunk-route coverage is still unverified — see Key Risks.)
- **Real-time position as the headline feature.** This is exactly the gap every competitor (official and third-party) leaves partially unfilled for Bogotá. It's also the riskiest part of the build, since it still depends on scraping or reverse-engineering an unofficial source — that trade-off is made deliberately, not accidentally.
- **No ads, no data harvesting, no commercial incentive.** In a landscape where the crowdsourced alternative is ad-supported, this is a plain, immediately legible trust signal for any rider, not just a footnote for the technically minded.

The product's voice matters too: "explained like a knowledgeable local friend" instead of TransMiApp's official/bureaucratic tone is a deliberate, sustained design principle, not just an opening line — it's also what makes the product naturally accessible to visitors and non-Spanish-fluent newcomers without extra design work.

## Who This Serves

**Primary: everyday Bogotá TransMilenio/SITP riders navigating an unfamiliar route** — someone taking a route they don't take daily, whether that's a visitor, a new resident, someone whose regular route just got restructured, or a regular commuter making an unusual trip. Their moment of need is standing at a stop (or before leaving home) asking "which bus, and is it close?" — and the "aha" is seeing their route laid out clearly on a map with a bus actually approaching, instead of guessing or bouncing between apps.

The first concrete success bar is intentionally close to home: the developer's own friends and family adopting it for real trips. That's a meaningful, honest measure of whether the product actually works for the person it's built for, before any broader ambition is layered on.

## Success Criteria

Given this is a solo, nights-and-weekends effort, success is measured in adoption and reliability, not commercial metrics:

- **Real adoption**: people the developer knows use it for actual trips, unprompted, more than once — tracked informally (direct check-ins) rather than through analytics that would undercut the "no data harvesting" principle.
- **Data currency**: the GTFS refresh pipeline keeps routes/stations/schedules current through at least one real TransMilenio route restructuring without manual intervention.
- **Live tracking actually works**: bus positions are visibly accurate and available for at least the busiest trunk (BRT) routes, without silent, unnoticed outages.
- **It doesn't die the way v1 did**: baseline engineering health (tests around the data pipeline especially, CI, monitoring for the scraper/live-tracking source breaking) so a future site change is caught, not discovered months later by silence.

## Scope

**In for v1:**
- Web app, map-first route and station browsing built on official GTFS static data
- A GTFS refresh pipeline (not a one-time import) that tolerates upstream schedule/route changes
- Live bus position tracking for at least trunk (BRT) routes
- Clean, plain-language route search/browse — "find the route for my trip," not just a route list
- Baseline engineering modernization: current Django/Python, containerized (Docker) local dev, a database choice suited to geospatial + refresh-pipeline needs, real test coverage

**Explicitly out for v1:**
- Reviving the Telegram bot (real candidate for phase 2, not v1 — it's currently a non-functional stub)
- Real-time coverage of all 345 zonal routes (start with trunk/BRT, expand deliberately)
- Any official partnership, licensing conversation, or commercial ambition
- Native mobile app
- Trip planning / multi-leg journey routing (route discovery and live position first; full itinerary planning is a bigger, separate problem)

## Key Risks

- **Live tracking depends on an unofficial source, again — confirmed, not just assumed.** TransMilenio's own GIS portal advertises a GTFS-Realtime page (`gis.transmilenio.gov.co/gtfs/`, vehicle positions/trip updates/service alerts as `.pb` feeds), but as of this research all three endpoints return HTTP 404 and the page itself appears to have been dead since at least 2021 (no newer Wayback Machine snapshot, visibly outdated template). There is no working official real-time feed today. Continuing to rely on the unofficial TransmiApp backend (as the current codebase already does, at `transmiapp/services.py`) is a deliberate, informed trade-off, not a gap to research further — worth a periodic recheck of the official endpoint in case it's ever revived, but not worth blocking on. Mitigation: treat the unofficial source as expected-to-break rather than exceptional — design the UI to degrade gracefully (clearly show "position unavailable" rather than stale or wrong data) instead of assuming resilience by isolation alone.
- **Unverified GTFS completeness.** It's not yet confirmed that TransMilenio's official GTFS feed covers zonal/feeder routes as thoroughly as trunk routes. Worth a quick validation spike early, since it directly affects whether the "stable foundation" claim holds for the whole network or just the BRT trunk.
- **Solo bus-factor.** Detection (CI, monitoring) isn't repair — a nights-and-weekends solo maintainer may not fix breakage quickly even with good alerting. Scope is sized to stay shippable at that pace deliberately (see Scope), but this remains the project's most likely failure mode if life gets busy.
- **Running costs aren't bounded yet.** Map tiles, a geospatial database, and any live-tracking infrastructure carry ongoing hosting costs for a project with no revenue. Worth setting an explicit budget ceiling (e.g., stay within free tiers) before infrastructure choices lock it in.

## Vision

In two to three years, if this works, it's the thing the developer's circle actually reaches for when navigating Bogotá by bus — reliable enough that "just check the app" is the default answer to "how do I get there." The Telegram bot returns as a lightweight companion to the web app. Real-time coverage expands past trunk routes into the busier zonal lines. And because the hardest part — a resilient, self-healing GTFS refresh pipeline — was solved once, it becomes reusable groundwork rather than a one-off, whether that means open-sourcing it for other Colombian cities' transit data, becoming a small piece of Bogotá's civic-tech/open-data ecosystem, or simply never having to relive the "the source changed and everything silently broke" failure mode that ended v1.

## Sources

- Route counts (99 BRT, 107 feeder, 345 zonal, 2024): [Integrated Public Transport System (Bogotá) — Wikipedia](https://en.wikipedia.org/wiki/Integrated_Public_Transport_System_(Bogot%C3%A1)), citing TransMilenio's December 2024 statistics.
- Transparency Law basis for open-data reuse: [Ley 1712 de 2014 — Función Pública (official text)](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=56882); TransMilenio's own confirmation it publishes under this law for commercial/non-commercial reuse: [Consulta toda la oferta de datos abiertos de TRANSMILENIO](https://www.transmilenio.gov.co/publicaciones/151922/consulta-toda-la-oferta-de-datos-abiertos-de-transmilenio/).
- 2026 unified fare ($3,550 COP): [Infobae, 2026-01-09](https://www.infobae.com/colombia/2026/01/09/confirmado-el-pasaje-de-transmilenio-sube-350-en-2026-y-queda-en-3550-para-servicios-zonales-y-troncales/); official: [TransMilenio — Abecé Ajuste Tarifario 2026](https://www.transmilenio.gov.co/comunicaciones/noticias-de-transmilenio/comunicados-oficiales/abece-ajuste-tarifario-2026).
- Official static GTFS feeds and open-data portal: [Portal de Datos Abiertos de TransMilenio (ArcGIS Hub)](https://datosabiertos-transmilenio.hub.arcgis.com/); [Datos Abiertos Bogotá — SITP](https://datosabiertos.bogota.gov.co/dataset/?tags=SITP).
- GTFS-Realtime confirmed dead: directly tested 2026-08-02 at `gis.transmilenio.gov.co/gtfs/{vehiclepos,serviceAlerts,tripupdate}.pb` (all HTTP 404); page itself has no Wayback Machine snapshot newer than January 2021 ([archived Jan 2021 version](http://web.archive.org/web/20210126145051/https://gis.transmilenio.gov.co/gtfs/)) — verifiable by re-running the same check.
- Competitor landscape (Moovit, Google Maps, TransMiApp gaps): [Unstar.app — Transit apps comparison, 2026](https://unstar.app/blog/transit-citymapper-moovit-google-maps-trainline-public-transit-apps-ranked-2026).
- System restructuring / TransMiZonal rollout: [TransMilenio — Nuevas rutas de TransMiZonal](https://www.transmilenio.gov.co/comunicaciones/noticias-de-transmilenio/comunicados-oficiales/nuevas-rutas-de-transmizonal-conectan-bosa-con-el-portal-americas).
- TransMiCable Oct 2025 closure: [Cronista — Cierre del TransMiCable](https://www.cronista.com/colombia/actualidad-co/cierre-del-transmicable-transmilenio-activa-nuevas-rutas-de-transporte-y-canales-digitales-para-viajar-mas-facil/).
- Operational "crisis" framing / PQRS complaints: [El Tiempo — TransMilenio: preguntas y respuestas para entender su crisis](https://www.eltiempo.com/bogota/transmilenio-preguntas-y-respuestas-para-entender-su-crisis-73944).
