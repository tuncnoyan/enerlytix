# Tasks: Report Ownership Model

**Input**: Design documents from `/specs/010-report-ownership-model/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Docker-first workflow and feature scaffolding.

- [X] T001 Add Docker-only verification commands section for this feature in `README.md`
- [X] T002 Create migration scaffold for report ownership model in `django_app/sitesync/migrations/0018_report_ownership_model.py`
- [X] T003 [P] Add concrete POST routes for ownership workflows in `django_app/sitesync/urls.py`: `/reports/<report_id>/ownership/grants/`, `/reports/<report_id>/ownership/grants/revoke/`, `/reports/<report_id>/ownership/transfer/`, `/reports/<report_id>/ownership/unavailability/approve/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data and service infrastructure required before user stories.

**⚠️ CRITICAL**: No user story implementation starts before this phase is complete.

- [X] T004 Extend `MonthlyReport` ownership metadata fields in `django_app/sitesync/models.py`
- [X] T005 [P] Add `ReportWriteGrant` model in `django_app/sitesync/models.py`
- [X] T006 [P] Add `ReportOwnershipUnavailabilityApproval` model in `django_app/sitesync/models.py`
- [X] T007 [P] Add `ReportOwnershipTransferEvent` model in `django_app/sitesync/models.py`
- [X] T008 Implement migration schema and indexes for ownership entities in `django_app/sitesync/migrations/0018_report_ownership_model.py`
- [X] T009 Implement migration backfill for report owner and last-modified metadata in `django_app/sitesync/migrations/0018_report_ownership_model.py`
- [X] T010 Add ownership admin registrations for operational inspection in `django_app/sitesync/admin.py`
- [X] T011 Add ownership permission and fallback helper services in `django_app/sitesync/services.py`
- [X] T012 Add ownership workflow forms for grant, revoke, transfer, and unavailability approval in `django_app/sitesync/forms.py`
- [X] T042 Add report scope source by linking site to team in `django_app/sitesync/models.py`
- [X] T043 Create migration for site-team scope linkage in `django_app/sitesync/migrations/0019_site_team_scope.py`
- [X] T044 Update fallback eligibility resolver to enforce same-scope checks using site-team linkage in `django_app/sitesync/services.py`

**Checkpoint**: Foundation complete, user stories can now be implemented.

---

## Phase 3: User Story 1 - Own and Edit My Reports (Priority: P1) 🎯 MVP

**Goal**: Ensure each report has one owner and only authorized writers can edit.

**Independent Test**: Create a report as user A, verify owner metadata is set, verify A can edit, verify user B without grant is read-only and blocked on save.

### Tests for User Story 1

- [X] T036 [P] [US1] Add integration test for owner write and non-owner deny-write in `tests/integration/test_report_ownership_access.py`
- [X] T037 [P] [US1] Add integration test for submit-time permission check with no partial write in `tests/integration/test_report_ownership_access.py`

### Implementation for User Story 1

- [X] T013 [US1] Set owner and creator metadata on first report creation path in `django_app/sitesync/views.py`
- [X] T014 [US1] Update last-modified metadata on permitted report saves in `django_app/sitesync/views.py`
- [X] T015 [US1] Enforce submit-time write permission guard for report save action in `django_app/sitesync/views.py`
- [X] T016 [US1] Add read-only access-state projection for report editor context in `django_app/sitesync/views.py`
- [X] T017 [US1] Render and enforce read-only editor behavior in `django_app/templates/sitesync/report.html`
- [X] T018 [US1] Add denied-write and owner-write audit event logging for report saves in `django_app/sitesync/views.py`

**Checkpoint**: User Story 1 is independently functional.

---

## Phase 4: User Story 2 - Grant Named Collaborators Write Access (Priority: P2)

**Goal**: Allow owners to grant/revoke named-user write access and support approved fallback owner transfer.

**Independent Test**: Owner grants user B write, B edits successfully, owner revokes B and B is blocked; team lead approval triggers fallback transfer in required order and previous owner retains collaborator write.

### Tests for User Story 2

- [X] T038 [P] [US2] Add integration test for grant and revoke collaborator write access in `tests/integration/test_report_collaborator_grants.py`
- [X] T039 [P] [US2] Add integration test for fallback transfer order and previous-owner collaborator retention in `tests/integration/test_report_owner_fallback_transfer.py`
- [X] T045 [P] [US2] Add integration test for cross-scope fallback candidate rejection in `tests/integration/test_report_owner_fallback_transfer.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement owner-only grant endpoint logic for report collaborators in `django_app/sitesync/views.py`
- [X] T020 [US2] Implement owner-only revoke endpoint logic for report collaborators in `django_app/sitesync/views.py`
- [X] T021 [P] [US2] Add ownership management POST routes in `django_app/sitesync/urls.py`
- [X] T022 [US2] Implement manual owner transfer workflow in `django_app/sitesync/views.py`
- [X] T023 [US2] Implement team-lead unavailability approval workflow in `django_app/sitesync/views.py`
- [X] T024 [US2] Implement fallback candidate resolution order and eligibility checks in `django_app/sitesync/services.py`
- [X] T025 [US2] Persist ownership transfer events and preserve previous-owner collaborator access in `django_app/sitesync/services.py`
- [X] T026 [US2] Add grant, revoke, approval, and transfer audit logging in `django_app/sitesync/views.py`

**Checkpoint**: User Stories 1 and 2 are both independently functional.

---

## Phase 5: User Story 3 - View Ownership Metadata on Saved Reports (Priority: P3)

**Goal**: Display required ownership/accountability fields on Saved Reports and preserve access behavior.

**Independent Test**: Open Saved Reports and verify each row shows site/report, month, owner, created at, last edited by, last edited at, status; open action preserves read/write access rules.

### Tests for User Story 3

- [X] T040 [P] [US3] Add contract test for saved reports ownership fields in `tests/contract/test_saved_reports_ownership.md`
- [X] T041 [P] [US3] Add integration test for saved reports metadata rendering and access indicator in `tests/integration/test_saved_reports_ownership_listing.py`

### Implementation for User Story 3

- [X] T027 [US3] Extend saved-reports query projection with ownership metadata fields in `django_app/sitesync/views.py`
- [X] T028 [US3] Add effective access indicator derivation for each saved report row in `django_app/sitesync/services.py`
- [X] T029 [US3] Render owner and edit metadata columns in `django_app/templates/sitesync/saved_reports.html`
- [X] T030 [US3] Render per-row access mode indicator in `django_app/templates/sitesync/saved_reports.html`
- [X] T031 [US3] Add legacy metadata fallback and empty-state wiring in `django_app/templates/sitesync/saved_reports.html` and `django_app/templates/sitesync/reports_empty_state.html`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, documentation alignment, and Docker-only validation.

- [X] T032 [P] Update API and ownership workflow docs in `docs/API.md`
- [X] T033 [P] Document ownership transfer governance and fallback behavior in `docs/SECRET_MANAGEMENT.md`
- [X] T034 Validate full feature scenarios using Docker-only steps in `specs/010-report-ownership-model/quickstart.md`
- [X] T035 Execute Docker test suite for ownership feature paths and capture results in `test-results.txt`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): No dependencies.
- Phase 2 (Foundational): Depends on Phase 1 and blocks all user stories.
- Phase 3 (US1): Depends on Phase 2.
- Phase 4 (US2): Depends on Phase 2 and integrates with US1 ownership primitives.
- Phase 5 (US3): Depends on Phase 2 and consumes metadata from US1/US2 flows.
- Phase 6 (Polish): Depends on completion of desired user stories.

### User Story Dependencies

- US1 (P1): Starts after Foundational phase; delivers MVP ownership enforcement.
- US2 (P2): Starts after Foundational phase; uses US1 ownership state and extends collaborator/fallback workflows.
- US3 (P3): Starts after Foundational phase; can be developed after US1 metadata plumbing is available.

### Within Each User Story

- Data and permission logic before route handlers.
- Route handlers before template behavior.
- Audit logging integrated before story completion checkpoint.

## Parallel Opportunities

- Phase 1: T003 can run in parallel with T001-T002.
- Phase 2: T005, T006, T007 can run in parallel after T004 starts.
- Phase 2: T043 can run in parallel with T008-T009 after T042 is defined.
- Phase 4: T021 can run in parallel with T019-T020.
- Phase 3-5 tests: T036, T037, T038, T039, T040, T041, T045 can run in parallel by story.
- Phase 6: T032 and T033 can run in parallel.

## Parallel Example: User Story 2

```bash
Task: "T019 Implement owner-only grant endpoint logic in django_app/sitesync/views.py"
Task: "T020 Implement owner-only revoke endpoint logic in django_app/sitesync/views.py"
Task: "T021 Add ownership management POST routes in django_app/sitesync/urls.py"
```

## Parallel Example: User Story 3

```bash
Task: "T029 Render owner and edit metadata columns in django_app/templates/sitesync/saved_reports.html"
Task: "T030 Render per-row access mode indicator in django_app/templates/sitesync/saved_reports.html"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3 (US1).
4. Validate US1 independently using Docker runtime.

### Incremental Delivery

1. Foundation first (Phases 1-2).
2. Deliver US1 and validate.
3. Deliver US2 and validate.
4. Deliver US3 and validate.
5. Finish polish and Docker-only end-to-end checks.

### Parallel Team Strategy

1. Team completes Phases 1-2 together.
2. Then split by story:
   - Developer A: US1 core permission enforcement.
   - Developer B: US2 grant/revoke/transfer flows.
   - Developer C: US3 saved-reports metadata and UI.
3. Rejoin for Phase 6 validation and documentation.

## Notes

- `[P]` tasks are parallelizable across independent files or route/model surfaces.
- `[US1]`, `[US2]`, and `[US3]` labels map tasks directly to prioritized user stories.
- All verification commands for this feature must run in Docker environment only.

---

## Phase 7: Convergence

- [X] T046 CRITICAL: Restrict legacy null-team report visibility to authorized ownership/grant scope (do not expose all null-team reports to any team-assigned user) per Constitution III (contradicts)
- [X] T047 Enforce same-scope fallback guarantees when `Site.team` is null by blocking fallback transfer or deriving an equivalent validated scope before candidate selection per FR-013 (partial)
- [X] T048 Update Docker-only verification commands in `README.md` and `specs/010-report-ownership-model/quickstart.md` to runnable in-container test targets (module paths under `sitesync.tests`) per plan: Docker-only verification decision (partial)
- [X] T049 Add regression tests for legacy null-team visibility and null-team fallback-transfer scope handling per Constitution III + FR-013 (missing)
