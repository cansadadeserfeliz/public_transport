---
workflowType: 'implementation-readiness'
project_name: 'public_transport'
user_name: 'Vera'
date: '2026-08-18'
stepsCompleted: [step-01-document-discovery, step-02-prd-analysis, step-03-epic-coverage-validation, step-04-ux-alignment, step-05-epic-quality-review, step-06-final-assessment]
status: 'complete'
readinessStatus: 'READY'
documentsIncluded:
  prd: '_bmad-output/planning-artifacts/relaunch-prd.md'
  architecture: '_bmad-output/planning-artifacts/relaunch-architecture.md'
  ux: '_bmad-output/planning-artifacts/relaunch-ux-design-specification.md'
  epicsAndStories: '_bmad-output/planning-artifacts/relaunch-epics.md'
supersedes: '_bmad-output/planning-artifacts/relaunch-implementation-readiness-report-2026-08-17.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-18
**Project:** public_transport

## Document Inventory

**PRD:** `relaunch-prd.md` (whole document, last edited 2026-08-18 19:09)
**Architecture:** `relaunch-architecture.md` (whole document, last edited 2026-08-18 19:10)
**UX Design:** `relaunch-ux-design-specification.md` (whole document, last edited 2026-08-18 19:13)
**Epics & Stories:** `relaunch-epics.md` (whole document, last edited 2026-08-18 19:10)

No duplicate (whole + sharded) document conflicts found for any document type.

This report supersedes `relaunch-implementation-readiness-report-2026-08-17.md`, which ran before epics and stories were created (`epicsAndStories: null` in that report). This is the first full readiness pass covering all four planning documents together.

## PRD Analysis

### Functional Requirements

**Nearby Route & Stop Discovery (core differentiator)**
- FR1: Rider can view all trunk (BRT/troncal) routes and stops near their current location on a single map, without selecting a specific route first.
- FR2: Rider can view all trunk (BRT/troncal) routes and stops near a location they choose (not just live GPS), to plan a trip before leaving home.
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
- FR11: System can refresh static route/stop/schedule data from the official GTFS source, triggered by the maintainer, and rider can see when that data was last successfully refreshed.
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

**Total FRs: 20**

### Non-Functional Requirements

**Performance**
- NFR1: Static route/stop/schedule pages load and render within 3 seconds on a mid-range Android device over a weak/3G-equivalent connection.
- NFR2: The nearby-routes/stops comparison query (FR1–FR4) returns results from the local static dataset in under 1 second.
- NFR3: No fixed latency target for live bus position updates (upstream third-party API outside project control) — staleness/unavailability must be surfaced explicitly (FR10) rather than hidden.

**Security**
- NFR4: No user accounts, authentication, or payment data in v1.
- NFR5: Geolocation coordinates are never logged or persisted server-side, regardless of client-side or server-side query computation.
- NFR6: Credentials/headers used to call the unofficial `transmiapp` live-tracking endpoint are kept server-side only, never exposed in client-side JS or committed to public repo history.
- NFR7: HTTPS-only in production; no secrets committed to version control.

**Reliability & Monitoring**
- NFR8: GTFS refresh pipeline failures are surfaced to the maintainer immediately (via Sentry) during a manually-triggered run.
- NFR9: Live-tracking source failures or response-format changes are detected and alert the maintainer within the same day.
- NFR10: Static route/stop data availability is fully decoupled from live-tracking availability.

**Accessibility**
- NFR11: Text meets WCAG 2.1 AA color contrast minimums (4.5:1 for normal text).
- NFR12: Font sizes are readable by default — no reliance on pinch-zoom for core content.
- NFR13: Core navigation (route search, stop details) is operable via keyboard, not just touch/mouse.

**Total NFRs: 13**

### Additional Requirements

- **Non-affiliation disclaimer:** always-visible UI element stating the app is unaffiliated with TransMilenio/SITP (ties to FR14, but framed in Domain-Specific Requirements as a concrete compliance-adjacent item).
- **Open-data attribution:** data-source credit line (e.g., "Datos de rutas: TransMilenio S.A. — Datos Abiertos") in footer/about page (ties to FR15).
- **Geolocation privacy disclosure:** one short, honest, plain-language disclosure at the point of location use (ties to FR16).
- **Open architecture question (resolved in architecture doc, verify below):** whether the nearby-routes query is computed client-side or server-side — PRD explicitly deferred this decision to the architecture phase.
- **Endpoint confidentiality (soft mitigation):** avoid publicizing the reverse-engineered `transmiapp` endpoint's details (headers, spoofed User-Agent, URL structure) in any public-facing surface.
- **Project type constraint:** server-rendered MPA, not a full SPA — architecture and epics should not silently introduce a SPA framework/build pipeline.
- **Mobile-first, broad browser compatibility:** no bleeding-edge JS APIs requiring polyfills that exclude older/lower-end Android devices.
- **SEO explicitly out of scope** for v1, but clean human-readable per-route/per-stop URLs still expected (supports FR17/FR18 sharing).
- **Progressive enhancement constraint:** core route/stop browsing must work with minimal JS; map/live-tracking is an enhancement layer, not a hard dependency.

### PRD Completeness Assessment

The PRD is thorough and internally cross-referenced (explicit amendment history shows two prior alignment passes with the architecture document, on 2026-08-17 and 2026-08-18, reconciling FR1–FR4 trunk/BRT MVP scoping and FR11's refresh-trigger model). Success Criteria, User Journeys, Domain-Specific Requirements, and Web App Specific Requirements sections all supply testable detail beyond the FR/NFR lists themselves — these are captured above as "Additional Requirements" so epic coverage validation can check against them too, not just the 20 FRs and 13 NFRs. One item is explicitly flagged in the PRD itself as not yet resolved at the PRD level: the client-side vs. server-side computation choice for the nearby-routes query — this should have a definitive answer in `relaunch-architecture.md`, checked in the epic coverage step.

## Epic Coverage Validation

### Epic FR Coverage Extracted

The epics document ships its own explicit "FR Coverage Map" (lines 182–203) plus a per-epic "FRs covered" line repeated at each epic heading — coverage claims below are cross-checked against both.

### Coverage Matrix

| FR Number | PRD Requirement (summary) | Epic Coverage | Status |
|---|---|---|---|
| FR1 | Nearby trunk routes/stops at current location | Epic 1, Story 1.5 | ✓ Covered |
| FR2 | Nearby trunk routes/stops at chosen location | Epic 1, Story 1.5 | ✓ Covered |
| FR3 | Compare live bus proximity across nearby stops | Epic 1, Story 1.6 | ✓ Covered |
| FR4 | Identify routes shared across nearby stops | Epic 1, Story 1.7 | ✓ Covered |
| FR5 | Browse full route list | Epic 2, Story 2.1 | ✓ Covered |
| FR6 | Search route by name/number | Epic 2, Story 2.2 | ✓ Covered |
| FR7 | View route's full path/stop sequence | Epic 2, Story 2.3 | ✓ Covered |
| FR8 | View stop details incl. serving routes | Epic 2, Story 2.4 | ✓ Covered |
| FR9 | Live BRT bus positions on map | Epic 3, Story 3.2 | ✓ Covered |
| FR10 | Distinguish "unavailable" from live | Epic 3, Story 3.1 + 3.2 | ✓ Covered |
| FR11 | GTFS refresh + last-refreshed disclosure | Epic 1 Story 1.3 (refresh) + Epic 4 Story 4.1 (disclosure) | ✓ Covered (split, both halves present) |
| FR12 | Alert maintainer on refresh failure | Epic 1, Story 1.4 | ✓ Covered |
| FR13 | Alert maintainer on live-tracking failure | Epic 3, Story 3.3 | ✓ Covered |
| FR14 | Non-affiliation statement | Epic 4, Story 4.1 | ✓ Covered |
| FR15 | Open-data attribution | Epic 4, Story 4.1 | ✓ Covered |
| FR16 | Location-use disclosure | Epic 4, Story 4.1 | ✓ Covered |
| FR17 | Share direct link | Epic 4, Story 4.2 | ✓ Covered |
| FR18 | Shared link opens directly to view | Epic 4, Story 4.2 | ✓ Covered |
| FR19 | Spanish-only UI | Epic 5, Story 5.1 | ✓ Covered |
| FR20 | Contrast/font/keyboard accessibility | Epic 5, Story 5.2 + 5.3 | ✓ Covered |

### Missing Requirements

None. All 20 PRD FRs have a traceable epic/story. No FRs appear in the epics' coverage map that are absent from the PRD (FR1–FR20 in epics match FR1–FR20 in PRD exactly, same numbering, same wording).

One coverage nuance, not a gap: **FR11 is intentionally split** across two epics — the core refresh mechanism lands in Epic 1 (Story 1.3), while the rider-facing "last-refreshed" disclosure lands in Epic 4 (Story 4.1), because Epic 4 is where all rider-facing trust/transparency UI is consolidated. The epics document flags this explicitly ("Cross-epic" note on Epic 4), so it's a deliberate sequencing choice, not an oversight — worth confirming the Sprint Plan doesn't schedule Epic 4 so far behind Epic 1 that FR11's disclosure half sits undelivered for a long stretch.

### Coverage Statistics

- Total PRD FRs: 20
- FRs covered in epics: 20
- Coverage percentage: 100%

## UX Alignment Assessment

### UX Document Status

**Found.** `relaunch-ux-design-specification.md` — complete, dated 2026-08-17, `status: complete`, all 14 workflow steps finished. Its own `editHistory` records a targeted fix (Route Directory component) made specifically in response to the prior (2026-08-17) implementation readiness report's FR5/FR6 coverage finding — evidence the cross-document feedback loop already worked once.

### A. UX ↔ PRD Alignment

Strong, explicit alignment:
- Both PRD user journeys (Camila, Andrés) are reproduced as UX Journey Flows with matching mermaid diagrams and matching climax/resolution beats.
- Every FR has a UX home: FR1–FR4 → Core Experience + Nearby Route Row + Map Marker Set; FR5–FR6 → Route Directory (added specifically to close a gap the previous readiness pass found); FR7–FR8 → Route Detail Panel; FR9–FR10 → Map Marker Set live/unavailable states; FR11 → Trust Footer's last-refreshed line; FR14–FR16 → Trust Footer; FR17–FR18 → Panel/URL duality; FR19 → Spanish-only content voice throughout; FR20 → dedicated Responsive Design & Accessibility section targeting WCAG 2.1 AA, matching the PRD's own accessibility bar exactly (4.5:1 contrast, no color-alone states, keyboard operability).
- No UX requirement found that lacks a PRD anchor, and no PRD requirement found without UX treatment.

### B. UX ↔ Architecture Alignment

Strong, and bidirectionally traceable — each document cites the other by name at the relevant decision points:
- **No-build frontend:** UX's "lightweight custom design system, no framework, no build step, CSS custom properties" matches architecture's Frontend Architecture decision (MapLibre GL JS via `<script>` tag, no bundler) exactly; UX explicitly cites this as its rationale for rejecting Bootstrap/Material.
- **Corridor color:** the architecture's Data Model Amendment (item 2) explicitly promoted `Corridor` to a real model *because* the UX spec's four-tier Color System makes per-corridor color a Phase-1 requirement — a genuine two-way dependency, correctly resolved in both documents rather than left as a silent mismatch.
- **Server-side nearby query + GeoJSON:** UX's map/marker rendering assumes GeoJSON feature data, matching architecture's Format Patterns decision (GeoJSON for all geometry endpoints).
- **Performance:** UX's "no custom webfont, lean payloads" matches architecture's WhiteNoise/NFR1 resolution; UX's <1s "feels instant" success criterion matches NFR2's PostGIS-backed target.
- **Loading/error states:** UX's "no global spinner, local placeholders" and "two honestly-attributed error states" match architecture's Process Patterns (no global loading state; Sentry-captured system errors vs. upstream-attributed errors) verbatim.

### Alignment Issues

**One documentation-hygiene issue, not a technical/content conflict:**

`relaunch-architecture.md` contains multiple stale cross-references describing two items as still outstanding, when both have since been completed:
- Line ~117, ~393, ~656–657, ~675, ~749: notes describing the FR11/NFR8 PRD reconciliation (manual vs. scheduled GTFS refresh) as "not yet done" / "pending" / "to-be-updated wording."
- Line ~699, ~750, ~761–762 ("Outstanding Action Items"): lists "update PRD FR11/NFR8" and "run `bmad-create-ux-design`" as not-yet-done follow-ups.

Both are actually done: the PRD's own `editHistory` records the FR11/NFR8 reconciliation on 2026-08-17, and the UX design document itself (this step's subject) exists, is complete, and explicitly builds on the architecture document. Notably, `relaunch-architecture.md` has continued to receive edits *after* 2026-08-17 (it carries several 2026-08-18-dated amendments in its Data Model Amendment section), so this isn't simply an untouched old snapshot — these specific stale notes were left unreconciled even while other parts of the same document were actively revised.

**Impact:** Low. The actual technical content across PRD, architecture, UX, and epics is consistent — this doesn't block Phase 4 implementation, since the epics document (the thing Sprint Planning will actually consume) already reflects the correct, resolved state. But a future reader consulting `relaunch-architecture.md` in isolation could be misled into re-litigating a settled question or duplicating already-done work.

**Recommendation:** A short, low-risk edit pass on `relaunch-architecture.md` to mark its "Outstanding Action Items" as resolved (with a dated note pointing to the PRD's 2026-08-17 amendment and this UX document) — not a blocker for Sprint Planning, but worth doing before this document is treated as a long-lived reference during Phase 4.

### Warnings

None beyond the alignment issue above. UX/UI is clearly present and thoroughly documented — no missing-UX warning applies.

## Epic Quality Review

Validated against create-epics-and-stories standards: user value focus, epic independence, forward-dependency prohibition, story sizing, AC quality (Given/When/Then, testable, complete), and database-creation timing.

### Epic Structure Validation

| Epic | User Value Focus | Independence |
|---|---|---|
| Epic 1 | Real user value (core differentiator) plus bundled brownfield foundation work — justified, see note below | Stands alone; nothing later required |
| Epic 2 | Real user value (browse/search/detail) | Uses only Epic 1 output ✓ |
| Epic 3 | Real user value (live tracking) | Uses only Epic 1 output; explicitly "no dependency on Epic 2" ✓ |
| Epic 4 | Real user value (trust/sharing) | Uses Epic 1 + Epic 2 output (skips Epic 3, which is fine — no future-epic dependency) ✓ |
| Epic 5 | Real user value (localization/accessibility) | Uses Epic 1–4 output as an explicit hardening pass — backward-only dependency, compliant ✓ |

No epic requires a *later* epic to function. All dependencies point backward only — compliant with the "Epic N cannot require Epic N+1" rule.

**Note on Epic 1's technical stories (1.1–1.4, 1.8):** These are maintainer-facing/technical (Django/PostGIS upgrade, data model, refresh pipeline, alerting, README) rather than literally rider-facing. Per this workflow's own Special Implementation Checks (§5B), brownfield projects are *expected* to carry migration/compatibility stories — this isn't the "Setup Database with no user value" anti-pattern the checklist warns about in the greenfield case, since the epic explicitly frames this work as unavoidable enabling work for the epic's real (rider-facing) FRs, not a standalone technical epic. No violation.

### Within-Epic Dependency Check

Traced every story's stated dependency across all 5 epics: **no forward dependencies found.** Every "depends on Story X.Y" or implicit ordering reference points to an earlier-numbered story in the same or an earlier epic (e.g., Epic 4 Story 4.2 relies on Epic 1 Stories 1.2/1.3's natural-key behavior; Epic 2 Story 2.3 is self-contained). Two stories (1.1, 3.1) mention a *later* story by number (Story 1.1 → Story 3.1's cache-bounding assumption; Story 3.1 → Story 3.3's Sentry capture) — these are explanatory cross-references ("here's why this matters later"), not blocking dependencies; each origin story is fully completable on its own without the referenced future story existing. Not a violation.

### Database/Entity Creation Timing

Epic 1 Story 1.2 creates all five models (`BusStop`, `Route`, `Corridor`, `RouteSchedule`, `RouteStations`) in a single migration, rather than "each story creates tables it needs" per this workflow's general guidance. **Deviation, but justified:** this is a brownfield full-schema replacement where the models are relationally interdependent from day one (`Route.corridor` FK to `Corridor`, `RouteStations` FK to both `Route` and `BusStop`) and are explicitly generated as one fresh `0001_initial` migration (architecture's own stated rationale — incremental migrations against a schema being replaced wholesale would be pure churn). Splitting model creation across stories here would fragment one atomic, relationally-coupled migration for no benefit. Not flagged as a defect.

### Acceptance Criteria & Story Sizing Findings

#### 🟠 Major

- **Story 1.7 (Shared-Route Identification), core AC is non-committal.** "that route is identifiable as shared across those stops (**e.g.,** visually grouped or cross-referenced)" — the "e.g." leaves the actual treatment undefined. Every other story in the epics document commits to a specific, testable treatment (exact copy strings, exact HTTP status codes, exact marker shapes); this AC is the one exception, and as written, two implementers could satisfy it in materially different, non-equivalent ways. **Recommendation:** tighten to a specific treatment before Sprint Planning schedules this story — e.g., reference the UX spec's actual grouping mechanism if one exists, or explicitly state this is a UX decision deferred to implementation time (and say so, rather than leaving it ambiguous by omission).

- **Story 1.2 (GTFS-Ready Data Model) conflates a blocking research task with implementation.** Its first Given/When/Then block is a data-verification spike (pull real `routes.txt`/`stops.txt`/`calendar.txt`/`calendar_dates.txt`, confirm natural-key mappings and the day-type value set) that the architecture document itself flags as blocking and currently unresolved ("Verification still needed before implementation"). The second block is the actual model/migration implementation, which depends on the first's findings. Bundling an open-ended external-data investigation with a concrete build task in one story risks the story stalling in an ambiguous "in progress" state if the verification surfaces surprises (e.g., a `service_tier` field that doesn't map the way assumed). **Recommendation:** consider splitting into a verification/spike story (output: confirmed field mappings, documented in the architecture doc) followed by the model-implementation story — gives Sprint Planning a clean point to re-plan if the verification finds something unexpected, rather than discovering it mid-story.

#### 🟡 Minor

- **Story 1.5 (Nearby Routes & Stops on the Map) bundles five distinct concerns** in one story: core geolocation query, manual-pin fallback, empty state, responsive breakpoint reflow, and loading state. It's defensible as-is since this is explicitly the epic's (and PRD's) single most load-bearing story — the core differentiator — and all five pieces are needed for a coherent first demo. Flagged only as a size/splitting candidate if the maintainer finds it slow going in practice, not as a defect.
- **Epic 1's title** ("Nearby Route & Stop Discovery (Foundation + Core Differentiator)") mixes a user-facing name with a technical parenthetical. Cosmetic only.

### Best Practices Compliance Checklist (per epic)

| Check | Epic 1 | Epic 2 | Epic 3 | Epic 4 | Epic 5 |
|---|---|---|---|---|---|
| Delivers user value | ✓ (+justified enabling work) | ✓ | ✓ | ✓ | ✓ |
| Functions independently of later epics | ✓ | ✓ | ✓ | ✓ | ✓ |
| Stories appropriately sized | ⚠️ (1.2, 1.5 large — see above) | ✓ | ✓ | ✓ | ✓ |
| No forward dependencies | ✓ | ✓ | ✓ | ✓ | ✓ |
| DB tables created only when needed | ⚠️ (justified deviation — see above) | n/a | n/a | n/a | n/a |
| Clear, testable acceptance criteria | ⚠️ (Story 1.7 — see above) | ✓ | ✓ | ✓ | ✓ |
| Traceability to FRs maintained | ✓ | ✓ | ✓ | ✓ | ✓ |

## Summary and Recommendations

### Overall Readiness Status

**READY**

### Critical Issues Requiring Immediate Action

None. Zero critical violations found across FR coverage (20/20), epic independence, forward-dependency checks, and UX/architecture alignment.

### Issues Found (non-blocking)

1. **[Major] Story 1.7's core acceptance criterion is non-committal** ("e.g., visually grouped or cross-referenced") — the only AC in the entire epics document that doesn't specify a concrete, testable treatment. See Epic Quality Review.
2. **[Major] Story 1.2 bundles a blocking GTFS-verification spike with model implementation** — risks the story stalling mid-flight if the real feed data doesn't match current assumptions about `service_tier`/natural-key mappings. See Epic Quality Review.
3. **[Documentation hygiene] `relaunch-architecture.md` contains stale "outstanding action item" notes** (PRD FR11/NFR8 update, UX design creation) describing already-completed work as still pending. See UX Alignment Assessment. Doesn't affect epics/stories (which already reflect the correct state) but risks confusing a future reader of the architecture doc in isolation.
4. **[Minor] Story 1.5 bundles five distinct concerns** (core query, manual-pin fallback, empty state, responsive layout, loading state) — defensible given it's the product's single most load-bearing story, flagged only as a splitting candidate if it proves slow to implement.
5. **[Nuance, not a gap] FR11 is intentionally split** across Epic 1 (refresh mechanism) and Epic 4 (rider-facing disclosure) — confirm Sprint Planning doesn't schedule Epic 4 so far behind Epic 1 that the disclosure half sits undelivered for a long stretch.

### Recommended Next Steps

1. Before or during Sprint Planning: tighten Story 1.7's acceptance criterion in `relaunch-epics.md` to a specific, testable treatment for cross-stop route identification.
2. Before or during Sprint Planning: decide whether to split Story 1.2 into a verification/spike story plus a model-implementation story, or explicitly accept the bundled risk and flag it for the maintainer to watch during that story.
3. Low-priority cleanup: update `relaunch-architecture.md`'s stale "Outstanding Action Items" and inline deviation notes (§Data Architecture, §Requirements Coverage Validation, §Architecture Readiness Assessment) to reflect that the PRD FR11/NFR8 reconciliation and the UX design document are both complete.
4. Proceed to **Sprint Planning** (`bmad-sprint-planning`) — the required Phase 4 gate that produces the sprint status file driving story-by-story implementation.

### Final Note

This assessment identified 5 issues (2 Major, 1 documentation-hygiene, 1 Minor, 1 sequencing nuance) across FR coverage, UX alignment, and epic quality — none blocking. Functional requirement coverage is complete (20/20, 100%), epic structure and dependencies are sound, and UX/architecture/PRD are substantively aligned with only stale cross-references (not content conflicts) found. Recommend addressing items 1–2 above before their respective stories reach active development, but proceeding to Sprint Planning now rather than blocking on them.

---

**Assessed by:** Implementation Readiness workflow (bmad-check-implementation-readiness)
**Date:** 2026-08-18
**Project:** public_transport
