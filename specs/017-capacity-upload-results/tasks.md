# Tasks: Capacity Upload Results UX

**Input**: Design documents from `/specs/017-capacity-upload-results/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are included for UX simplification, export correctness, access control, and edge-case handling because the specification defines explicit independent test scenarios and measurable outcomes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare constants, route skeleton, and template placeholders for upload-results export.

- [ ] T001 Define capacity-upload results export constants (sheet names, column labels, outcome values) in `django_app/sitesync/services.py`
- [ ] T002 [P] Add a capacity upload results download action placeholder near latest-run summary in `django_app/templates/sitesync/settings_panel.html`
- [ ] T003 Add export route placeholder for latest upload results workbook in `django_app/sitesync/urls.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build durable row-result persistence and export building blocks used by all stories.

**CRITICAL**: No user story implementation should begin until this phase is complete.

- [ ] T004 Add `CapacityUploadRowResult` model (run FK, source row number, outcome, explanation, original columns JSON) in `django_app/sitesync/models.py`
- [ ] T005 Create migration `django_app/sitesync/migrations/0027_capacity_upload_row_results.py` for `CapacityUploadRowResult`
- [ ] T006 Implement row-result persistence helpers for success/failure rows in `django_app/sitesync/services.py`
- [ ] T007 Implement latest-completed-run resolution helper for results export in `django_app/sitesync/services.py`
- [ ] T008 Implement two-sheet workbook builder (`Successes`, `Failures`) with shared schema in `django_app/sitesync/services.py`
- [ ] T009 Implement export endpoint skeleton with access checks and response headers in `django_app/sitesync/views.py`
- [ ] T010 Wire `settings_panel_view` context to expose export availability for latest run in `django_app/sitesync/views.py`

**Checkpoint**: Persistence and export foundations are ready; user story work can proceed.

---

## Phase 3: User Story 1 - Streamlined Upload Outcome View (Priority: P1) 🎯 MVP

**Goal**: Remove long inline per-row issue lists from settings while preserving concise status and summary blocks.

**Independent Test**: Upload a file with many failures and verify settings page does not render row-by-row inline issue list but still shows status and latest-run summary.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add settings-page regression test asserting no inline upload-errors list is rendered in `django_app/sitesync/tests/test_settings_view.py`
- [ ] T012 [P] [US1] Add settings-page regression test asserting status notice and latest-run summary remain visible in `django_app/sitesync/tests/test_settings_view.py`

### Implementation for User Story 1

- [ ] T013 [US1] Remove inline error-list rendering block from available-capacity section in `django_app/templates/sitesync/settings_panel.html`
- [ ] T014 [US1] Update `settings_panel_view` context usage so aggregate status/summary remains without requiring inline row-error display in `django_app/sitesync/views.py`
- [ ] T015 [US1] Ensure upload notices and latest-run summary text stay concise and stable for large runs in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: US1 delivers readable settings UX even for high-error uploads.

---

## Phase 4: User Story 2 - Downloadable Full Results (Priority: P1)

**Goal**: Provide a download button that exports latest run results to Excel with separate Successes and Failures sheets.

**Independent Test**: Complete an upload and download workbook from settings; verify file downloads and includes both `Successes` and `Failures` worksheets.

### Tests for User Story 2

- [ ] T016 [P] [US2] Add endpoint authorization and content-type tests for results export in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- [ ] T017 [P] [US2] Add workbook shape test asserting exactly `Successes` and `Failures` sheets in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- [ ] T018 [P] [US2] Add no-latest-run and no-row-results feedback tests in `django_app/sitesync/tests/test_capacity_upload_results_export.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement export endpoint behavior (`GET /settings/capacity-upload/results.xlsx`) in `django_app/sitesync/views.py`
- [ ] T020 [US2] Register export route name `capacity_upload_results_export` in `django_app/sitesync/urls.py`
- [ ] T021 [US2] Implement workbook response builder and attachment naming for latest run in `django_app/sitesync/services.py`
- [ ] T022 [US2] Render active download action only when latest run has persisted row outcomes in `django_app/templates/sitesync/settings_panel.html`

**Checkpoint**: US2 delivers downloadable full upload outcomes without reintroducing inline list bloat.

---

## Phase 5: User Story 3 - Actionable Result Records for Follow-up (Priority: P2)

**Goal**: Export rows are self-explanatory and include full source context for remediation.

**Independent Test**: Open exported workbook and verify each row includes row number, original upload columns, outcome, and explanation; failed rows include all reasons combined.

### Tests for User Story 3

- [ ] T023 [P] [US3] Add service test for per-row persistence of source row number and original columns in `django_app/sitesync/tests/test_capacity_upload.py`
- [ ] T024 [P] [US3] Add export test asserting row schema includes source row number, original columns, outcome, explanation in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- [ ] T025 [P] [US3] Add export test asserting multi-error failures are combined into one explanation cell for one failed row in `django_app/sitesync/tests/test_capacity_upload_results_export.py`

### Implementation for User Story 3

- [ ] T026 [US3] Persist success and failure row results during import processing in `django_app/sitesync/services.py`
- [ ] T027 [US3] Persist combined validation reasons into a single failure explanation field in `django_app/sitesync/services.py`
- [ ] T028 [US3] Materialize export rows with required schema across both sheets in `django_app/sitesync/services.py`

**Checkpoint**: US3 makes exported data directly usable for correction and retry workflows.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, run Docker validations, and confirm release readiness.

- [ ] T029 [P] Update export contract details with final status/error semantics in `specs/017-capacity-upload-results/contracts/capacity-upload-results-export.md`
- [ ] T030 [P] Update validation scenarios and expected workbook checks in `specs/017-capacity-upload-results/quickstart.md`
- [ ] T031 Run targeted Docker tests for capacity upload + settings + export and record results in `specs/017-capacity-upload-results/quickstart.md`
- [ ] T032 Run Docker full regression and record pass/fail snapshot in `specs/017-capacity-upload-results/quickstart.md`
- [ ] T033 Run timed SC-005 usability validation (identify at least one failed-row cause from downloaded workbook within 2 minutes) and record per-run timings in specs/017-capacity-upload-results/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): no dependencies.
- Phase 2 (Foundational): depends on Phase 1 and blocks all user stories.
- Phase 3 (US1): depends on Phase 2.
- Phase 4 (US2): depends on Phase 2 and can proceed after foundations are complete.
- Phase 5 (US3): depends on Phase 2 and leverages US2 export surface.
- Phase 6 (Polish): depends on completion of desired user stories.

### User Story Dependencies

- US1 (P1): independent after foundational phase.
- US2 (P1): independent after foundational phase; can be delivered alongside US1.
- US3 (P2): depends on foundational persistence and export pipeline from US2.

### Within Each User Story

- Tests are written first and expected to fail before implementation.
- Backend persistence/service changes precede view/template integration.
- Endpoint and UI wiring precede polish documentation updates.

### Parallel Opportunities

- T002 can run in parallel with T001/T003.
- T011 and T012 can run in parallel.
- T016, T017, and T018 can run in parallel.
- T023, T024, and T025 can run in parallel.
- T029 and T030 can run in parallel.

---

## Parallel Example: User Story 2

- Task: `T016 [US2]` endpoint authorization/content-type tests in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- Task: `T017 [US2]` workbook-shape tests in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- Task: `T018 [US2]` no-data feedback tests in `django_app/sitesync/tests/test_capacity_upload_results_export.py`

---

## Parallel Example: User Story 3

- Task: `T023 [US3]` row-result persistence tests in `django_app/sitesync/tests/test_capacity_upload.py`
- Task: `T024 [US3]` export schema test in `django_app/sitesync/tests/test_capacity_upload_results_export.py`
- Task: `T025 [US3]` combined-failure explanation test in `django_app/sitesync/tests/test_capacity_upload_results_export.py`

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1 and Phase 2 foundations.
2. Deliver US1 to remove unusable inline issue list.
3. Deliver US2 to provide workbook download replacement.
4. Validate targeted scenarios before broader rollout.

### Incremental Delivery

1. Deliver US1 readability improvements.
2. Deliver US2 export availability and access/error handling.
3. Deliver US3 rich row-level remediation details.
4. Finish with polish and full Docker regression.

### Parallel Team Strategy

1. One developer implements model/migration/service foundations (T004-T008).
2. One developer implements endpoint/template wiring (T009-T022).
3. One developer drives test expansion and validation artifacts (T011-T012, T016-T018, T023-T025, T029-T032).
