# Tasks: Saved Reports Search and Filters

**Input**: Design documents from `/specs/015-report-search-filters/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are included for critical acceptance criteria and measurable outcomes (SC-003 and SC-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare saved-reports filter scaffolding and shared defaults used by all stories

- [X] T001 Define saved-reports filter parameter names and status allowlists in `django_app/sitesync/views.py`
- [X] T002 Add month-key normalization and comparison helpers for start/end month criteria in `django_app/sitesync/views.py`
- [X] T003 Add filter-state serialization helper for HTML context and JSON responses in `django_app/sitesync/views.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core filter parsing and combined-query pipeline before story-specific UI behavior

**CRITICAL**: No user story implementation should begin until this phase is complete

- [X] T004 Implement canonical query-param parsing for `site_query`, `user_query`, `start_month`, `end_month`, `report_status`, and `validation_status` in `django_app/sitesync/views.py`
- [X] T005 Implement invalid month-range guard (`start_month > end_month`) with deterministic error/feedback response in `django_app/sitesync/views.py`
- [X] T006 Build combined filter application pipeline over accessible reports queryset and payload rows in `django_app/sitesync/views.py`
- [X] T007 Return normalized `selected_filters` in JSON mode and filter state in template context from `django_app/sitesync/views.py`

**Checkpoint**: Shared filtering core is in place and user stories can be implemented safely

---

## Phase 3: User Story 1 - Find Reports by Site and User (Priority: P1) 🎯 MVP

**Goal**: Let users quickly locate reports by site name and one username field spanning OWNER, LAST EDITED BY, and VALIDATOR

**Independent Test**: Enter a partial site value and a partial username on `/reports/` and verify only matching rows are displayed

### Implementation for User Story 1

- [X] T008 [US1] Add Site and User search controls (single username box) to saved reports UI in `django_app/templates/sitesync/saved_reports.html`
- [X] T009 [US1] Apply case-insensitive contains matching for site-name filtering in `django_app/sitesync/views.py`
- [X] T010 [US1] Apply case-insensitive contains matching for cross-column user filtering (owner, last editor, validator) in `django_app/sitesync/views.py`
- [X] T011 [P] [US1] Render active search values back into input controls on page load in `django_app/templates/sitesync/saved_reports.html`
- [X] T012 [P] [US1] Add lightweight client behavior to submit search changes and preserve current criteria state in `django_app/static/sitesync/js/saved_reports.js`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Narrow by Month and Statuses (Priority: P1)

**Goal**: Allow users to constrain reports by Start/End month and status checkbox groups with default-all selections

**Independent Test**: Apply month and status filters, confirm inclusive month range, default selections, and correct row exclusion behavior

### Implementation for User Story 2

- [X] T013 [US2] Add Start Month and End Month filter controls (month-year precision) in `django_app/templates/sitesync/saved_reports.html`
- [X] T014 [US2] Add Report Status and Validation Status checkbox groups with default-all rendering logic in `django_app/templates/sitesync/saved_reports.html`
- [X] T015 [US2] Apply inclusive month-range filtering (`start_month <= reporting_month <= end_month`) in `django_app/sitesync/views.py`
- [X] T016 [US2] Apply report-status checkbox filtering (`draft`, `final`) in `django_app/sitesync/views.py`
- [X] T017 [US2] Apply validation-status checkbox filtering (`draft`, `awaiting_validation`, `validated`) in `django_app/sitesync/views.py`
- [X] T018 [P] [US2] Add client-side form serialization for repeated checkbox params and month filters in `django_app/static/sitesync/js/saved_reports.js`

**Checkpoint**: User Stories 1 and 2 both work independently with default and narrowed filter behavior

---

## Phase 5: User Story 3 - Maintain Clear Results Under Combined Filters (Priority: P2)

**Goal**: Make combined-filter and restrictive-filter behavior predictable, including explicit empty states and easy criteria adjustments

**Independent Test**: Apply restrictive combined criteria to reach zero rows, then remove one criterion and verify rows recalculate correctly

### Implementation for User Story 3

- [X] T019 [US3] Add explicit empty-state messaging for zero results under active criteria in `django_app/templates/sitesync/saved_reports.html`
- [X] T020 [US3] Ensure all-status-unticked behavior is treated as valid and yields zero rows in `django_app/sitesync/views.py`
- [X] T021 [US3] Add invalid month-range correction messaging (non-misleading) to saved reports page in `django_app/templates/sitesync/saved_reports.html`
- [X] T022 [P] [US3] Add clear/reset-filters action while preserving authorization-scoped listing behavior in `django_app/templates/sitesync/saved_reports.html`
- [X] T023 [P] [US3] Keep table and empty-state rendering synchronized after criteria changes in `django_app/static/sitesync/js/saved_reports.js`

**Checkpoint**: All three user stories are independently functional and combined-filter UX is predictable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, contract alignment, and Docker-native validation

- [X] T024 [P] Update saved-reports contract details if implementation-level parameter names or error semantics changed in `specs/015-report-search-filters/contracts/saved-reports-search-filters.md`
- [X] T025 [P] Update manual validation notes to reflect final UI labels and interactions in `specs/015-report-search-filters/quickstart.md`
- [X] T026 Run Docker-native targeted saved-reports regression command and capture output notes in `specs/015-report-search-filters/quickstart.md`
- [X] T027 Run Docker-native full regression command and log final pass/fail snapshot in `specs/015-report-search-filters/quickstart.md`
- [X] T028 Add saved reports filter contract tests for invalid month range and selected_filters payload in `django_app/sitesync/tests/test_saved_reports_view.py`
- [X] T029 Add integration tests for default checked statuses (report and validation groups) on first load in `django_app/sitesync/tests/test_saved_reports_view.py`
- [X] T030 Add integration tests for case-insensitive Site/User contains filtering across owner, last editor, and validator fields in `django_app/sitesync/tests/test_saved_reports_ownership_listing.py`
- [X] T031 Add integration tests for combined criteria accuracy and all-status-unticked zero-result behavior in `django_app/sitesync/tests/test_saved_reports_team_context.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2; can run in parallel with US1 if staffed
- **Phase 5 (US3)**: Depends on completion of US1 and US2 behavior
- **Phase 6 (Polish)**: Depends on completion of all user stories

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational phase
- **US2 (P1)**: Depends only on Foundational phase
- **US3 (P2)**: Depends on combined outputs from US1 and US2

### Within Each User Story

- Backend filter logic before final UI/interaction polish for that story
- Template controls before JS-enhanced submission behavior
- Story checkpoint validation before moving to the next phase

### Parallel Opportunities

- Phase 3: T011 and T012 can run in parallel after T008-T010
- Phase 4: T018 can run in parallel once template checkbox/month controls exist
- Phase 5: T022 and T023 can run in parallel after core empty-state behavior is defined
- Phase 6: T024 and T025 can run in parallel; regression runs (T026-T027) remain sequential

---

## Parallel Example: User Story 1

```text
Run in parallel after T008-T010:
- T011 [US1] Render active search values back into input controls in django_app/templates/sitesync/saved_reports.html
- T012 [US1] Add client behavior to submit search changes in django_app/static/sitesync/js/saved_reports.js
```

## Parallel Example: User Story 2

```text
Run in parallel after T013-T017 core implementation:
- T018 [US2] Add client-side form serialization for checkbox and month params in django_app/static/sitesync/js/saved_reports.js
```

## Parallel Example: User Story 3

```text
Run in parallel after T019-T021:
- T022 [US3] Add clear/reset-filters action in django_app/templates/sitesync/saved_reports.html
- T023 [US3] Keep rendering synchronized after criteria changes in django_app/static/sitesync/js/saved_reports.js
```

---

## Implementation Strategy

### MVP First (US1-focused)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3 (US1)
3. Validate US1 independently on `/reports/`
4. Demo/deploy MVP if needed

### Incremental Delivery

1. Deliver US1 (search by site and user)
2. Deliver US2 (month/status filtering with defaults)
3. Deliver US3 (empty-state and combined-filter predictability)
4. Finalize with Phase 6 contract/docs/validation

### Parallel Team Strategy

1. One developer completes Phase 1-2 backend foundation
2. Then split:
   - Developer A: US1 (search UX + backend)
   - Developer B: US2 (month/status filters)
   - Developer C: US3 (empty-state/reset behavior)
3. Rejoin for Phase 6 Docker validation and polish

---

## Notes

- All tasks use strict checklist format with Task ID, optional [P], and [US#] labels for story phases
- Each user story is independently testable at its checkpoint
- Docker-only runtime and test execution is preserved throughout
