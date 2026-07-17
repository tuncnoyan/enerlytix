# Tasks: Average Capacity Integration

**Input**: Design documents from `/specs/005-available-capacity-upload/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: No automated test tasks are included because the specification did not explicitly request TDD or test-first delivery.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add baseline dependency and shared constants needed by upload implementation.

- [ ] T001 Add `.xlsx` parser dependency `openpyxl` to `requirements.txt`
- [ ] T002 [P] Add `.xlsx` parser dependency `openpyxl` to `django_app/requirements.txt`
- [ ] T003 [P] Add `.xlsx` parser dependency `openpyxl` to `Pipfile`
- [ ] T004 Define capacity-upload required header constants in `django_app/sitesync/services.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create persistence and shared processing primitives required by all stories.

**⚠️ CRITICAL**: No user story work should start before this phase is complete.

- [ ] T005 Add `CapacityReference` model in `django_app/sitesync/models.py`
- [ ] T006 Add `CapacityUploadRun` model in `django_app/sitesync/models.py`
- [ ] T007 Create migration for new capacity models in `django_app/sitesync/migrations/0007_capacity_upload_models.py`
- [ ] T008 Implement reusable eSight meter code normalization helper in `django_app/sitesync/services.py`
- [ ] T009 Implement workbook loading/worksheet extraction helper for `.xlsx` files in `django_app/sitesync/services.py`
- [ ] T010 Extend settings forms for file upload support in `django_app/sitesync/forms.py`

**Checkpoint**: Foundation ready - user story implementation can begin.

---

## Phase 3: User Story 1 - Upload Available Capacity File (Priority: P1) 🎯 MVP

**Goal**: Allow operations users to upload `.xlsx` capacity data on Settings and show mapped values in electricity load factor.

**Independent Test**: Upload valid `.xlsx` data from Settings and confirm matched electricity meters show numeric `Available Capacity (kVA)` in report load factor cards.

### Implementation for User Story 1

- [ ] T011 [US1] Add capacity-upload POST handling path to `settings_panel_view` in `django_app/sitesync/views.py`
- [ ] T012 [P] [US1] Add Available Capacity upload section and file input form in `django_app/templates/sitesync/settings_panel.html`
- [ ] T013 [US1] Implement accepted-row import path that stores capacity records by eSight code in `django_app/sitesync/services.py`
- [ ] T014 [US1] Integrate capacity lookup by supply meter code in report payload builder in `django_app/sitesync/views.py`
- [ ] T015 [P] [US1] Update load factor metric label to `Available Capacity (kVA)` in `django_app/static/sitesync/js/report.js`
- [ ] T016 [US1] Render upload success summary values (total/accepted/rejected) in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: User Story 1 delivers end-to-end upload + report display value.

---

## Phase 4: User Story 2 - Validate File Structure and Data Quality (Priority: P2)

**Goal**: Provide robust validation and row-level feedback while preserving partial-import behavior.

**Independent Test**: Upload malformed and mixed-quality files, then verify invalid rows are skipped with explicit row-level reasons while valid rows are still imported.

### Implementation for User Story 2

- [ ] T017 [US2] Validate required headers (`Name`, `eSight Meter Code`, `Av Cap (kVA)`) and fail schema-invalid files in `django_app/sitesync/services.py`
- [ ] T018 [US2] Validate blank key fields and non-numeric capacity values with row-indexed errors in `django_app/sitesync/services.py`
- [ ] T019 [US2] Detect duplicate eSight meter codes within a single file and skip duplicates in `django_app/sitesync/services.py`
- [ ] T020 [US2] Enforce non-`.xlsx` upload rejection with supported-format message in `django_app/sitesync/forms.py`
- [ ] T021 [US2] Pass partial-success/failure status and row-level error payload from `settings_panel_view` in `django_app/sitesync/views.py`
- [ ] T022 [P] [US2] Render validation errors and partial-import notices in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: User Story 2 produces clear, actionable import validation outcomes.

---

## Phase 5: User Story 3 - Refresh Static Capacity Data Over Time (Priority: P3)

**Goal**: Support periodic re-uploads that refresh existing meter capacities without deleting unrelated stored records.

**Independent Test**: Upload baseline file then revised file; verify updated codes use latest values while non-mentioned existing codes remain available.

### Implementation for User Story 3

- [ ] T023 [US3] Implement upsert-by-eSight-code refresh logic for valid rows in `django_app/sitesync/services.py`
- [ ] T024 [US3] Preserve unmatched existing capacity records during incremental uploads in `django_app/sitesync/services.py`
- [ ] T025 [US3] Persist upload audit metadata and row counts in `CapacityUploadRun` via `django_app/sitesync/services.py`
- [ ] T026 [US3] Surface latest upload run summary context in `settings_panel_view` in `django_app/sitesync/views.py`
- [ ] T027 [P] [US3] Display latest upload run details in `django_app/templates/sitesync/settings_panel.html`
- [ ] T028 [US3] Ensure report load-factor resolution uses latest imported capacity record values in `django_app/sitesync/views.py`

**Checkpoint**: User Story 3 completes long-term maintainability for static reference data refreshes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and manual validation.

- [ ] T029 Update API/feature documentation for capacity upload behavior in `docs/API.md`
- [ ] T030 Align capacity unit wording (`kVA`) in model help text and related server payload comments in `django_app/sitesync/models.py`
- [ ] T031 Execute quickstart validation scenarios and capture run notes in `specs/005-available-capacity-upload/quickstart.md`
- [ ] T032 Measure and record SC-001 timing (valid-row availability within 1 minute) in `specs/005-available-capacity-upload/quickstart.md`
- [ ] T033 Measure and record SC-003 match-rate (>=95% matched electricity meters show numeric capacity) in `specs/005-available-capacity-upload/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and builds on US1 upload flow.
- **Phase 5 (US3)**: Depends on Phase 2 and benefits from US1/US2 import pipeline completion.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; MVP slice.
- **US2 (P2)**: Extends US1 upload behavior with strict validation feedback.
- **US3 (P3)**: Extends persistence lifecycle for refresh and audit behavior.

### Within Each User Story

- Data/model logic before view wiring.
- View context before template rendering.
- Upload pipeline updates before report integration validation.

## Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel after T001 scope is clear.
- **US1**: T012 and T015 can run in parallel with backend task T013.
- **US2**: T022 can run in parallel after T021 context contract is defined.
- **US3**: T027 can run in parallel with T025/T026 once summary fields are finalized.

## Parallel Example: User Story 1

```bash
# Backend and UI tasks that can proceed concurrently:
Task: "T013 [US1] Implement accepted-row import path in django_app/sitesync/services.py"
Task: "T012 [US1] Add upload section in django_app/templates/sitesync/settings_panel.html"
Task: "T015 [US1] Update load-factor label in django_app/static/sitesync/js/report.js"
```

## Parallel Example: User Story 3

```bash
# Persist/audit and template rendering can overlap after context shape is agreed:
Task: "T025 [US3] Persist upload audit metadata in django_app/sitesync/services.py"
Task: "T027 [US3] Display latest upload run details in django_app/templates/sitesync/settings_panel.html"
```

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate with quickstart Scenario 1 before moving forward.

### Incremental Delivery

1. Deliver US1 for immediate business value (capacity visible in reports).
2. Add US2 for robust operational validation and feedback.
3. Add US3 for lifecycle refresh and audit traceability.
4. Finish with polish/documentation and final quickstart run.

### Team Parallelization Strategy

1. One developer focuses on models/migrations/services (T005-T009, T023-T025).
2. One developer focuses on views/templates UX feedback (T011-T012, T016, T021-T022, T026-T027).
3. One developer focuses on report integration and docs/validation (T014-T015, T028-T033).
