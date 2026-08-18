---
workflowType: 'implementation-readiness'
project_name: 'public_transport'
user_name: 'Vera'
date: '2026-08-17'
stepsCompleted: [step-01-document-discovery, step-02-prd-analysis, step-03-epic-coverage-validation, step-04-ux-alignment, step-05-epic-quality-review, step-06-final-assessment]
status: 'complete'
readinessStatus: 'READY'
reVerified:
  - date: '2026-08-17'
    scope: 'step-04-ux-alignment only, per user request'
    result: 'Both first-pass findings (Corridor/troncal data, FR5-FR6 UX coverage) confirmed resolved after fixes to relaunch-architecture.md and ux-design-specification.md'
documentsIncluded:
  prd: '_bmad-output/planning-artifacts/relaunch-prd.md'
  architecture: '_bmad-output/planning-artifacts/relaunch-architecture.md'
  ux: '_bmad-output/planning-artifacts/ux-design-specification.md'
  epicsAndStories: null
supersedes: '_bmad-output/planning-artifacts/relaunch-implementation-readiness-report-2026-08-05.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-17
**Project:** public_transport

## Document Inventory

**PRD:** `relaunch-prd.md` (whole document, last edited 2026-08-17 — FR11/NFR8 amendment)
**Architecture:** `relaunch-architecture.md` (whole document, last edited 2026-08-17 — Data Model Amendment)
**UX Design:** `ux-design-specification.md` (whole document, last edited 2026-08-17 18:23)
**Epics & Stories:** Not found — not yet created; noted as not-yet-applicable rather than a gap, since this assessment runs *before* `bmad-create-epics-and-stories`.

No duplicate (whole + sharded) document conflicts found for any document type.

This report supersedes `relaunch-implementation-readiness-report-2026-08-05.md`, which predated the architecture document, the UX design specification, and today's data-model amendment — all created/finalized after that report ran.

## PRD Analysis

### Functional Requirements Extracted

**Nearby Route & Stop Discovery (core differentiator)**
- FR1: Rider can view all routes and stops near their current location on a single map, without selecting a specific route first.
- FR2: Rider can view all routes and stops near a location they choose (not just live GPS), to plan a trip before leaving home.
- FR3: Rider can compare live bus proximity across multiple nearby stops simultaneously, to decide which stop to walk to.
- FR4: Rider can identify which routes are shared across multiple nearby stops, to spot redundant or overlapping options.

**Route & Stop Browsing**
- FR5: Rider can browse the full list of routes.
- FR6: Rider can search for a specific route by name or number.
- FR7: Rider can view a route's full path and ordered stop sequence on a map.
- FR8: Rider can view a stop's details, including which routes serve it.

**Live Bus Tracking**
- FR9: Rider can see live positions of buses on trunk (BRT) routes overlaid on the map.
- FR10: Rider can distinguish an explicit "position unavailable" state from a normal live position, rather than seeing stale or wrong data when the live-tracking source is down.

**Data Currency (system capability)**
- FR11: System can refresh static route/stop/schedule data from the official GTFS source, triggered by the maintainer, so riders never see data older than the last refresh. *(Amended 2026-08-17 — maintainer-triggered, not automatic/scheduled.)*
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

### Non-Functional Requirements Extracted

The PRD does not number its NFRs individually — they're grouped under 4 unlabeled-bullet subsections. Numbered here (NFR1–NFR13) following the same sequential convention `relaunch-architecture.md` already established in its own Requirements Coverage Validation table, so cross-references between the two documents stay consistent.

**Performance**
- NFR1: Static route/stop/schedule pages load and render within 3 seconds on a mid-range Android device over a weak/3G-equivalent connection.
- NFR2: The nearby-routes/stops comparison query (FR1–FR4) returns results from the local static dataset in under 1 second.
- NFR3: No fixed latency target for live bus position updates — staleness/unavailability must be surfaced explicitly (FR10) rather than hidden.

**Security**
- NFR4: No user accounts, authentication, or payment data in v1.
- NFR5: Geolocation coordinates are never logged or persisted server-side, client-side or server-side computation notwithstanding.
- NFR6: `transmiapp` credentials/headers kept server-side only, never exposed in client-side JS or committed to public repo history.
- NFR7: HTTPS-only in production; no secrets committed to version control.

**Reliability & Monitoring**
- NFR8: GTFS refresh pipeline failures are surfaced to the maintainer immediately (via Sentry) during a manually-triggered run. *(Amended 2026-08-17 — was "within 24 hours of a missed or failed scheduled run.")*
- NFR9: Live-tracking source failures or response-format changes are detected and alert the maintainer within the same day.
- NFR10: Static route/stop data availability is fully decoupled from live-tracking availability.

**Accessibility**
- NFR11: Text meets WCAG 2.1 AA color contrast minimums (4.5:1 for normal text).
- NFR12: Font sizes are readable by default — no reliance on pinch-zoom for core content.
- NFR13: Core navigation (route search, stop details) is operable via keyboard, not just touch/mouse.

**Total NFRs: 13**

### Additional Requirements

- **Domain-Specific Requirements** (Compliance & Regulatory, Technical Constraints, Risk Mitigations sections): non-affiliation disclaimer, open-data attribution, geolocation-use disclosure text, and a soft mitigation to avoid publicizing the reverse-engineered `transmiapp` endpoint's details. These overlap with FR14–FR16 but the geolocation privacy *architecture question* ("client-side vs. server-side computation") was explicitly flagged in the PRD as "carry to architecture phase, not resolved here" — confirmed resolved in `relaunch-architecture.md` (server-side, PostGIS `ST_DWithin`, with logging exclusions as a policy-enforced guarantee).
- **Web App Specific Requirements** section carries additional implementation-shaping constraints not phrased as FR/NFR: MPA (not SPA) architecture, mobile-first/broad-compatibility browser support, single responsive layout, lean/progressive-enhancement performance posture, explicit no-SEO-investment stance, and "as accessible as possible" (not formal WCAG certification) as the accessibility bar framing NFR11–13.
- **Journey Requirements Summary** (User Journeys section) is a narrative cross-check, not new requirements — every item in it traces to an FR/NFR already listed above; no orphaned journey-only requirement found.

### PRD Completeness Assessment

PRD is BMAD Standard format, internally consistent as of the 2026-08-17 edit. All 20 FRs and all 13 NFRs are individually testable/observable (no vague "should be fast" phrasing without a bound — even the deliberately-unbounded live-position latency (NFR3) is unbounded *by explicit decision*, not by omission, and pairs with a concrete substitute requirement, FR10). No outstanding open architecture questions remain flagged inside the PRD itself — the one that existed (client vs. server-side nearby-query) is marked "carry to architecture phase" and has since been resolved in `relaunch-architecture.md`. No contradictions found between FR/NFR text and the Domain-Specific/Web-App-Specific sections after today's FR11/NFR8 amendment.

## Epic Coverage Validation

**Status: Not applicable — no epics and stories document exists yet.**

This assessment is running deliberately *before* `bmad-create-epics-and-stories`, at Vera's request, specifically to validate PRD/UX/Architecture alignment before epics get written against them. Per document discovery (Step 1), no `*epic*.md` file or sharded epics folder exists in `{planning_artifacts}`.

All 20 FRs are therefore **pending**, not **missing** — there is no coverage gap to report because there is nothing yet that should be covering them. Flagging any of FR1–FR20 as "❌ MISSING" here would misrepresent normal pre-epic-creation state as a defect.

**Coverage Statistics**
- Total PRD FRs: 20
- FRs covered in epics: 0 (epics not yet created)
- Coverage percentage: N/A

**Carried forward as input to `bmad-create-epics-and-stories`:** the full FR/NFR list in PRD Analysis above, plus the PRD/Architecture/UX alignment findings from the remaining steps of this assessment.

## UX Alignment Assessment

### UX Document Status

**Found.** `ux-design-specification.md`, complete (14/14 steps), dated 2026-08-17, listing both `relaunch-prd.md` and `relaunch-architecture.md` as input documents. Full document read for this assessment (492 lines), not sampled.

### Positive Alignment (confirmed, not just absence of conflict)

- **Stop-type visual taxonomy independently matches the architecture's new `stop_type` discriminator.** UX's Map Marker Set defines a halo-ring marker for "TM station" and a plain dot for "SITP paradero" — this is the exact `estacion_troncal`/`paradero_zonal` split introduced in today's Data Model Amendment, arrived at from the UX side without reference to it (the UX spec predates the amendment within the same day). No action needed; flagging as evidence the two documents are converging on the same real-world model, not drifting apart.
- Live-tracking "unavailable" contract (FR10, architecture's `"live"`/`"unavailable"` HTTP-200 contract) is directly and correctly implemented in UX: "Sin datos en vivo" as a distinct, muted, non-color-only state — Feedback Patterns and Map Marker Set both.
- NFR1 mechanism (WhiteNoise, system font stack, no custom webfont) and NFR2 (<1s nearby-query) are both correctly cited and respected as constraints in Typography System and Core UX Success Criteria respectively.
- Architecture's MapLibre GL JS / no-build frontend decision is correctly cited (Design System Foundation) as the reason for a hand-rolled CSS system.
- Responsive strategy (single fluid layout, one breakpoint) matches the PRD's Web App Requirements "single responsive layout... rather than separate experiences" literally, not just in spirit.
- Ciclovía note ("alerta Ciclovía" in the Route Detail Panel / Journey 1 flow) is scoped as a tag/note only, never implying exact diverted-path rendering — consistent with the architecture's advisory-flag-only decision (no overcommitment beyond what data actually supports).

### Alignment Issues

Both issues below were found on the 2026-08-17 first pass and **re-verified as resolved** on re-check the same day, after targeted fixes to both documents.

**1. ~~Critical~~ RESOLVED — Corridor color / `troncal` data.**
Original finding: UX's Color System treats per-corridor trunk-route color as foundational (Tier 2 of its four-tier scheme, load-bearing from the first design decision onward), while the architecture's Data Model Amendment marked the underlying `troncal` grouping data "deferred, not required for MVP."
- **Fix verified in `relaunch-architecture.md`:** a `Corridor` model was added to the Proposed Data Models (name, zone_letter, color, pdf_link — matching exactly what the UX needs), with a `Route.corridor` FK (nullable for zonal routes, set for trunk routes). The original "deferred" line was corrected in place, not silently replaced, with a dated note explaining why the original deferral was wrong. `name` was chosen as the refresh natural key since GTFS has no native corridor concept.
- **Confirmed:** the UX's three required fields (corridor name, zone letter, color) all have a corresponding model field. No remaining gap.

**2. ~~Warning~~ RESOLVED — FR5/FR6 (browse/search) UX coverage.**
Original finding: FR5 (browse full route list) and FR6 (search by name/number) had no corresponding component anywhere in the UX spec, and the one place the document seemed to notice ("route search... N/A") never surfaced it as a decision.
- **Fix verified in `ux-design-specification.md`:** a fifth Custom Component, **Route Directory**, was added — a secondary, low-emphasis page (plain filterable route list + existing Route Detail Panel), explicitly not on the homepage, with a documented decision (2026-08-17) to keep FR5/FR6 in MVP scope rather than defer them, and reasoning for why (the per-route detail page and its shareable URL already exist; only discovery was missing). The three places that previously overstated "no search anywhere" (Core Experience, Form Patterns, the Accessibility Strategy bullet quoting NFR13) were each corrected to clarify the no-search principle applies to the *landing experience*, not the whole app.
- **Confirmed:** FR5 and FR6 now each have a direct component to trace to, consistent with the rest of the FR→component mapping. No remaining gap.

### Warnings

None. No case found, in either pass, of architecture failing to support a UX requirement's *technical* feasibility (performance, caching, data shape) — both resolved issues were about requirements coverage and data-model scope, and both are now closed.

## Epic Quality Review

**Status: Not applicable — no epics and stories document exists yet**, same basis as Epic Coverage Validation above. Best-practices enforcement (user-value framing, epic independence, forward-dependency checks, story sizing, database-creation timing) has nothing to run against. This section will be the one to fill in on the *next* readiness check, run after `bmad-create-epics-and-stories` and before implementation begins.

## Summary and Recommendations

### Overall Readiness Status

**READY** — updated 2026-08-17 after re-verifying the UX Alignment section against fixes applied to both `relaunch-architecture.md` (Corridor model) and `ux-design-specification.md` (Route Directory component). Both issues found on the first pass are confirmed resolved (see UX Alignment Assessment above). No open issues remain in any section of this assessment.

PRD, Architecture, and UX are each internally consistent as of today's edits and cross-consistent with each other. Epic Coverage and Epic Quality remain correctly not-applicable — there's nothing to write epics against yet, which was the point of running this check *before* `bmad-create-epics-and-stories` rather than after.

### Critical Issues Requiring Immediate Action

None remaining. (First-pass finding — corridor color foundational to UX but deferred in architecture — resolved; see UX Alignment Assessment, item 1.)

### Recommended Next Steps

1. **Proceed to `bmad-create-epics-and-stories`.** All planning-artifact alignment gates for this pre-epics check are closed.
2. Not blocking, carry forward as a note for the epics/stories themselves: the GTFS verification item already flagged in the architecture's Data Model Amendment (confirming `service_tier` sourcing, `gtfs_route_id`/`gtfs_stop_id` mapping, and the day-type value set against a real feed pull) doesn't block epic *creation*, but should block the specific *story* that implements those fields — worth carrying into that story's acceptance criteria or a pre-implementation task.
3. Run a full **Epic Coverage Validation** and **Epic Quality Review** (Steps 3 and 5 of this same workflow) once epics and stories exist — those sections were correctly skipped here, not passed.

### Final Note

First pass (this same date) identified 2 issues (1 critical, 1 warning), both in PRD/Architecture/UX cross-alignment — everything else checked clean on the first pass. Both issues were fixed and re-verified resolved on this re-check. Status is now READY to proceed to epic creation.