---
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-public_transport.md
  - _bmad-output/planning-artifacts/product-brief-public_transport-distillate.md
  - _bmad-output/project-context.md
workflowType: 'prd'
classification:
  projectType: web_app
  domain: general
  complexity: medium
  complexityNote: "Elevated from low — driven by technical complexity of the live bus-position dependency and recurring GTFS refresh pipeline, and legal/ToS exposure of the unofficial live-tracking API, not by domain regulation."
  projectContext: brownfield
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
---

# Product Requirements Document - public_transport

**Author:** Vera
**Date:** 2026-08-02

## Executive Summary

public_transport is a relaunch of a dormant 2023 solo project: a web app that helps Bogotá TransMilenio/SITP riders navigate a 550+ route bus network by showing every route and stop relevant to where they are — not one route at a time, the way TransMiApp, Moovit, and Google Maps do — so riders can compare live options themselves and decide which stop to walk to. The primary user is the developer's own circle of friends and family, standing at a stop or about to leave home, who currently get lost in a system too large to hold in their heads and are underserved by tools that force route-by-route lookup and mental cross-referencing. The deeper goal is not to make riders dependent on the app for every trip, but to help them build lasting knowledge of their own neighborhood's routes — freeing them from needing a live connection or an open app every time, in deliberate contrast to engagement-optimized transit apps.

### What Makes This Special

Three things distinguish this build: (1) a geography-first, multi-route comparison view — see all routes and stops near you at once, not a single-route lookup — validated by proven patterns in Citymapper's "Nearby" tab and 9292's "stops nearby" planner; (2) live bus position layered on an official, Transparency-Law-licensed GTFS static foundation, replacing the fragile HTML-scraping that killed v1 in 2023; (3) a design goal of teaching riders their own routes — extending to an offline-friendly, zone-scoped printable map — rather than maximizing app engagement, a direct extension of the project's no-ads, no-data-harvesting, non-commercial stance. Core insight: this is a second attempt by someone who has already watched this exact class of app fail from an unmonitored scraper breaking silently, and is building deliberately around that failure mode rather than repeating it.

## Project Classification

**Project Type:** Web app (map-first, browser-based, no native/mobile app for v1)
**Domain:** General, no regulatory domain — complexity rated **medium**, driven by technical factors (live-position dependency on an undocumented, ToS-fragile third-party API; a GTFS refresh pipeline that must tolerate ongoing route restructuring) rather than domain regulation.
**Project Context:** Brownfield — rebuilding on an existing Django 4.2.4/SQLite/Scrapy codebase dormant since September 2023, with planned technical modernization (current Python/Django versions, Docker, a geospatial-capable database, real test coverage, near-zero-cost mapping).

## Success Criteria

### User Success

- A rider at an unfamiliar stop, or about to leave home, opens the app and within seconds sees every relevant route/stop nearby with live position — no route-by-route lookup, no mental cross-referencing.
- After repeated use for their own neighborhood, a rider self-reports they stopped needing to open the app for routes they now know — the "teach, don't create dependency" goal made observable, tracked informally (a check-in conversation, not analytics).
- The developer's own friends/family circle uses the app unprompted for real trips, more than once.
- Early validation already exists: showing the concept to a stranger at a bus stop who asked for directions was enough to solve their problem on the spot — real-world evidence the core value proposition works, ahead of any formal build.

### Business Success

Reframed as **Project Sustainability Success** (no revenue target — non-commercial solo project):
- Runs within a defined near-zero-cost ceiling (map tiles, hosting, geospatial DB) indefinitely, without becoming a financial burden.
- Doesn't die the way v1 did: tests around the data pipeline, CI, and monitoring on the scraper/live-tracking source so a future breakage is caught, not discovered months later by silence.

### Technical Success

- Static data (routes, stops, schedules) is stored and indexed for fast nearby-route/stop queries — this is the part fully within project control, so it's held to a real engineering bar (e.g., spatial indexing via a geospatial-capable database) rather than left vague.
- Live bus position latency is explicitly not held to a bar — it depends on an upstream, unofficial third-party API outside the project's control. Per the brief's existing mitigation, the UI should degrade gracefully (show "position unavailable" rather than stale/wrong data) instead of chasing a latency target that isn't achievable.
- GTFS refresh pipeline stays current through at least one real TransMilenio route restructuring, unattended.
- Live bus position visibly accurate for at least the busiest trunk (BRT) routes, no silent outages.

### Measurable Outcomes

Deliberately qualitative, consistent with the "no data harvesting" principle — adoption tracked via direct check-ins, not analytics. No numeric target set. The bus-stop stranger anecdote above stands as the first concrete data point.

## Product Scope & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP — prove the core loop (see all nearby routes/stops at once, compare live, decide where to walk) actually works for real people, not a revenue or platform MVP. Already informally validated once (the bus-stop stranger).
**Resource Requirements:** Solo developer, nights-and-weekends, existing Python/Django background — no team, no external contributors assumed.

### MVP (Phase 1)

**Core user journeys supported:** Journey 1 (Camila — already at a stop) and Journey 2 (Andrés — deciding which stop to walk to).

**Must-have capabilities:**
- Web app, map-first
- GTFS refresh pipeline (not one-time import), with static data optimized/indexed for fast nearby queries
- Live BRT tracking, degrading gracefully when the upstream source is unavailable
- Nearby-routes/stops comparison view — both flows (already-at-a-stop, about-to-leave-home) — the core differentiator
- Spanish-only UI, non-affiliation disclaimer, open-data attribution
- Engineering modernization (current Django/Python, Docker, geospatial DB, real test coverage, near-zero-cost mapping)

### Growth Features (Phase 2, Post-MVP)

- Zone/neighborhood-scoped printable map
- Real-time expansion beyond trunk into busier zonal routes
- Telegram bot revival

### Vision (Phase 3, Future)

- Open-sourcing the refresh pipeline for reuse (other Colombian cities, civic-tech)
- Broader printable reference, if a citywide or larger-zone version proves feasible

### Risk Mitigation Strategy

**Technical risk:** the two hardest things are (1) the unofficial live-tracking API, mitigated by graceful degradation and monitoring, and (2) making the nearby-routes comparison query fast against ~550 system-wide routes. Simplification: index and query only trunk/BRT stops and routes for the nearby view at MVP — the same subset live tracking already covers — expandable later alongside zonal real-time in Phase 2.

**Market/adoption risk:** the real risk isn't "will anyone want this" — that's already been shown true once. It's whether the developer's circle adopts it repeatedly, not just out of curiosity. Mitigation: informal check-ins double as both measurement and a nudge to keep using it.

**Resource risk:** solo, nights-and-weekends is the binding constraint, and MVP is already sized for it. Explicit fallback: if live bus tracking integration proves harder than expected, the nearby-routes/stops comparison view alone (without live position) is still a viable interim MVP slice — it still solves Andrés's problem and de-risks the launch timeline from the single hardest dependency.

## User Journeys

### Journey 1: Primary User — Success Path ("Already at the stop")

**Camila**, a new resident who moved to Bogotá three months ago, is standing at a bus stop on Av. Boyacá she's never used before, heading to a friend's place across town. She doesn't know which of the several routes passing this stop actually gets her there, or whether a bus is even close.

She opens the app. Instead of typing a route number she doesn't know, she sees a map centered on where she's standing, with every route that passes this stop laid out at once — no jargon, plain Spanish labels. One route has a bus icon three minutes out. She taps it, confirms the direction matches where she's going, and gets on.

**Climax:** the moment she sees a live bus icon actually approaching *her* stop, on *her* route, without having looked anything up beyond "what's near me."

**Resolution:** She makes the trip without asking anyone, without switching apps. Next time she's at a stop she doesn't recognize, she already knows to check the app first.

**Reveals requirements for:** geolocation-anchored nearby-stop query, multi-route rendering on one map, live position overlay, plain-language (Spanish) route labeling.

### Journey 2: Primary User — Edge Case ("Leaving home, choosing a stop")

**Andrés** has taken the same route to work for two years. This week, TransMilenio restructured it — his usual stop no longer serves the route he needs. He's about to leave his apartment near Av. Villas and Calle 127, and he's not sure whether to walk to Av. Villas, Av. Boyacá, or Calle 127 to catch something useful. Google Maps' suggestion last time sent him somewhere clearly wrong for how the local network actually works, so he doesn't trust it anymore.

He opens the app before leaving. It shows all three nearby streets' stops and their routes side by side, with live positions where available. He compares: Av. Boyacá has a bus 4 minutes out on a route that gets him closer; the others don't have anything imminent. He decides for himself, walks there, catches it.

**Climax:** the moment he realizes he can *evaluate the options himself* instead of trusting an algorithm's single answer — and that the answer is visibly better than what Google Maps gave him.

**Resolution:** Over the following weeks, Andrés stops checking the app for this decision — he's learned the pattern for his own neighborhood. He only opens it now when he's somewhere unfamiliar.

**Reveals requirements for:** multi-stop comparison within walking range (not just nearest stop), route/stop data dense enough to compare meaningfully, a UI that supports self-directed comparison rather than a single "best route" recommendation.

### Journey 3: Maintainer/Ops User (you)

It's a Sunday night. The unofficial live-tracking API — the one thing outside your control — has silently changed its response format. Because there's monitoring on it (not just hope), you get an alert instead of finding out three weeks later from a friend saying "the bus icons disappeared."

You check the dashboard/logs, confirm it's the upstream source and not your code, and the app has already degraded gracefully in the meantime — showing "position unavailable" instead of stale or wrong bus locations, so nobody was misled while you fix it.

**Climax:** the failure is caught by monitoring within hours, not discovered by silence months later — the exact failure mode that killed v1.

**Resolution:** You fix or adapt to the upstream change on your own schedule, without the static route/schedule data ever being at risk, because that part runs on the independent, monitored refresh pipeline.

**Reveals requirements for:** monitoring/alerting on the live-tracking source and refresh pipeline, graceful UI degradation when live data is unavailable, separation between static-data reliability and live-data fragility (already named as a mitigation in the brief).

### Journey Requirements Summary

- Geolocation-anchored, multi-route "nearby" query (not single-route lookup) — core to Journeys 1 & 2
- Side-by-side comparison across multiple nearby stops, including live position where available — core to Journey 2
- Plain-language route/stop labeling, no operator jargon — Journey 1
- Live position overlay with graceful "unavailable" state, not stale/wrong data — Journeys 1 & 3
- Monitoring/alerting on both the refresh pipeline and the live-tracking source — Journey 3
- Fast, indexed static-data queries (from Step 3's technical success criteria) — underpins the "seconds, not lookups" experience in Journeys 1 & 2
- **UI language: Spanish only for v1 (confirmed).** Resolves an open question flagged during the product brief's research phase (Spanish was assumed but never confirmed) — no English/bilingual requirement for launch.

## Domain-Specific Requirements

Domain is `general` (no regulated industry); complexity was elevated to medium for technical and legal-exposure reasons specific to this project, not domain regulation. The standard compliance/certification version of this step doesn't apply — but four real domain-adjacent items surfaced during discovery:

### Compliance & Regulatory

- **Non-affiliation disclaimer (required):** the app must visibly state it is unaffiliated with TransMilenio/SITP — not just a positioning note in the brief, but a concrete, always-visible UI requirement (e.g., footer or about page), to avoid confusion or trademark issues.
- **Open-data attribution:** GTFS static data is used under Colombia's Transparency Law (Ley 1712). Not strictly mandated, but source portals (ArcGIS Hub / Datos Abiertos Bogotá) generally expect credit on reuse. Requirement: a simple data-source credit line (e.g., "Datos de rutas: TransMilenio S.A. — Datos Abiertos") in the footer or about page.

### Technical Constraints

- **Geolocation privacy:** the core nearby-routes differentiator requires browser geolocation. The browser's native permission prompt already gates consent. Requirement: display one short, honest, plain-language disclosure (not a formal legal Privacy Policy) — e.g., *"Tu ubicación se usa solo para mostrarte rutas cercanas; no se guarda ni se comparte."* — reinforcing the existing "no ads, no data harvesting" trust principle.
- **Open architecture question (carry to architecture phase, not resolved here):** whether the nearby-routes query is computed client-side (stops/routes GeoJSON loaded in-browser, filtered locally — location never leaves the device) or server-side (coordinates sent to a backend spatial query, e.g., PostGIS `ST_DWithin` — location transmitted but not stored). This materially affects the strength of the privacy position and should be decided during architecture design.

### Risk Mitigations

- **Unofficial live-tracking API (`transmiapp` client):** legal exposure already accepted as a risk (Step 3), mitigated by graceful UI degradation rather than legal action. Additional soft mitigation: avoid publicizing the reverse-engineered endpoint's details (headers, spoofed User-Agent, URL structure) in any public-facing surface (docs, README, error messages, client-visible network calls where avoidable) to reduce the chance of drawing attention to it.

## Web App Specific Requirements

### Project-Type Overview

Server-rendered MPA (multi-page app) with targeted interactive elements (the map and live-tracking widgets), chosen deliberately over a full SPA framework — fewer moving parts to build, deploy, and keep working for a solo, nights-and-weekends maintainer. This also aligns with the existing Django server-rendered template foundation, reducing rewrite scope.

### Browser Support Matrix

Mobile-first as the primary target, matching the brief's real usage context (mid-range Android, sometimes weak signal inside BRT stations). Broad compatibility prioritized over bleeding-edge JS — avoid requiring newest browser APIs or polyfill-heavy code that would exclude older/lower-end devices. No dedicated desktop-only features, but the responsive layout should degrade reasonably on desktop.

### Responsive Design

Single responsive layout across breakpoints (mobile primary, tablet/desktop secondary) rather than separate experiences — consistent with the MPA-first, low-maintenance approach.

### Performance Targets

Lean page payloads, minimal JS by default, so core route/stop info loads reasonably fast on constrained mobile connections. Progressive enhancement: the page should be usable even if the interactive map/live-tracking layer loads slowly or fails. (Static-data query speed and live-position latency expectations already set in Step 3.)

### SEO Strategy

Explicitly not a priority — growth is via shared links and word of mouth, not search discovery. Clean, human-readable per-route URLs are still worth keeping (they support the "share a link with a friend" growth path and are just good MPA practice), but no dedicated SEO investment (meta tags, sitemap, structured data) planned for v1.

### Accessibility Level

"As accessible as possible," not formal WCAG compliance (no legal requirement per Step 5). Concrete baseline: semantic HTML, sufficient color contrast, readable font sizes, keyboard-navigable where feasible. This is a genuine extension of the project's inclusivity stance (plain language, no ads, no data harvesting) and ties back to the original motivation for a printable map aimed at older riders.

### Implementation Considerations

- Progressive enhancement: core route/stop browsing works with minimal JS; the map/live-tracking layer is the enhanced piece layered on top, not a hard dependency for basic usability.
- No separate SPA framework/build pipeline unless a specific interactive need genuinely can't be met with lighter tooling — keeps deployment simple.
- Server-rendered, shareable per-route/per-stop URLs, without SEO overhead.

## Functional Requirements

### Nearby Route & Stop Discovery (core differentiator)

- FR1: Rider can view all routes and stops near their current location on a single map, without selecting a specific route first.
- FR2: Rider can view all routes and stops near a location they choose (not just live GPS), to plan a trip before leaving home.
- FR3: Rider can compare live bus proximity across multiple nearby stops simultaneously, to decide which stop to walk to.
- FR4: Rider can identify which routes are shared across multiple nearby stops, to spot redundant or overlapping options.

### Route & Stop Browsing

- FR5: Rider can browse the full list of routes.
- FR6: Rider can search for a specific route by name or number.
- FR7: Rider can view a route's full path and ordered stop sequence on a map.
- FR8: Rider can view a stop's details, including which routes serve it.

### Live Bus Tracking

- FR9: Rider can see live positions of buses on trunk (BRT) routes overlaid on the map.
- FR10: Rider can distinguish an explicit "position unavailable" state from a normal live position, rather than seeing stale or wrong data when the live-tracking source is down.

### Data Currency (system capability)

- FR11: System can refresh static route/stop/schedule data from the official GTFS source on a recurring schedule without manual intervention.
- FR12: System can alert the maintainer when the GTFS refresh pipeline fails.
- FR13: System can alert the maintainer when the live-tracking source becomes unavailable or its response format changes.

### Trust & Transparency

- FR14: Rider can see a clear, always-visible statement that the app is unaffiliated with TransMilenio/SITP.
- FR15: Rider can see attribution/credit for the official open-data source used.
- FR16: Rider can see a short, plain-language explanation of how their location is used and that it isn't stored or shared.

### Sharing

- FR17: Rider can share a direct link to a specific route or stop with another person.
- FR18: A person opening a shared link sees that specific route/stop view directly, without additional navigation.

### Localization & Accessibility

- FR19: Rider can use the entire app in Spanish, with no other language required.
- FR20: Rider can read all content with sufficient color contrast and readable font sizes, and navigate via keyboard where feasible.

## Non-Functional Requirements

### Performance

- Static route/stop/schedule pages load and render within 3 seconds on a mid-range Android device over a weak/3G-equivalent connection — matches the real usage context (standing inside a BRT station).
- The nearby-routes/stops comparison query (FR1–FR4) returns results from the local static dataset in under 1 second — fully within project control, backed by the spatial indexing already required in Success Criteria.
- No fixed latency target for live bus position updates (depends on an upstream third-party API outside project control, per Step 3) — instead, staleness/unavailability must be surfaced explicitly (FR10) rather than hidden.

### Security

- No user accounts, authentication, or payment data in v1 — significantly limits the security surface.
- Geolocation coordinates are never logged or persisted server-side, regardless of whether the nearby-query is ultimately computed client-side or server-side — consistent with FR16's "not stored, not shared" commitment.
- Credentials/headers used to call the unofficial `transmiapp` live-tracking endpoint (spoofed User-Agent, hardcoded appid) are kept server-side only, never exposed in client-side JS or committed to public repo history — reduces the chance of the endpoint being discovered and blocked.
- HTTPS-only in production; no secrets committed to version control.

### Reliability & Monitoring

- GTFS refresh pipeline failures trigger a maintainer alert within 24 hours of a missed or failed scheduled run (ties to FR12).
- Live-tracking source failures or response-format changes are detected and alert the maintainer within the same day, not discovered via silent user complaints (ties to FR13, Journey 3).
- Static route/stop data availability is fully decoupled from live-tracking availability — a live-tracking outage must never take down route/stop browsing.

### Accessibility

- Text meets WCAG 2.1 AA color contrast minimums (4.5:1 for normal text), even though not a legal requirement.
- Font sizes are readable by default — no reliance on pinch-zoom for core content.
- Core navigation (route search, stop details) is operable via keyboard, not just touch/mouse.
