# Tasks: Available Capacity Upload

**Input**: Design documents from `/specs/005-available-capacity-upload/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Add focused Django automated tests for upload parsing, settings-page feedback, and report capacity resolution because the implementation plan expects verification through the existing test suite.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the dependency and shared constants needed by the upload workflow.

- [ ] T001 Add `openpyxl` dependency to `requirements.txt`
- [ ] T002 [P] Add `openpyxl` dependency to `django_app/requirements.txt`
- [ ] T003 [P] Add `openpyxl` dependency to `Pipfile`
- [ ] T004 Define capacity-upload header, status, and validation message constants in `django_app/sitesync/services.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the persistence and shared processing primitives required by all user stories.

**⚠️ CRITICAL**: No user story work should start before this phase is complete.

- [ ] T005 Add `CapacityReference` and `CapacityUploadRun` models to `django_app/sitesync/models.py`
- [ ] T006 Create migration `django_app/sitesync/migrations/0007_capacity_upload_models.py` for the new capacity models
- [ ] T007 [P] Implement reusable eSight meter code normalization helpers in `django_app/sitesync/services.py`
- [ ] T008 [P] Implement workbook loading, worksheet extraction, and header normalization helpers in `django_app/sitesync/services.py`
- [ ] T009 Extend the settings upload form for `.xlsx` file submission in `django_app/sitesync/forms.py`
- [ ] T010 Create a structured capacity import result builder in `django_app/sitesync/services.py`
- [ ] T011 [P] Add service-level upload parsing and validation tests in `django_app/sitesync/tests/test_capacity_upload.py`

**Checkpoint**: Foundation ready; user story implementation can begin.

---

## Phase 3: User Story 1 - Upload Available Capacity File (Priority: P1) 🎯 MVP

**Goal**: Let operations users upload valid `.xlsx` capacity data on Settings and show matched capacity values in electricity load factor output.

**Independent Test**: Upload a valid `.xlsx` file from Settings and confirm matched electricity meters show numeric `Available Capacity (kVA)` values in the report load factor section.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add successful upload and report-resolution integration tests in `django_app/sitesync/tests/test_capacity_upload.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement valid-row import and upsert processing for capacity uploads in `django_app/sitesync/services.py`
- [ ] T014 [US1] Add the capacity-upload POST handling path to `django_app/sitesync/views.py`
- [ ] T015 [P] [US1] Add the Available Capacity upload section and file input to `django_app/templates/sitesync/settings_panel.html`
- [ ] T016 [US1] Integrate `available_capacity_kva` lookup into electricity report payload assembly in `django_app/sitesync/views.py`
- [ ] T017 [P] [US1] Update load factor label and available-capacity rendering to `Available Capacity (kVA)` in `django_app/static/sitesync/js/report.js`
- [ ] T018 [US1] Render successful upload summary counts in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: User Story 1 delivers end-to-end upload and report display value.

---

## Phase 4: User Story 2 - Validate File Structure and Data Quality (Priority: P2)

**Goal**: Provide robust validation and row-level feedback while preserving partial-import behavior.

**Independent Test**: Upload malformed and mixed-quality files and verify invalid rows are skipped with explicit reasons while valid rows are still imported.

### Tests for User Story 2

- [ ] T019 [P] [US2] Add invalid-header, duplicate-code, non-numeric, and negative-capacity tests in `django_app/sitesync/tests/test_capacity_upload.py`
- [ ] T020 [P] [US2] Add settings-page validation messaging tests in `django_app/sitesync/tests/test_settings_view.py`

### Implementation for User Story 2

- [ ] T021 [US2] Enforce required-header validation for `Name`, `eSight Meter Code`, and `Av Cap (kVA)` in `django_app/sitesync/services.py`
- [ ] T022 [US2] Enforce blank-field, non-numeric, and negative-capacity row validation in `django_app/sitesync/services.py`
- [ ] T023 [US2] Enforce duplicate `eSight Meter Code` detection and partial-import skip behavior in `django_app/sitesync/services.py`
- [ ] T024 [US2] Reject non-`.xlsx` uploads with a supported-format message in `django_app/sitesync/forms.py`
- [ ] T025 [US2] Pass `failed` and `partial_success` upload statuses plus row-level errors from `django_app/sitesync/views.py`
- [ ] T026 [P] [US2] Render validation errors, partial-import notices, and supported-format messaging in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: User Story 2 produces clear, actionable import validation outcomes.

---

## Phase 5: User Story 3 - Refresh Static Capacity Data Over Time (Priority: P3)

**Goal**: Support periodic re-uploads that refresh existing meter capacities and stored reference names without deleting unrelated records.

**Independent Test**: Upload a baseline file and then a revised file with changed capacities and a changed `Name` for one existing code; verify matched keys use the latest uploaded values while omitted keys remain available.

### Tests for User Story 3

- [ ] T027 [P] [US3] Add overwrite-on-match and append-update persistence tests in `django_app/sitesync/tests/test_capacity_upload.py`
- [ ] T028 [P] [US3] Add latest-value report resolution tests in `django_app/sitesync/tests/test_report_drafts.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement overwrite-on-match upsert logic for `name` and `available_capacity_kva` in `django_app/sitesync/services.py`
- [ ] T030 [US3] Preserve unmatched existing capacity references during append-update imports in `django_app/sitesync/services.py`
- [ ] T031 [US3] Persist upload audit metadata, row counts, and aggregate error details through `django_app/sitesync/services.py`
- [ ] T032 [US3] Surface the latest upload run summary and metadata in `django_app/sitesync/views.py`
- [ ] T033 [P] [US3] Display latest upload run filename, timestamp, and status in `django_app/templates/sitesync/settings_panel.html`
- [ ] T034 [US3] Ensure report capacity resolution always uses the latest imported reference value in `django_app/sitesync/views.py`

**Checkpoint**: User Story 3 completes the refresh and maintenance lifecycle for stored capacity data.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and executable validation across the feature.

- [ ] T035 Update available-capacity upload documentation in `docs/API.md`
- [ ] T036 Align `Available Capacity (kVA)` wording in `django_app/sitesync/models.py` and `django_app/sitesync/services.py`
- [ ] T037 Update validation and refresh walkthroughs in `specs/005-available-capacity-upload/quickstart.md`
- [ ] T038 Run the quickstart validation scenarios and record results in `specs/005-available-capacity-upload/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and builds on the upload flow from US1.
- **Phase 5 (US3)**: Depends on Phase 2 and benefits from the import pipeline established in US1 and US2.
- **Phase 6 (Polish)**: Depends on completion of the desired user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; MVP slice.
- **US2 (P2)**: Extends US1 upload behavior with strict validation and user feedback.
- **US3 (P3)**: Extends persistence lifecycle and refresh behavior without requiring a purge mode.

### Within Each User Story

- Shared service/model work before view wiring.
- View context before template rendering.
- Upload pipeline work before report integration validation.

## Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel after T001 confirms dependency scope.
- **Foundational**: T007 and T008 can run in parallel after T005 and T006 establish the persistence model.
- **US1**: T015 and T017 can run in parallel with backend import work in T013 and T014.
- **US2**: T026 can run in parallel after T025 defines the view context contract.
- **US3**: T033 can run in parallel with T031 and T032 once upload-run metadata fields are finalized.

## Parallel Example: User Story 1

```bash
Task: "T013 [US1] Implement valid-row import and upsert processing in django_app/sitesync/services.py"
Task: "T015 [US1] Add the Available Capacity upload section in django_app/templates/sitesync/settings_panel.html"
Task: "T017 [US1] Update load factor label in django_app/static/sitesync/js/report.js"
```

## Parallel Example: User Story 3

```bash
Task: "T031 [US3] Persist upload audit metadata in django_app/sitesync/services.py"
Task: "T033 [US3] Display latest upload run metadata in django_app/templates/sitesync/settings_panel.html"
```

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks in Phase 3.
3. Validate with the successful-upload scenario in `specs/005-available-capacity-upload/quickstart.md` before moving forward.

### Incremental Delivery

1. Deliver US1 for immediate business value: upload and display capacity values in reports.
2. Add US2 for strict validation, negative-value rejection, and row-level feedback.
3. Add US3 for overwrite-on-match refresh behavior and upload audit visibility.
4. Finish with documentation and quickstart validation in Phase 6.

### Team Parallelization Strategy

1. One developer focuses on models, migrations, core services, and service-level tests in T005-T013 and T029-T031.
2. One developer focuses on views, settings feedback, and template work in T014-T018, T020, T025-T026, and T032-T033.
3. One developer focuses on report integration, report tests, wording alignment, and validation in T016-T017, T028, T034-T038.
