# Tasks: Report Validation Workflow

**Input**: Design documents from `/specs/012-report-validation-workflow/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Docker-executed Django tests are included because this feature explicitly requires containerized verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Docker-first validation workflow execution scaffolding

- [X] T001 Verify validation workflow test command coverage and scenario accuracy in specs/012-report-validation-workflow/quickstart.md
- [X] T002 Create Docker test helper script for validation suites in .specify/scripts/powershell/test-validation-workflow.ps1
- [X] T003 [P] Create feature test data notes for validation personas in specs/012-report-validation-workflow/checklists/test-data.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema and shared service primitives required by all user stories

**⚠️ CRITICAL**: No user story work starts until this phase is complete

- [X] T004 Extend report-level validation fields and choices in django_app/sitesync/models.py
- [X] T005 Add page validation, validation comment, and validation event models in django_app/sitesync/models.py
- [X] T006 Create additive migration for report validation schema in django_app/sitesync/migrations/ (use Django-generated timestamped filename ending with _report_validation_workflow.py)
- [X] T007 [P] Add validation payload form parsing and field validation in django_app/sitesync/forms.py
- [X] T008 Implement shared validation eligibility and status services in django_app/sitesync/services.py
- [X] T009 [P] Add validation route definitions for assign, page mark, and regrant flows in django_app/sitesync/urls.py
- [X] T010 Add reusable validation context projection helpers for report and saved reports in django_app/sitesync/services.py

**Checkpoint**: Foundation ready - user stories can proceed

---

## Phase 3: User Story 1 - Assign Independent Validator (Priority: P1) 🎯 MVP

**Goal**: Enable valid validator assignment and transition reports to awaiting validation with visible metadata

**Independent Test**: Assign an eligible validator to a draft report and verify awaiting-validation status and validator display in report and saved reports views

### Tests for User Story 1

- [X] T011 [P] [US1] Add assignment authorization and eligibility tests in django_app/sitesync/tests/test_report_validation_assignment.py
- [X] T012 [P] [US1] Add saved-reports validator metadata visibility tests in django_app/sitesync/tests/test_saved_reports_validation_metadata.py
- [X] T013 [US1] Add contract checks for assignment endpoint behavior in tests/contract/test_report_validation_assignment_contract.py

### Implementation for User Story 1

- [X] T014 [US1] Implement validator assignment service flow and reassignment detection in django_app/sitesync/services.py
- [X] T015 [US1] Implement validator assignment endpoint handler in django_app/sitesync/views.py
- [X] T016 [US1] Add assignment endpoint permission and response handling in django_app/sitesync/views.py
- [X] T017 [US1] Surface validation header metadata in report context assembly in django_app/sitesync/views.py
- [X] T018 [US1] Render validator and validation-status summary in django_app/sitesync/templates/sitesync/report.html
- [X] T019 [US1] Add validator and validation-status fields to saved reports JSON payload in django_app/sitesync/views.py
- [X] T020 [US1] Render validator metadata columns and remove non-essential updated column in django_app/sitesync/templates/sitesync/saved_reports.html

**Checkpoint**: US1 is independently functional and testable

---

## Phase 4: User Story 2 - Validate Report Pages With Comment Trail (Priority: P2)

**Goal**: Support validator-only page checkboxes and dedicated validation comments for owner/contributor/validator collaboration

**Independent Test**: Assigned validator can mark pages validated, non-validator cannot, and validation comments can be saved without clearing validated status

### Tests for User Story 2

- [X] T021 [P] [US2] Add validator-only page checkbox permission tests in django_app/sitesync/tests/test_report_validation_page_status.py
- [X] T022 [P] [US2] Add validation-comment persistence tests in django_app/sitesync/tests/test_report_validation_comments.py
- [X] T023 [US2] Add contract checks for page mark endpoint behavior in tests/contract/test_report_validation_page_mark_contract.py

### Implementation for User Story 2

- [X] T024 [US2] Implement page validation mark/unmark service with validator-only enforcement in django_app/sitesync/services.py
- [X] T025 [US2] Implement validation comment upsert/read services in django_app/sitesync/services.py
- [X] T026 [US2] Implement page validation toggle endpoint in django_app/sitesync/views.py
- [X] T027 [US2] Integrate validation comments payload handling into report save flow in django_app/sitesync/views.py
- [X] T028 [US2] Render page-level validation checkbox and dedicated validation comment box UI in django_app/sitesync/templates/sitesync/report.html
- [X] T029 [US2] Add page validation warning and non-validator disable states in django_app/sitesync/templates/sitesync/report.html

**Checkpoint**: US1 and US2 both independently functional

---

## Phase 5: User Story 3 - Reopen Validation on Edits and Gate Finalization (Priority: P3)

**Goal**: Automatically reset validation on business-content edits, require full validation for final save, and reopen validation after authorized final-report write regrant

**Independent Test**: Editing validated business content resets affected page validation, unvalidated reports cannot be finalized, fully validated reports can be finalized, and authorized regrant followed by edit reopens validation

### Tests for User Story 3

- [X] T030 [P] [US3] Add final-save gate tests for unvalidated vs fully validated reports in django_app/sitesync/tests/test_report_validation_final_gate.py
- [X] T031 [P] [US3] Add reset-on-business-edit and no-reset-on-validation-comment tests in django_app/sitesync/tests/test_report_validation_reset_rules.py
- [X] T032 [P] [US3] Add validator reassignment reset-all-pages tests in django_app/sitesync/tests/test_report_validation_reassignment.py
- [X] T033 [US3] Add final-reopen via supervisory-chain regrant tests in django_app/sitesync/tests/test_report_validation_regrant_reopen.py
- [X] T034 [US3] Add contract checks for final-save validation gate responses in tests/contract/test_report_validation_final_gate_contract.py

### Implementation for User Story 3

- [X] T035 [US3] Implement business-content diff detection and selective page reset logic in django_app/sitesync/services.py
- [X] T036 [US3] Enforce final-save validation gate and denial responses in django_app/sitesync/views.py
- [X] T037 [US3] Implement report-level validated transition when all pages are validated in django_app/sitesync/services.py
- [X] T038 [US3] Implement supervisory-chain regrant endpoint behavior with validation reopen semantics in django_app/sitesync/views.py
- [X] T039 [US3] Add regrant endpoint validation and response handling in django_app/sitesync/views.py
- [X] T040 [US3] Persist validation workflow audit events for assignment, page validation, resets, final-block, and reopen in django_app/sitesync/services.py
- [X] T041 [US3] Expose validated-by, validation-date, and can-save-final metadata in saved reports payload in django_app/sitesync/views.py

**Checkpoint**: All user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Stability hardening, documentation alignment, and end-to-end Docker verification

- [X] T042 [P] Add end-to-end validation workflow integration scenario in django_app/sitesync/tests/test_report_validation_end_to_end.py
- [X] T043 [P] Update validation workflow contract notes after implementation parity check in specs/012-report-validation-workflow/contracts/report-validation-workflow.md
- [X] T044 [P] Update saved-reports metadata contract examples after implementation parity check in specs/012-report-validation-workflow/contracts/saved-reports-validation-metadata.md
- [X] T045 Run Docker migration and full validation workflow test bundle command in specs/012-report-validation-workflow/quickstart.md
- [X] T046 Update release verification checklist with validation workflow evidence in deployment/PLATFORM_FOUNDATION_CHECKLIST.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories
- **Phase 3 (US1)**: Starts after Phase 2
- **Phase 4 (US2)**: Starts after Phase 2; can run in parallel with late US1 tasks if no file conflicts
- **Phase 5 (US3)**: Starts after Phase 2; depends on US2 page validation behavior for complete gate semantics
- **Phase 6 (Polish)**: Starts after desired user stories complete

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories
- **US2 (P2)**: Depends on foundational schema/services only; independent from US1 outcomes
- **US3 (P3)**: Depends on page validation behaviors from US2 and report metadata flows from US1

### Within Each User Story

- Tests first, confirm failure against missing behavior
- Service/domain logic before endpoint/controller wiring
- Endpoint wiring before template/UI integration
- Story acceptance checks before moving on

### Parallel Opportunities

- Phase 1: T003 can run with T001-T002
- Phase 2: T007 and T009 can run in parallel after schema direction is fixed
- US1: T011 and T012 can run in parallel, then T013
- US2: T021 and T022 can run in parallel, then T023
- US3: T030, T031, and T032 can run in parallel
- Polish: T042, T043, and T044 can run in parallel

---

## Parallel Example: User Story 2

```bash
# Parallel test tasks
Task: "T021 [US2] validator-only page checkbox permission tests"
Task: "T022 [US2] validation-comment persistence tests"

# Parallel implementation tasks after service contracts are stable
Task: "T026 [US2] page validation toggle endpoint"
Task: "T028 [US2] report page validation UI rendering"
```

---

## Phase 7: Convergence

- [X] T047 Restrict the validation regrant route to team lead, manager, or admin in the owner’s supervisory chain instead of forwarding to the generic write-grant flow per FR-015 / SC-007 (contradicts)
- [X] T048 Add the missing contract coverage for validation assignment, page-mark, and final-gate endpoints under tests/contract/ to lock request, response, and denial behavior per T013, T023, and T034 (missing)
- [X] T049 Add regression tests for validation-comment-only saves and validator-reassignment reset-all-pages behavior to prove the current workflow rules stay intact per T031 and T032 (missing)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3 (US1)
3. Validate assignment/status/metadata in Docker tests
4. Demo MVP before page-level validation work

### Incremental Delivery

1. Deliver US1 (assignment and awaiting-validation metadata)
2. Deliver US2 (page checkboxes and validation comments)
3. Deliver US3 (reset rules, final gate, reopen semantics)
4. Finish with cross-cutting polish and full Docker verification

### Parallel Team Strategy

1. Pair on foundational schema/service tasks (Phase 2)
2. After foundation completion:
   - Developer A: US1 endpoint + metadata wiring
   - Developer B: US2 page validation/comment workflow
   - Developer C: US3 finalization gate and reset/reopen logic
3. Rejoin for Phase 6 parity and Docker full-suite run

---

## Notes

- [P] tasks are intentionally separated by file responsibility where possible
- User story labels map each task to independently testable value slices
- Docker command execution is mandatory for migration and test verification
- Avoid cross-story coupling that blocks independent validation of each story

---

## Phase 8: Convergence

- [X] T050 Create the missing Docker validation-suite helper script at .specify/scripts/powershell/test-validation-workflow.ps1 per plan: Docker-first validation workflow and task intent T002 (missing)
- [X] T051 Add missing validation persona test-data checklist at specs/012-report-validation-workflow/checklists/test-data.md per quickstart prerequisites and task intent T003 (missing)
- [X] T052 Add or reconcile missing root contract test coverage for page-mark endpoint at tests/contract/test_report_validation_page_mark_contract.py so root contract set matches assignment/final-gate parity per task intent T023/T048 (partial)
