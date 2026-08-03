---
description: "Task list for report write delegation feature"
---

# Tasks: Report Write Delegation

**Input**: Design documents from /specs/011-report-write-delegation/

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include integration and contract-behavior tests because feature success criteria explicitly require permission validation and Docker-based test execution.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare feature-specific scaffolding and Docker test entry points

- [X] T001 Create delegation test module stubs in django_app/sitesync/tests/test_report_write_delegation_access.py, django_app/sitesync/tests/test_report_write_delegation_authority.py, django_app/sitesync/tests/test_report_write_delegation_visibility.py, and django_app/sitesync/tests/test_report_write_delegation_conflicts.py
- [X] T002 [P] Add delegation endpoint placeholders in django_app/sitesync/urls.py and handler stubs in django_app/sitesync/views.py
- [X] T003 [P] Add feature-level Docker validation command section in specs/011-report-write-delegation/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data and permission infrastructure that all user stories depend on

**CRITICAL**: No user story work starts until this phase is complete

- [X] T004 Implement ReportWriteDelegation and ReportWriteDelegationEvent models in django_app/sitesync/models.py
- [X] T005 Create the next sequential Django migration in django_app/sitesync/migrations/ to add delegation models, indexes, and constraints.
- [X] T006 [P] Register delegation models for operations and audit visibility in django_app/sitesync/admin.py
- [X] T007 [P] Add delegation payload validation and serialization fields in django_app/sitesync/forms.py and django_app/sitesync/serializers.py
- [X] T008 Implement delegation authority resolver and effective-write access resolver in django_app/sitesync/services.py
- [X] T009 Implement delegation audit event writer and history query helpers in django_app/sitesync/services.py
- [X] T010 Implement transaction-safe active delegation lookup helpers in django_app/sitesync/services.py

**Checkpoint**: Delegation data model and shared authorization services are ready

---

## Phase 3: User Story 1 - Owner Delegates Team Support (Priority: P1) MVP

**Goal**: Report owner can grant and revoke same-team write collaboration

**Independent Test**: Owner grants a same-team user edit rights, user can save, owner revokes, user save is denied

### Tests for User Story 1

- [X] T011 [P] [US1] Add owner grant and owner revoke access-flow tests in django_app/sitesync/tests/test_report_write_delegation_access.py
- [X] T012 [P] [US1] Add same-team, inactive-user, and out-of-scope denial tests for owner grants in django_app/sitesync/tests/test_report_write_delegation_authority.py
- [X] T013 [US1] Add submit-time save denial test after revoke in django_app/sitesync/tests/test_report_write_delegation_access.py

### Implementation for User Story 1

- [X] T014 [US1] Implement owner grant endpoint behavior in django_app/sitesync/views.py
- [X] T015 [US1] Implement owner revoke endpoint behavior in django_app/sitesync/views.py
- [X] T016 [US1] Wire owner delegation grant and revoke routes in django_app/sitesync/urls.py
- [X] T017 [US1] Enforce submit-time write authorization in report save workflow in django_app/sitesync/views.py
- [X] T018 [US1] Render owner delegation controls and permission feedback in django_app/templates/sitesync/report.html

**Checkpoint**: Owner-driven team collaboration works end-to-end and is independently testable

---

## Phase 4: User Story 2 - Lead or Manager Delegates Org Coverage (Priority: P2)

**Goal**: Team leads and managers can delegate write access across their organisation, including self

**Independent Test**: Team lead or manager grants access on non-owned report within organisation and delegate can save changes

### Tests for User Story 2

- [X] T019 [P] [US2] Add team lead and manager organisation-scope grant tests in django_app/sitesync/tests/test_report_write_delegation_authority.py
- [X] T020 [P] [US2] Add self-grant success and cross-organisation denial tests in django_app/sitesync/tests/test_report_write_delegation_authority.py
- [X] T021 [US2] Add revoke authorization tests for original grantor and same-organisation lead or manager in django_app/sitesync/tests/test_report_write_delegation_authority.py

### Implementation for User Story 2

- [X] T022 [US2] Extend delegation grant authorization for team lead and manager roles in django_app/sitesync/services.py
- [X] T023 [US2] Extend delegation revoke authorization for original grantor and same-organisation lead or manager in django_app/sitesync/services.py
- [X] T024 [US2] Persist grantor role metadata for owner, team lead, and manager grants in django_app/sitesync/views.py and django_app/sitesync/models.py
- [X] T025 [US2] Update report editor delegation actions to support lead or manager self-delegation in django_app/templates/sitesync/report.html

**Checkpoint**: Organisation-level emergency and coverage delegation works independently of US1 ownership flow

---

## Phase 5: User Story 3 - Users See Delegation Accountability (Priority: P3)

**Goal**: Report readers can view active delegated writers and grantors with consistent editor access mode

**Independent Test**: A user with report read access can view active delegates and grantors, and editor mode matches effective permissions

### Tests for User Story 3

- [X] T026 [P] [US3] Add delegation visibility endpoint tests for read-access users in django_app/sitesync/tests/test_report_write_delegation_visibility.py
- [X] T027 [P] [US3] Add saved-report to editor mode-consistency tests in django_app/sitesync/tests/test_saved_reports_view.py
- [X] T028 [US3] Add revoked-between-open-and-save behavior test in django_app/sitesync/tests/test_report_write_delegation_access.py

### Implementation for User Story 3

- [X] T029 [US3] Implement active delegation visibility endpoint with grantor fields in django_app/sitesync/views.py
- [X] T030 [US3] Wire delegation visibility route in django_app/sitesync/urls.py
- [X] T031 [US3] Render active delegated writers and grantors in django_app/templates/sitesync/report.html
- [X] T032 [US3] Add saved reports delegation context and indicator rendering in django_app/sitesync/views.py and django_app/templates/sitesync/saved_reports.html

**Checkpoint**: Delegation accountability and read-mode transparency are independently functional

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Complete deterministic conflict handling, audit completeness, and Docker verification

- [X] T033 [P] Add concurrent grant-revoke conflict tests with timestamp winner assertions in django_app/sitesync/tests/test_report_write_delegation_conflicts.py
- [X] T034 [P] Implement last-write-wins conflict resolution with transaction boundaries in django_app/sitesync/services.py
- [X] T035 [P] Add delegation event audit assertions for conflict metadata in django_app/sitesync/tests/test_audit_logging_events.py
- [X] T036 Update API and operator docs for delegation grant, revoke, and visibility flows in docs/API.md and django_app/README.md
- [X] T037 Run Docker-only delegation test bundle and capture execution log in specs/011-report-write-delegation/quickstart.md
- [ ] T038 Run timed UAT for delegation visibility with a representative user sample, record completion times, and confirm SC-005 threshold in specs/011-report-write-delegation/quickstart.md

---

## Dependencies and Execution Order

### Phase Dependencies

- Setup (Phase 1): Starts immediately
- Foundational (Phase 2): Depends on Setup and blocks all user stories
- User Story phases (Phase 3 to Phase 5): Depend on Phase 2 completion
- Polish (Phase 6): Depends on completion of selected user stories

### User Story Dependencies

- User Story 1 (P1): Depends only on Foundational phase
- User Story 2 (P2): Depends on Foundational phase; does not require US1 completion
- User Story 3 (P3): Depends on Foundational phase; validates behavior across US1 and US2 outputs

### Within Each User Story

- Write tests first and confirm they fail
- Implement services before view handlers where authorization logic is reused
- Wire routes after handlers exist
- Update templates after backend permission context is available

## Parallel Opportunities

- T002 and T003 can run in parallel in Setup
- T006 and T007 can run in parallel after T004 in Foundational
- T011 and T012 can run in parallel in US1
- T019 and T020 can run in parallel in US2
- T026 and T027 can run in parallel in US3
- T033, T034, and T035 can run in parallel in Polish

## Parallel Example: User Story 1

- Task T011 in django_app/sitesync/tests/test_report_write_delegation_access.py
- Task T012 in django_app/sitesync/tests/test_report_write_delegation_authority.py

## Parallel Example: User Story 2

- Task T019 in django_app/sitesync/tests/test_report_write_delegation_authority.py
- Task T020 in django_app/sitesync/tests/test_report_write_delegation_authority.py

## Parallel Example: User Story 3

- Task T026 in django_app/sitesync/tests/test_report_write_delegation_visibility.py
- Task T027 in django_app/sitesync/tests/test_saved_reports_view.py

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 Setup
2. Complete Phase 2 Foundational
3. Complete Phase 3 User Story 1
4. Validate owner delegation flow in Docker before moving on

### Incremental Delivery

1. Deliver US1 for owner collaboration support
2. Add US2 for lead and manager organisational coverage
3. Add US3 for delegation transparency and accountability
4. Finish with conflict handling and full Docker regression run

### Parallel Team Strategy

1. One engineer completes data model and shared services in Phase 2
2. One engineer executes US1 while another prepares US2 tests
3. US3 can start once core delegation endpoints stabilize
4. Polish tasks split across conflict handling, audit validation, and documentation
