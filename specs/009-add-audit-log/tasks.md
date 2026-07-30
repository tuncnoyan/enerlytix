# Tasks: Admin Audit Log

**Input**: Design documents from `/specs/009-add-audit-log/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include automated tests for each user story. All tests for this feature MUST run in Docker using `docker compose -f django_app/docker/docker-compose.yml exec -T web ...`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare repository and runtime prerequisites for audit-log delivery in the containerized environment.

- [X] T001 Verify Docker test workflow commands are documented in specs/009-add-audit-log/quickstart.md
- [X] T002 Use django_app/requirements.txt as the canonical dependency source; add/confirm XLSX dependency there and mirror-lock top-level requirements.txt from canonical file.
- [X] T003 [P] Add audit feature URL placeholders in django_app/sitesync/urls.py
- [X] T004 [P] Add admin panel navigation placeholder for audit logs in django_app/sitesync/templates/sitesync/panel.html

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared audit infrastructure that blocks all user-story implementation until complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Create AuditLogEntry model with UTC timestamp, action/outcome fields, snapshots, and indexes in django_app/sitesync/models.py
- [X] T006 Generate and commit AuditLogEntry migration using django manage.py makemigrations sitesync; commit generated file under django_app/sitesync/migrations/
- [X] T007 Implement normalized action-type and outcome constants in django_app/sitesync/services.py
- [X] T008 Implement shared audit write helper for success/denied/failed events in django_app/sitesync/services.py
- [X] T009 Implement admin authorization helper and denied-attempt audit logging hook in django_app/sitesync/views.py
- [X] T010 Enforce minimum one-year retention policy settings for audit logs in django_app/sitesync/config_service.py

**Checkpoint**: Foundation ready. User story implementation can begin.

---

## Phase 3: User Story 1 - Record Traceable Activity (Priority: P1) 🎯 MVP

**Goal**: Persist immutable audit records for authenticated mutating actions and denied/failed security-relevant attempts.

**Independent Test**: Perform create report, delete user, approve report, and one denied security-relevant action; verify all required fields are present in persisted audit entries.

### Tests for User Story 1

- [X] T011 [P] [US1] Add contract tests for required AuditLogEntry fields and outcomes in tests/contract/test_audit_log_entry_contract.py
- [X] T012 [P] [US1] Add integration tests covering representative authenticated mutating actions across report, user-management, team-management, invitation, and settings flows, plus denied-attempt logging in tests/integration/test_audit_logging_events.py
- [X] T012a [US1] Add integration test to create auditable event, delete the target entity, and verify audit row remains readable in viewer and exports in tests/integration/test_audit_logging_events.py

### Implementation for User Story 1

- [X] T013 [US1] Instrument report create/approve flows to emit success audit events in django_app/sitesync/views.py
- [X] T014 [US1] Instrument user-management mutating flows to emit success audit events in django_app/sitesync/views.py
- [X] T014a [US1] Build a mutating-action inventory for sitesync endpoints and instrument each action class to emit audit events in django_app/sitesync/views.py and django_app/sitesync/services.py
- [X] T015 [US1] Instrument denied/failed security-relevant actions to emit audit events in django_app/sitesync/views.py
- [X] T016 [US1] Add immutable snapshot/value validation for audit writes in django_app/sitesync/services.py
- [X] T017 [US1] Execute US1 automated tests in Docker and record command/results in specs/009-add-audit-log/quickstart.md

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Review and Filter Audit History (Priority: P2)

**Goal**: Provide an admin-only audit viewer in the panel with user, keyword, date-range, and action-type filters.

**Independent Test**: Open audit viewer as admin and non-admin; verify access control and that each filter (alone and combined) returns the expected subset.

### Tests for User Story 2

- [X] T018 [P] [US2] Add contract tests for audit viewer filter parameters and validation errors, including 200 HTML with inline errors for invalid filters, in tests/contract/test_audit_log_viewer_contract.py
- [X] T019 [P] [US2] Add integration tests for admin-only access and filter behavior in tests/integration/test_audit_log_viewer_filters.py

### Implementation for User Story 2

- [X] T020 [US2] Implement audit filter parsing and validation (user/keyword/start/end/action_type) in django_app/sitesync/forms.py
- [X] T021 [US2] Implement admin audit viewer endpoint with pagination and filter application in django_app/sitesync/views.py
- [X] T022 [US2] Wire audit viewer route in django_app/sitesync/urls.py and django_app/config/urls.py
- [X] T023 [US2] Build admin audit viewer template with filter controls and result table in django_app/sitesync/templates/sitesync/admin_audit_logs.html
- [X] T023a [US2] Implement explicit timezone labeling in audit viewer timestamps (display timezone label and UTC reference) in django_app/sitesync/templates/sitesync/admin_audit_logs.html and django_app/sitesync/views.py.
- [X] T024 [US2] Execute US2 automated tests in Docker and record command/results in specs/009-add-audit-log/quickstart.md

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Export Filtered Audit Data (Priority: P3)

**Goal**: Export the currently filtered audit subset as CSV and XLSX from the admin viewer.

**Independent Test**: Apply filters, export CSV/XLSX, and verify row parity with on-screen results (including empty-result export with headers).

### Tests for User Story 3

- [X] T025 [P] [US3] Add contract tests for CSV/XLSX export endpoints and content types, including 400 responses for invalid filters, in tests/contract/test_audit_log_export_contract.py
- [X] T025a [P] [US3] Add contract tests verifying CSV/XLSX timestamp columns include unambiguous timezone labeling in tests/contract/test_audit_log_export_contract.py.
- [X] T025b [P] [US3] Add contract tests verifying exports with >50,000 filtered rows fail fast with a clear "narrow filters" message and return no partial file in tests/contract/test_audit_log_export_contract.py.
- [X] T026 [P] [US3] Add integration tests for export row parity, empty-result behavior, deleted-target readability parity checks, and timezone-label consistency checks between viewer, CSV, and XLSX outputs in tests/integration/test_audit_log_exports.py

### Implementation for User Story 3

- [X] T027 [US3] Implement shared filtered-query builder reused by viewer and exports in django_app/sitesync/services.py
- [X] T028 [US3] Implement CSV and XLSX export handlers using active filters in django_app/sitesync/views.py
- [X] T028a [US3] Implement FR-017 export threshold guard (>50,000 rows) for CSV/XLSX with fail-fast user-facing message and explicit no-partial-file behavior in django_app/sitesync/views.py and django_app/sitesync/services.py.
- [X] T029 [US3] Add export actions/links to audit viewer UI in django_app/sitesync/templates/sitesync/admin_audit_logs.html
- [X] T030 [US3] Execute US3 automated tests in Docker (including FR-017 threshold/no-partial-file scenarios) and record command/results in specs/009-add-audit-log/quickstart.md

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize quality, security, and documentation across all stories.

- [X] T031 [P] Add focused unit tests for audit helpers and filter validators in django_app/sitesync/tests/test_audit_helpers.py
- [X] T032 Perform security review of admin-only access and denied-attempt logging paths in django_app/sitesync/views.py
- [X] T033 [P] Update API documentation for audit viewer/export contracts in docs/API.md
- [X] T034 [P] Update secret/security operational notes for audit data handling in docs/SECRET_MANAGEMENT.md
- [X] T035 Run full regression test suite in Docker and capture final validation commands in specs/009-add-audit-log/quickstart.md
- [X] T036 Execute and document acceptance validation trials for SC-002 and SC-005 (time-to-find-event and first-attempt success rate) using scenarios in specs/009-add-audit-log/quickstart.md, and store results in specs/009-add-audit-log/checklists/requirements.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies, start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1, blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion; can begin after US1 foundation but should follow priority order.
- **Phase 5 (US3)**: Depends on Phase 2 completion and reuses US2 filter/query behavior.
- **Phase 6 (Polish)**: Depends on completion of target user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 (P2)**: Starts after Phase 2; depends on US1 audit data availability for practical validation.
- **US3 (P3)**: Starts after Phase 2; depends on US2 filter semantics for parity between screen and exports.

### Within Each User Story

- Tests should be implemented before or alongside implementation and must fail before final pass.
- Model/infrastructure hooks before endpoint wiring.
- Endpoint logic before template wiring and final validation.

## Parallel Opportunities

- **Setup**: T003 and T004 can run in parallel.
- **US1**: T011 and T012 can run in parallel.
- **US2**: T018 and T019 can run in parallel.
- **US3**: T025 and T026 can run in parallel.
- **Polish**: T031, T033, and T034 can run in parallel.

## Parallel Example: User Story 1

- Run together: T011 and T012.
- After tests are in place, implementation proceeds sequentially: T013 → T014 → T015 → T016.

## Parallel Example: User Story 2

- Run together: T018 and T019.
- Implementation split: T020 can proceed while T021 starts, then T022 and T023 follow.

## Parallel Example: User Story 3

- Run together: T025 and T026.
- Implementation split: T028 and T029 can overlap after T027 is complete.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 in Docker before moving on.

### Incremental Delivery

1. Deliver US1 (audit capture).
2. Deliver US2 (viewer and filters).
3. Deliver US3 (exports).
4. Finish with Phase 6 hardening and full Docker regression.

### Docker-First Validation Rule

- Every validation task in this file is executed inside Docker web container using commands documented in specs/009-add-audit-log/quickstart.md.
