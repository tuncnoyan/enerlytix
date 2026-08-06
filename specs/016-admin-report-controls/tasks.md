# Tasks: Saved Reports Admin Controls

**Input**: Design documents from /specs/016-admin-report-controls/

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are included for security-critical acceptance criteria (authorization, password confirmation, atomic deletion, and audit logging) and sorting behavior, with explicit timed validation for SC-004.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared constants, routes, and UI scaffolding needed by all stories

- [ ] T001 Define saved-reports bulk-delete audit action constants in django_app/sitesync/services.py
- [ ] T002 Add saved-reports sortable field allowlist and field-type direction map in django_app/sitesync/views.py
- [ ] T003 [P] Add placeholder bulk-delete form container and selection column header in django_app/templates/sitesync/saved_reports.html
- [ ] T004 [P] Add saved-reports client context placeholders for sort and bulk-delete state in django_app/static/sitesync/js/saved_reports.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared backend pipeline for sorting, authorization, atomic delete, and audit outcomes

**CRITICAL**: No user story implementation should begin until this phase is complete

- [ ] T005 Implement normalized sort-field parser with allowlist fallback in django_app/sitesync/views.py
- [ ] T006 Implement field-type default sort-direction resolver in django_app/sitesync/views.py
- [ ] T007 Implement platform-admin gate and password confirmation validator for bulk delete in django_app/sitesync/views.py
- [ ] T008 Implement selected report resolution constrained by get_accessible_reports scope in django_app/sitesync/views.py
- [ ] T009 Implement atomic bulk-delete transaction helper with blocking-reference detection in django_app/sitesync/services.py
- [ ] T010 Implement shared saved-reports audit event logger for success, denied, and failed outcomes in django_app/sitesync/views.py
- [ ] T011 Register POST bulk-delete route in django_app/sitesync/urls.py

**Checkpoint**: Shared sorting and secure bulk-delete foundation is complete

---

## Phase 3: User Story 1 - Platform Admin Bulk Report Deletion with Verification (Priority: P1) 🎯 MVP

**Goal**: Enable platform-admin-only multi-select report deletion with required password re-entry

**Independent Test**: Sign in as platform admin, select multiple reports, submit correct password, and verify only selected reports are deleted

### Tests for User Story 1

- [ ] T012 [P] [US1] Add integration test for admin-only visibility of row-selection and delete controls in django_app/sitesync/tests/test_saved_reports_view.py
- [ ] T013 [P] [US1] Add integration test for successful multi-select deletion with correct password in django_app/sitesync/tests/test_saved_reports_view.py
- [ ] T014 [P] [US1] Add integration test for incorrect-password denial with zero deletions in django_app/sitesync/tests/test_saved_reports_view.py

### Implementation for User Story 1

- [ ] T015 [US1] Add per-row left-side selection checkboxes and bulk-delete action UI in django_app/templates/sitesync/saved_reports.html
- [ ] T016 [US1] Implement saved_reports_bulk_delete_view POST handler with admin/password checks in django_app/sitesync/views.py
- [ ] T017 [US1] Implement selected row ID serialization and bulk-delete submit behavior in django_app/static/sitesync/js/saved_reports.js
- [ ] T018 [US1] Add success and failure message rendering for delete outcomes in django_app/templates/sitesync/saved_reports.html
- [ ] T019 [US1] Wire deleted-row refresh behavior after successful delete in django_app/static/sitesync/js/saved_reports.js

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Sort Saved Reports by Dropdown Field Selection (Priority: P2)

**Goal**: Let users reorder reports by selecting a sort field while preserving active filters

**Independent Test**: Select each sort field from dropdown and verify filtered list ordering updates with field-based default direction

### Tests for User Story 2

- [ ] T020 [P] [US2] Add contract-style test for sort-field allowlist and unknown-field fallback in django_app/sitesync/tests/test_saved_reports_view.py
- [ ] T021 [P] [US2] Add integration tests for field-based default sort directions in django_app/sitesync/tests/test_saved_reports_team_context.py

### Implementation for User Story 2

- [ ] T022 [US2] Add sort-field dropdown control with persisted selection state in django_app/templates/sitesync/saved_reports.html
- [ ] T023 [US2] Apply sort-field ordering in saved_reports_view queryset pipeline in django_app/sitesync/views.py
- [ ] T024 [US2] Add normalized sort payload to HTML context and JSON response in django_app/sitesync/views.py
- [ ] T025 [US2] Implement sort-change submission that preserves active filters in django_app/static/sitesync/js/saved_reports.js

**Checkpoint**: User Stories 1 and 2 work independently with secure deletion and sortable listing

---

## Phase 5: User Story 3 - Safe and Transparent Bulk-Delete UX (Priority: P3)

**Goal**: Prevent accidental loss and ensure denied/failed delete attempts are explicit and auditable

**Independent Test**: Attempt delete with no selection, with blocked selection, and as non-admin direct POST; verify messages, zero unintended deletions, and audit rows

### Tests for User Story 3

- [ ] T026 [P] [US3] Add integration test for no-selection guard and clear feedback message in django_app/sitesync/tests/test_saved_reports_view.py
- [ ] T027 [P] [US3] Add integration test for atomic all-or-nothing failure with blocking references in django_app/sitesync/tests/test_saved_reports_ownership_listing.py
- [ ] T028 [P] [US3] Add audit integration test for unauthorized direct bulk-delete POST logging in django_app/sitesync/tests/test_audit_helpers.py

### Implementation for User Story 3

- [ ] T029 [US3] Implement no-selection validation path in saved_reports_bulk_delete_view in django_app/sitesync/views.py
- [ ] T030 [US3] Implement atomic-failure response payload including blocked report references in django_app/sitesync/views.py
- [ ] T031 [US3] Implement unauthorized direct-request denied audit logging for bulk delete in django_app/sitesync/views.py
- [ ] T032 [US3] Add confirmation summary text showing selected report count before submit in django_app/templates/sitesync/saved_reports.html
- [ ] T033 [US3] Render blocked-reference and denied-attempt feedback states in django_app/templates/sitesync/saved_reports.html

**Checkpoint**: All user stories are independently functional, safe, and auditable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final contract alignment, Docker-native validation, and release readiness

- [ ] T034 [P] Update saved-reports admin-controls contract with final request/response details in specs/016-admin-report-controls/contracts/saved-reports-admin-controls.md
- [ ] T035 [P] Update manual validation flow and expected outcomes in specs/016-admin-report-controls/quickstart.md
- [ ] T036 Run Docker-native targeted test command for saved-reports and audit scenarios; capture output notes in specs/016-admin-report-controls/quickstart.md
- [ ] T037 Run Docker-native full regression command and record pass/fail snapshot in specs/016-admin-report-controls/quickstart.md
- [ ] T038 Run timed sorting usability validation for SC-004 in Docker environment using 5 moderated runs and record per-run elapsed seconds in specs/016-admin-report-controls/quickstart.md; pass only if all runs are 10 seconds or less

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): No dependencies; can start immediately
- Phase 2 (Foundational): Depends on Phase 1; blocks all user stories
- Phase 3 (US1): Depends on Phase 2
- Phase 4 (US2): Depends on Phase 2 and can run in parallel with US1
- Phase 5 (US3): Depends on Phase 3 and Phase 4 because it validates delete safety while preserving sort/list state
- Phase 6 (Polish): Depends on completion of all user stories

### User Story Dependencies

- US1 (P1): Depends only on Foundational phase
- US2 (P2): Depends only on Foundational phase
- US3 (P3): Depends on US1 delete workflow and US2 list/sort state behavior

### Within Each User Story

- Tests should be authored before implementation tasks and should fail before implementation
- Backend authorization and transaction paths before UI polish messages
- Story checkpoint validation before moving to next phase

### Parallel Opportunities

- T003 and T004 can run in parallel
- T012, T013, and T014 can run in parallel
- T020 and T021 can run in parallel
- T026, T027, and T028 can run in parallel
- T034 and T035 can run in parallel

---

## Parallel Example: User Story 1

- Task: T012 [US1] admin-control visibility test in django_app/sitesync/tests/test_saved_reports_view.py
- Task: T013 [US1] successful deletion test in django_app/sitesync/tests/test_saved_reports_view.py
- Task: T014 [US1] invalid-password denial test in django_app/sitesync/tests/test_saved_reports_view.py

---

## Parallel Example: User Story 2

- Task: T020 [US2] sort allowlist/fallback test in django_app/sitesync/tests/test_saved_reports_view.py
- Task: T021 [US2] sort direction behavior tests in django_app/sitesync/tests/test_saved_reports_team_context.py

---

## Parallel Example: User Story 3

- Task: T026 [US3] no-selection guard test in django_app/sitesync/tests/test_saved_reports_view.py
- Task: T027 [US3] atomic failure test in django_app/sitesync/tests/test_saved_reports_ownership_listing.py
- Task: T028 [US3] unauthorized-attempt audit test in django_app/sitesync/tests/test_audit_helpers.py

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2 foundations
2. Complete Phase 3 (US1)
3. Validate US1 independently with targeted Docker tests
4. Demo/deploy MVP

### Incremental Delivery

1. Deliver US1 (secure admin bulk deletion)
2. Deliver US2 (sortable listing)
3. Deliver US3 (safety and audit transparency)
4. Run polish and full regression

### Parallel Team Strategy

1. Team completes Setup and Foundational together
2. After Foundational:
   - Developer A: US1 backend and UI deletion workflow
   - Developer B: US2 sorting pipeline and dropdown UI
   - Developer C: US3 safety and audit hardening
3. Finish with shared polish and regression validation
