# Tasks: Report Cover Pages

**Input**: Design documents from `/specs/007-add-report-cover-pages/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Targeted test-authoring tasks are included (T029, T030), plus Docker-based suite execution (T031) and quickstart validation (T032).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare static assets and baseline cover-page configuration points in the existing Dockerized Django app structure.

- [X] T001 Add first-cover default background and static back-cover image assets in django_app/static/sitesync/images/
- [X] T002 Add cover-page container placeholders and metadata hooks in django_app/templates/sitesync/report.html
- [X] T003 [P] Add cover-page constants (dimensions, field keys, format strings) in django_app/static/sitesync/js/report.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared cover composition and validation infrastructure required by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement report cover composition structures (`ReportCoverSet`, `FrontCoverOneFields`, `FrontCoverTwoFields`) in django_app/sitesync/services.py
- [X] T005 [P] Implement first-cover upload validation rules (JPG/JPEG/PNG/WebP, <=10 MB) in django_app/static/sitesync/js/report.js
- [X] T006 [P] Implement fixed `DD MMMM YYYY` date formatter utility for cover rendering in django_app/static/sitesync/js/report.js
- [X] T007 Implement report payload enrichment for cover defaults and visual contents entries in django_app/sitesync/views.py
- [X] T008 Implement shared cover sequence assembler (front1, front2, body, back) for draft/final/PDF/PPTX in django_app/static/sitesync/js/report.js

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate reports with integrated cover pages (Priority: P1) 🎯 MVP

**Goal**: Ensure both draft and final reports always include the three cover pages in the required order.

**Independent Test**: Generate draft and final reports for one site/month and verify sequence `front cover 1 -> front cover 2 -> report body -> back cover`.

### Implementation for User Story 1

- [X] T009 [US1] Render front cover page 1 and front cover page 2 before report body in django_app/templates/sitesync/report.html
- [X] T010 [US1] Render back cover page after report body in django_app/templates/sitesync/report.html
- [X] T011 [US1] Bind cover sequence assembly to report load/generation lifecycle in django_app/static/sitesync/js/report.js
- [X] T012 [US1] Ensure draft/final report rendering paths use the same cover sequence in django_app/static/sitesync/js/report.js
- [X] T013 [US1] Add graceful fallback to default assets if cover composition data is incomplete in django_app/static/sitesync/js/report.js

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Edit first front-cover content per report (Priority: P1)

**Goal**: Provide editable first-cover fields with defaults, optional logo, and per-report background replacement.

**Independent Test**: Edit first-cover fields and upload a valid/invalid background image, then generate output and verify defaults, edits, and validation behavior.

### Implementation for User Story 2

- [X] T014 [US2] Add editable first-cover inputs (site title, month title, date, client logo area) in django_app/templates/sitesync/report.html
- [X] T015 [US2] Populate first-cover default values from selected site/report month/current date in django_app/static/sitesync/js/report.js
- [X] T016 [US2] Implement first-cover replacement image upload handling scoped to current report context in django_app/static/sitesync/js/report.js
- [X] T017 [US2] Implement invalid upload error messaging and default-image fallback in django_app/templates/sitesync/report.html
- [X] T018 [US2] Map first-cover editable fields and logo/background assets into generated cover render state in django_app/static/sitesync/js/report.js
- [X] T018a [US2] Implement client-logo upload validation rules (PNG/JPG/SVG, <=2 MB) and user-facing validation messages in django_app/static/sitesync/js/report.js
- [X] T018b [US2] Implement aspect-ratio-safe logo fit behavior inside the reserved logo region in django_app/templates/sitesync/report.html and django_app/static/sitesync/js/report.js

**Checkpoint**: User Story 2 is fully functional and independently testable.

---

## Phase 5: User Story 3 - Edit second front-cover scope and contents text (Priority: P1)

**Goal**: Provide editable second-cover scope/contents blocks with correct default wording and meter-name suffix rules.

**Independent Test**: Edit scope/contents text, generate output, and verify defaults, order, and conditional meter suffix behavior.

### Implementation for User Story 3

- [X] T019 [US3] Add editable second-cover title/body fields for Scope and Contents in django_app/templates/sitesync/report.html
- [X] T020 [US3] Populate default scope text with site variable substitution in django_app/static/sitesync/js/report.js
- [X] T021 [US3] Generate contents entries from visual titles in display order in django_app/static/sitesync/js/report.js
- [X] T022 [US3] Apply conditional meter-name suffix rule for contents entries (except `Total Utility Usage (£)`) in django_app/static/sitesync/js/report.js
- [X] T023 [US3] Persist second-cover edited values through report generation lifecycle in django_app/static/sitesync/js/report.js

**Checkpoint**: User Story 3 is fully functional and independently testable.

---

## Phase 6: User Story 4 - Preserve cover content across PDF/PPTX outputs (Priority: P2)

**Goal**: Include full cover sequence in both export formats and preserve editability of front-cover fields in PPTX.

**Independent Test**: Download PDF and PPTX for the same report and verify full cover sequence in both files, editable front-cover fields in PPTX, and static back cover.

### Implementation for User Story 4

- [X] T024 [US4] Include front and back cover pages in PDF export assembly flow in django_app/static/sitesync/js/report.js
- [X] T025 [US4] Include front and back cover pages in PPTX export assembly flow in django_app/static/sitesync/js/report.js
- [X] T026 [US4] Map first- and second-cover text fields to native editable PPTX text objects in django_app/static/sitesync/js/report.js
- [X] T027 [US4] Export back cover as static image page in PPTX output in django_app/static/sitesync/js/report.js
- [X] T028 [US4] Align PDF/PPTX cover page ordering to the shared sequence contract in django_app/static/sitesync/js/report.js

**Checkpoint**: User Story 4 is fully functional and independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, Docker-based validation, and documentation alignment.

- [X] T029 [P] Add/update focused report cover feature tests in django_app/sitesync/tests/test_report_cover_pages.py
- [X] T030 [P] Add/update export integration checks in tests/integration/test_report_cover_exports.py
- [X] T031 Run Docker-based Django test suite via `docker compose -f django_app/docker/docker-compose.yml exec web python manage.py test` and address failures
- [ ] T032 Execute SC measurement protocol from spec (MP-001 and MP-002) in Docker-hosted flow and record pass/fail results in specs/007-add-report-cover-pages/quickstart.md
- [X] T033 [P] Update report export behavior notes in docs/API.md and django_app/README.md
- [X] T034 [P] Add a validation evidence table template for SC-003 and SC-006 in specs/007-add-report-cover-pages/quickstart.md (fields: run id, scenario, outcome, failure reason, threshold, pass rate)
- [ ] T035 Compute and document final pass-rate calculations for SC-003 and SC-006 in specs/007-add-report-cover-pages/quickstart.md and confirm threshold compliance (SC-003 >= 95%, SC-006 >= 95%)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all stories.
- **User Story Phases (Phase 3-6)**: Depend on Foundational completion.
- **Polish (Phase 7)**: Depends on completion of targeted user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; no dependency on other user stories.
- **US2 (P1)**: Starts after Foundational; independent from US1 except shared scaffolding.
- **US3 (P1)**: Starts after Foundational; independent from US1/US2 except shared scaffolding.
- **US4 (P2)**: Starts after Foundational; depends on cover data produced by US1, US2, and US3 for full export parity.

### Within Each User Story

- UI field definitions before export mapping.
- Default value generation before user override persistence.
- Cover state assembly before export integration.

### Parallel Opportunities

- Setup: T003 can run parallel with T001-T002.
- Foundational: T005 and T006 can run in parallel after T003.
- After Foundational: US1, US2, and US3 can be developed in parallel by different developers.
- Polish: T029 and T030 can run in parallel before T031.

---

## Parallel Example: User Story 1

```bash
Task: "Render front cover page 1 and front cover page 2 before report body in django_app/templates/sitesync/report.html"
Task: "Render back cover page after report body in django_app/templates/sitesync/report.html"
```

## Parallel Example: User Story 2

```bash
Task: "Add editable first-cover inputs (site title, month title, date, client logo area) in django_app/templates/sitesync/report.html"
Task: "Populate first-cover default values from selected site/report month/current date in django_app/static/sitesync/js/report.js"
```

## Parallel Example: User Story 3

```bash
Task: "Add editable second-cover title/body fields for Scope and Contents in django_app/templates/sitesync/report.html"
Task: "Generate contents entries from visual titles in display order in django_app/static/sitesync/js/report.js"
```

## Parallel Example: User Story 4

```bash
Task: "Include front and back cover pages in PDF export assembly flow in django_app/static/sitesync/js/report.js"
Task: "Include front and back cover pages in PPTX export assembly flow in django_app/static/sitesync/js/report.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate draft/final cover sequence before proceeding.

### Incremental Delivery

1. Deliver US1 for baseline cover insertion.
2. Deliver US2 for first-cover editability and upload validation.
3. Deliver US3 for second-cover scope/contents behavior.
4. Deliver US4 for export parity and PPTX editability.
5. Finish Phase 7 Docker validation and documentation updates.

### Parallel Team Strategy

1. Team completes Phase 1-2 together.
2. Split implementation: Developer A (US1), Developer B (US2), Developer C (US3).
3. Merge into US4 export parity work.
4. Complete Polish phase with Docker test execution and quickstart verification.
