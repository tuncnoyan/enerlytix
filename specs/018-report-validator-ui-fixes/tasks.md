# Tasks: Report Validator UI Fixes

**Input**: Design documents from /specs/018-report-validator-ui-fixes/

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/report-validator-ui-behavior.md, quickstart.md

**Tests**: Regression tests are included because this feature targets production defects and role-based behavior guarantees.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare execution baseline and test scaffolding for this feature.

- [ ] T001 Capture baseline failing scenarios and expected outcomes in specs/018-report-validator-ui-fixes/quickstart.md
- [ ] T002 [P] Add feature-focused test module scaffold in django_app/sitesync/tests/test_report_validation.py
- [ ] T003 [P] Add feature-focused contract test scaffold in django_app/tests/contract/test_report_validation_page_mark_contract.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce shared permission and context plumbing used by all stories.

**⚠️ CRITICAL**: Complete this phase before user story implementation.

- [ ] T004 Implement shared validator-restricted session helper in django_app/sitesync/services.py
- [ ] T005 [P] Expose validator-restricted and admin flags in report and saved-reports contexts in django_app/sitesync/views.py
- [ ] T006 [P] Wire context flags into templates for client-side consumption in django_app/templates/sitesync/report.html and django_app/templates/sitesync/saved_reports.html
- [ ] T007 Add foundational regression assertions for context contract in django_app/sitesync/tests/test_report_validation.py

**Checkpoint**: Permission/context foundation complete. User stories can proceed.

---

## Phase 3: User Story 1 - Fix Saved Reports Selection Layout (Priority: P1) 🎯 MVP

**Goal**: Restore admin-only row-selection checkboxes and correct header/body column alignment on Saved Reports.

**Independent Test**: Open Saved Reports as admin and non-admin users; verify checkbox visibility rules and no column shift.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add admin vs non-admin control visibility tests in django_app/sitesync/tests/test_saved_reports_view.py
- [ ] T009 [P] [US1] Add saved-reports row/header alignment and selection payload tests in django_app/sitesync/tests/test_saved_reports_view.py

### Implementation for User Story 1

- [ ] T010 [US1] Enforce admin-only selection-column rendering contract in django_app/templates/sitesync/saved_reports.html
- [ ] T011 [US1] Fix row rendering and selected_report_ids synchronization for admin mode in django_app/static/sitesync/js/saved_reports.js
- [ ] T012 [US1] Ensure saved-reports JSON/template context aligns with admin-only checkbox behavior in django_app/sitesync/views.py
- [ ] T013 [US1] Sync built saved-reports static assets in django_app/staticfiles/sitesync/js/saved_reports.js and django_app/staticfiles/sitesync/js/saved_reports.b00baf3601a0.js

**Checkpoint**: Saved Reports selection and alignment are stable and independently testable.

---

## Phase 4: User Story 2 - Restrict Validator Editing Rights (Priority: P1)

**Goal**: Enforce validator-only report sessions (read-only content, no draft/final save) while allowing validation actions and note autosave.

**Independent Test**: Open report as assigned validator (including dual-role user), verify save actions are blocked and validation interactions remain available with blur autosave.

### Tests for User Story 2

- [ ] T014 [P] [US2] Add validator save-denial and dual-role precedence tests in django_app/sitesync/tests/test_report_validation.py
- [ ] T015 [P] [US2] Add validation-note autosave persistence tests in django_app/sitesync/tests/test_report_validation.py
- [ ] T016 [P] [US2] Add contract test coverage for validator-restricted save attempts in django_app/tests/contract/test_report_validation_page_mark_contract.py
- [ ] T030 [P] [US2] Add validation-note autosave failure-state test coverage (text retained and retry feedback shown) in django_app/sitesync/tests/test_report_validation.py

### Implementation for User Story 2

- [ ] T017 [US2] Block draft/final save POST operations for validator-restricted sessions in django_app/sitesync/views.py
- [ ] T018 [US2] Update report template controls to hide/disable content-save actions for validator-restricted sessions in django_app/templates/sitesync/report.html
- [ ] T019 [US2] Implement blur-triggered debounced validation-note autosave behavior in django_app/static/sitesync/js/report.js
- [ ] T031 [US2] Implement validation-note autosave failure handling UI (retain note text and show retry feedback) in django_app/static/sitesync/js/report.js and django_app/templates/sitesync/report.html
- [ ] T020 [US2] Preserve allowed validation checkbox and note endpoints for validator-restricted sessions in django_app/sitesync/views.py and django_app/sitesync/services.py
- [ ] T021 [US2] Sync built report static assets in django_app/staticfiles/sitesync/js/report.js and django_app/staticfiles/sitesync/js/report.4eda9705ccbe.js

**Checkpoint**: Validator-restricted workflow is independently functional and testable.

---

## Phase 5: User Story 3 - Clean First Overview Validation Block Layout (Priority: P2)

**Goal**: Remove duplicate first-page validation/comment block and standardize remaining block width to match other pages.

**Independent Test**: Open first overview page and confirm only one validation/comment block with standard width and behavior.

### Tests for User Story 3

- [ ] T022 [P] [US3] Add overview validation block rendering regression coverage in django_app/sitesync/tests/test_report_validation.py

### Implementation for User Story 3

- [ ] T023 [US3] Remove duplicate first overview validation/comment block render path in django_app/static/sitesync/js/report.js
- [ ] T024 [US3] Align first overview validation/comment block sizing with standard page layout in django_app/templates/sitesync/report.html and django_app/static/sitesync/js/report.js
- [ ] T025 [US3] Sync built report static assets after overview layout fix in django_app/staticfiles/sitesync/js/report.js and django_app/staticfiles/sitesync/js/report.4eda9705ccbe.js

**Checkpoint**: First overview page layout is cleaned and consistent with other report pages.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency checks, docs, and release-readiness validation.

- [ ] T026 [P] Update release verification steps and production smoke scenarios in specs/018-report-validator-ui-fixes/quickstart.md
- [ ] T027 [P] Validate deployment static rebuild assumptions in nixpacks.toml and django_app/config/settings.py
- [ ] T028 Run focused Docker regression suite and capture outcomes in ./test-results.txt
- [ ] T029 Run full Docker report/saved-reports regression suite for sign-off in django_app/sitesync/tests/test_saved_reports_view.py and django_app/sitesync/tests/test_report_validation.py

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): no dependencies.
- Phase 2 (Foundational): depends on Phase 1 and blocks all user stories.
- Phase 3 (US1), Phase 4 (US2), Phase 5 (US3): all depend on Phase 2.
- Phase 6 (Polish): depends on completed user stories targeted for release.

### User Story Dependencies

- US1 (P1): depends on foundational context flags only; no dependency on US2/US3.
- US2 (P1): depends on foundational permission/context plumbing; no dependency on US1/US3.
- US3 (P2): depends on foundational context and report rendering pipeline; no dependency on US1.

### Within Each User Story

- Add tests first and confirm they fail for the intended regression.
- Apply server-side guard logic before client-side behavior for security-critical flows.
- Update source static files before syncing built staticfiles copies.

### Parallel Opportunities

- Setup tasks T002 and T003 can run in parallel.
- Foundational tasks T005 and T006 can run in parallel after T004 starts.
- In US1, tests T008 and T009 can run in parallel.
- In US2, tests T014, T015, T016, and T030 can run in parallel.
- In Polish, tasks T026 and T027 can run in parallel.

---

## Parallel Example: User Story 1

- Run T008 and T009 together while keeping T010 queued.
- After T010 merges, run T011 and T012 in sequence, then T013.

## Parallel Example: User Story 2

- Run T014, T015, T016, and T030 together.
- Start T018 and T019 in parallel after T017 is in place.

## Parallel Example: User Story 3

- Run T022 while preparing implementation branch for T023.
- Complete T024 after T023, then run T025.

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) to restore production-critical Saved Reports behavior.
3. Validate US1 independently before moving forward.

### Incremental Delivery

1. Foundation complete.
2. Deliver US1 (Saved Reports fix).
3. Deliver US2 (validator restrictions + autosave).
4. Deliver US3 (first overview layout cleanup).
5. Finish polish and release validation.

### Parallel Team Strategy

1. One developer completes foundational phase.
2. After foundation:
   - Developer A: US1
   - Developer B: US2
   - Developer C: US3
3. Rejoin for Phase 6 regression and production smoke validation.
