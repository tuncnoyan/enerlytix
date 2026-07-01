---
description: "Task list for 003-report-visuals-page"
---

# Tasks: Utility Usage Report Visuals Page

**Input**: Design documents from `specs/003-report-visuals-page/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/report-data-api.md ✅, quickstart.md ✅

---

## Phase 1: Setup

**Purpose**: Schema changes and file scaffolding that gate all other work.

- [ ] T001 Add `available_capacity` nullable DecimalField to `Supply` and create `Benchmark` model in `django_app/sitesync/models.py`; generate migration `django_app/sitesync/migrations/0004_supply_available_capacity_benchmark.py`
- [ ] T002 [P] Register `report_view` at `/report/` and `report_data_api_view` at `/api/report-data/` in `django_app/sitesync/urls.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core server-side data service and client-side skeleton that every user story builds on. No story work starts until these are complete.

⚠️ **CRITICAL**: All Phase 3–6 tasks depend on T003, T005, and T006.

- [ ] T003 Implement `report_data_api_view` in `django_app/sitesync/views.py`: accept `site_id` + `end_month` query params; assemble full JSON response per `contracts/report-data-api.md`; compute Max Demand, Load Factor, variance, Day/Night split server-side; return 400/404 on bad input
- [ ] T004 [P] Add `BenchmarkSerializer` in `django_app/sitesync/serializers.py` and stub `report_view` (renders `report.html` with `site_id` + `end_month` from GET params) in `django_app/sitesync/views.py`
- [ ] T005 [P] Create `django_app/templates/sitesync/report.html`: page shell (topbar, left-nav pane, main scroll area), CSS variables matching the existing design system (`--cxg-*`), CDN `<script>` tags for Chart.js 4.4.9, html2canvas 1.4.1, and jsPDF 2.5.2
- [ ] T006 [P] Create `django_app/static/sitesync/js/report.js`: fetch `/api/report-data/` on page load; parse response; dispatch section rendering per utility type in order electricity → gas → water; expose `renderReport(data)` entry point

**Checkpoint**: Foundation complete — US1/US2/US3/US4 work can now proceed in parallel per story.

---

## Phase 3: User Story 1 — Generate and View Utility Report (Priority: P1) 🎯 MVP

**Goal**: Dashboard entry point renders a fully populated report page with all charts, tables, section ordering, left nav, and empty/missing-data states.

**Independent test**: Navigate dashboard → select one site → set end month → click Create Report → all visual sections present and drawn with real data.

- [ ] T007 [US1] Add "Create Report" button and `<input type="month">` picker to `.import-controls` panel in `django_app/templates/sitesync/site_list.html`, directly after `#trigger-import-button` (per FR-001); style buttons to match existing `.import-controls button` style
- [ ] T008 [US1] Implement enable/disable logic for "Create Report" button and month picker in `django_app/static/sitesync/js/site_selection.js`: disabled when 0 sites checked (tooltip: "Select a site first"), disabled when ≥2 sites checked (tooltip: "Select only one site to create a report"), enabled + navigates to `/report/?site_id=X&end_month=YYYY-MM` when exactly 1 site checked
- [ ] T009 [US1] Implement Site Overview section in `django_app/static/sitesync/js/report.js`: render Total Utility Usage (£) pie chart (Chart.js doughnut) + cost-breakdown table from `response.overview`; use `--cxg-highlight-376` (#7AB800) for Electricity, `--cxg-primary-430` (#7C878E) for Gas, `--cxg-primary-432` (#333F48) for Water
- [ ] T010 [P] [US1] Implement Monthly Electricity Usage bar chart in `django_app/static/sitesync/js/report.js`: grouped bar chart with Current (green `#7AB800`), Previous Year (grey `#7C878E`), Benchmark (yellow `#F5C400`) series from `supply.monthly`; x-axis months, y-axis kWh with `K` suffix formatter; omit Benchmark series if all null
- [ ] T011 [P] [US1] Implement Monthly Electricity Usage table in `django_app/static/sitesync/js/report.js`: render HTML table rows from `supply.monthly.table` with columns Date, Last 12 Months (kWh), Prev. 12 Months (kWh), Gross Variance (kWh), Relative Variance (%)
- [ ] T012 [P] [US1] Implement Electricity Load Factor visual in `django_app/static/sitesync/js/report.js`: line chart with Consumption series (green), Max Demand constant line (grey), Available Capacity constant line (yellow, omit if null); three KPI cards below showing Load Factor %, Max Demand kW, Available Capacity kW (or "N/A"); data from `supply.load_factor`
- [ ] T013 [P] [US1] Implement HH Electricity Data Comparison — Last Month line chart in `django_app/static/sitesync/js/report.js`: dual line chart from `supply.hh_comparison`; Current Year (green `#7AB800`), Previous Year Same Month (grey `#7C878E`); x-axis datetime ticks; enable Chart.js `normalized: true` and `parsing: false` (pass pre-sorted numeric arrays) to handle ~1 500 data points per series within SC-001 render budget
- [ ] T014 [P] [US1] Implement HH Electricity Day/Night Usage — Last Month stacked bar chart in `django_app/static/sitesync/js/report.js`: one bar per HH interval from `supply.day_night.records`; Day period (green `#7AB800`), Night period (dark `#333F48`); x-axis datetime ticks
- [ ] T015 [P] [US1] Implement Daily Comparison — Weekday Usage overlaid line chart in `django_app/static/sitesync/js/report.js`: one line series per weekday from `supply.weekday_comparison.days`; x-axis 00:00–23:30 time labels; multi-colour series from a fixed 20-colour palette; use `normalized: true` and `parsing: false` (T013 pattern)
- [ ] T016 [P] [US1] Implement Daily Comparison — Weekend Usage overlaid line chart in `django_app/static/sitesync/js/report.js`: same pattern as T015 using `supply.weekend_comparison.days`; same performance options
- [ ] T017 [P] [US1] Implement Monthly Gas Usage bar chart in `django_app/static/sitesync/js/report.js`: same grouped bar pattern as T010 using gas supply `monthly` data (unit: kWh)
- [ ] T018 [P] [US1] Implement Monthly Gas Usage table in `django_app/static/sitesync/js/report.js`: same table pattern as T011 for gas supply `monthly.table` (unit: kWh)
- [ ] T019 [P] [US1] Implement HH Gas Data Comparison — Last Month line chart in `django_app/static/sitesync/js/report.js`: same dual-line pattern as T013 using gas `supply.hh_comparison`; same `normalized: true` / `parsing: false` options
- [ ] T020 [P] [US1] Implement Daily Comparison — Weekday Usage (Gas) overlaid line chart in `django_app/static/sitesync/js/report.js`: same pattern as T015 using gas `supply.weekday_comparison.days`; same performance options
- [ ] T021 [P] [US1] Implement Daily Comparison — Weekend Usage (Gas) overlaid line chart in `django_app/static/sitesync/js/report.js`: same pattern as T016 using gas `supply.weekend_comparison.days`; same performance options
- [ ] T022 [P] [US1] Implement Monthly Water Usage bar chart in `django_app/static/sitesync/js/report.js`: same grouped bar pattern as T010 using water supply `monthly` data (unit: m³; field names `current_m3` / `previous_year_m3` / `benchmark_m3`)
- [ ] T023 [P] [US1] Implement Monthly Water Usage table in `django_app/static/sitesync/js/report.js`: same table pattern as T011 for water supply `monthly.table` (columns use m³ unit label)
- [ ] T024 [US1] Implement utility section ordering and conditional rendering in `django_app/static/sitesync/js/report.js`: iterate `response.supplies` grouped by `utility_type` in order electricity → gas → water; skip a utility group if it has no entries; within a group render one full visual set per supply
- [ ] T025 [US1] Implement left navigation pane in `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js`: populate nav entries dynamically after data loads; single supply per type → labelled by utility name; multiple supplies → labelled by meter number; clicking an entry smooth-scrolls to the corresponding section anchor
- [ ] T026 [US1] Implement "no halfhourly data available" placeholder card in `django_app/static/sitesync/js/report.js`: shown in place of Load Factor, HH Comparison, Day/Night, Weekday, and Weekend visuals when `supply.load_factor` or `supply.hh_comparison` is null or has empty `halfhourly` / `current` arrays (implements FR-033)

---

## Phase 4: User Story 2 — Add Comments to Visuals (Priority: P2)

**Goal**: Each visual has an editable text area beneath it; comments persist for the session and appear in the PDF.

**Independent test**: Open report page, type text in any comment box, scroll away and back — text is retained.

- [ ] T027 [US2] Implement comment boxes in `django_app/static/sitesync/js/report.js` and `django_app/templates/sitesync/report.html`: inject a `<textarea>` beneath each chart/table visual with a stable `data-section-id` attribute; store and restore comment text from a `Map` keyed by section ID on `input` event; hide placeholder text in print/PDF context via CSS

---

## Phase 5: User Story 3 — Download Report as PDF (Priority: P3)

**Goal**: "Download as PDF" button generates a landscape PDF containing all visible visuals and comments.

**Independent test**: Type a comment, click Download as PDF, verify the PDF contains all sections and the comment text in the correct position.

- [ ] T028 [US3] Implement "Download as PDF" button and client-side export in `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js`: iterate visual sections in order; for each section use `html2canvas({ scale: 2 })` to capture the DOM node; add one landscape A4 jsPDF page per section; embed the canvas image; trigger browser download as `Enerlytix_Report_<site>_<end_month>.pdf`

---

## Phase 6: User Story 4 — Navigate Report Page (Priority: P4)

**Goal**: Top ribbon links allow navigation away from the report page; existing pages link to the report page.

**Independent test**: Click each top ribbon link from the report page and confirm the correct destination loads.

- [ ] T029 [US4] Add top ribbon navigation links to `django_app/templates/sitesync/report.html`: include Dashboard, Usage & Invoices, Settings links matching the pattern in `site_list.html`; "Report" link marked `is-active`
- [ ] T030 [P] [US4] Add "Report" link to the topbar navigation in `django_app/templates/sitesync/site_list.html` and `django_app/templates/sitesync/consumption_display.html`

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T031 Write unit tests for Max Demand, Load Factor, and variance calculation logic in `django_app/sitesync/tests/test_report_data.py`: assert correct values against known HH fixtures; assert null/zero handling for previous year absent cases
- [ ] T032 Implement "no supplies" empty state in `django_app/templates/sitesync/report.html`: show a user-friendly message when `response.supplies` is empty (site exists but has no associated supply records)

---

## Dependencies

```
T001 → T003, T004, T005
T002 → T003, T004, T006
T003 → T007..T028   (API must exist before client fetch is useful)
T004 → T005
T005 → T006
T006 [P with T003] → T007..T028   (skeleton can be written before T003 is complete; runtime dep only)

Story execution order (can be parallelised once Phase 2 is done):
  US1 (T007–T026) → recommended first: delivers the full visual page
  US2 (T027)      → can start as soon as T005/T006 exist
  US3 (T028)      → depends on T027 (comments must exist before PDF captures them)
  US4 (T029–T030) → fully independent; can be done alongside US1
```

## Parallel Execution Examples

Within **Phase 3 (US1)**, once T005/T006 are complete, T010–T023 can all run in parallel (they each implement one independent chart/table in `report.js` with no shared state).

Within **Phase 6 (US4)**, T029 and T030 touch different files and are fully parallel.

## Implementation Strategy

**MVP (US1 only)**: Complete Phases 1–3. Delivers the full report page with all charts and tables — the primary stakeholder-visible deliverable.

**Full sprint**: Complete all phases in order US1 → US2 → US3 → US4 → Polish.
