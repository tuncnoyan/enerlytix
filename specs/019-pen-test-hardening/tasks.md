# Tasks: Pen-Test Hardening and Readiness

**Input**: Design documents from `/specs/019-pen-test-hardening/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/security-hardening-contract.md`, `quickstart.md`

**Tests**: Included and required by spec FR-014.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an explicit file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare feature-specific scaffolding and shared security test harness.

- [X] T001 Create security hardening implementation notes and endpoint inventory in `specs/019-pen-test-hardening/research.md`
- [X] T001a Define and freeze the Sensitive Endpoint Baseline in `specs/019-pen-test-hardening/spec.md`
- [X] T002 Create security regression test module scaffold in `django_app/sitesync/tests/test_pen_test_hardening_access.py`
- [X] T003 [P] Create credential hardening test module scaffold in `django_app/sitesync/tests/test_pen_test_hardening_credentials.py`
- [X] T004 [P] Create deployment-gate and trust-boundary test module scaffold in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared mechanisms required by all stories.

**⚠️ CRITICAL**: No user story implementation starts until this phase is complete.

- [X] T005 Implement shared protected-endpoint policy helpers in `django_app/sitesync/security.py`
- [X] T006 Implement trusted-proxy CIDR parsing and source-IP resolution utility in `django_app/sitesync/security.py`
- [X] T007 Implement standardized 401/403 JSON denial helpers for API endpoints in `django_app/sitesync/security.py`
- [X] T008 Wire production fail-closed security validator entrypoint in `django_app/sitesync/apps.py`
- [X] T009 Add production security gate settings and validation configuration in `django_app/config/settings.py`
- [X] T010 Add startup/runtime gate tests for security validator behavior in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`

**Checkpoint**: Shared security primitives and production gate foundation are complete.

---

## Phase 3: User Story 1 - Close Unauthorized Access Paths (Priority: P1) 🎯 MVP

**Goal**: Ensure sensitive endpoints/actions require authentication and role-appropriate authorization.

**Independent Test**: Validate protected endpoints with anonymous, non-admin, and admin users and confirm 401/403 semantics and no unauthorized side effects.

### Tests for User Story 1

- [X] T011 [US1] Add API access-control tests for import/report/consumption endpoints in `django_app/sitesync/tests/test_pen_test_hardening_access.py`
- [X] T012 [US1] Add settings and manual-sync authorization tests in `django_app/sitesync/tests/test_pen_test_hardening_access.py`
- [X] T013 [US1] Add import-run detail endpoint authorization tests in `django_app/sitesync/tests/test_pen_test_hardening_access.py`

### Implementation for User Story 1

- [X] T014 [US1] Enforce authenticated permission class for `consumption_import_view` in `django_app/sitesync/views.py`
- [X] T015 [US1] Enforce authenticated permission class for `consumption_display_api_view` and `report_data_api_view` in `django_app/sitesync/views.py`
- [X] T016 [US1] Enforce authenticated permission class for `import_run_detail_view` with 401/403 behavior in `django_app/sitesync/views.py`
- [X] T017 [US1] Add admin-role authorization checks for `manual_sync_view` in `django_app/sitesync/views.py`
- [X] T018 [US1] Add admin-role authorization checks for settings mutation and capacity upload paths in `django_app/sitesync/views.py`
- [X] T019 [US1] Apply shared protected-endpoint helpers across sensitive route handlers in `django_app/sitesync/views.py`
- [X] T020 [US1] Add/adjust denied-access audit event coverage for newly protected surfaces in `django_app/sitesync/views.py`
- [X] T021 [US1] Align protected route expectations documentation in `specs/019-pen-test-hardening/contracts/security-hardening-contract.md`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Secure Account and Credential Workflows (Priority: P2)

**Goal**: Replace predictable resets with one-time 15-minute recovery and enforce invitation password quality.

**Independent Test**: Verify reset flow uses single-use 15-minute recovery token and invitation acceptance rejects weak passwords.

### Tests for User Story 2

- [X] T022 [US2] Add admin reset-flow tests ensuring no static password assignment in `django_app/sitesync/tests/test_pen_test_hardening_credentials.py`
- [X] T023 [US2] Add one-time 15-minute token lifecycle tests in `django_app/sitesync/tests/test_pen_test_hardening_credentials.py`
- [X] T024 [US2] Add invitation acceptance password-strength validation tests in `django_app/sitesync/tests/test_pen_test_hardening_credentials.py`

### Implementation for User Story 2

- [X] T025 [US2] Replace static password reset behavior in admin account action flow in `django_app/sitesync/views.py`
- [X] T026 [US2] Implement single-use 15-minute recovery issuance and invalidation logic in `django_app/sitesync/auth_service.py`
- [X] T027 [US2] Integrate secure recovery email generation/sending for reset flow in `django_app/sitesync/auth_service.py`
- [X] T028 [US2] Enforce Django password validators during invitation acceptance in `django_app/sitesync/views.py`
- [X] T029 [US2] Add invitation/reset failure audit metadata sanitization updates in `django_app/sitesync/views.py`

**Checkpoint**: User Story 2 is independently functional and testable.

---

## Phase 5: User Story 3 - Demonstrate Deployment-Grade Security Defaults (Priority: P3)

**Goal**: Enforce fail-closed production posture, trusted proxy boundaries, redirect safety, and sanitized error responses.

**Independent Test**: Validate production-like gate failures, forwarding-header trust constraints, redirect rejection rules, and no exception detail leakage.

### Tests for User Story 3

- [X] T030 [US3] Add open-redirect rejection tests for manual sync return path in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`
- [X] T031 [US3] Add sanitized error-response tests for sync and other failure paths in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`
- [X] T032 [US3] Add forwarded-header trust boundary tests for proxy CIDR allowlist behavior in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`
- [X] T033 [US3] Add deploy-check and startup-block expectation tests in `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`

### Implementation for User Story 3

- [X] T034 [US3] Harden manual sync `next` redirect validation against scheme-relative and external targets in `django_app/sitesync/views.py`
- [X] T035 [US3] Replace raw exception detail responses with sanitized payloads and internal logging in `django_app/sitesync/views.py`
- [X] T036 [US3] Apply trusted proxy CIDR allowlist to `_get_client_ip` resolution flow in `django_app/sitesync/views.py`
- [X] T037 [US3] Enforce secure production defaults and fail-closed checks for secret/transport/cookie controls in `django_app/config/settings.py`
- [X] T038 [US3] Update deployment security check guidance with startup blocking rules in `deployment/SECURITY_CHECKLIST.md`

**Checkpoint**: User Story 3 is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation sync, and release readiness evidence.

- [X] T039 [P] Update secret and trust-boundary operational guidance in `docs/SECRET_MANAGEMENT.md`
- [X] T040 [P] Update platform hardening checklist controls for 401/403 and protected endpoints in `deployment/PLATFORM_FOUNDATION_CHECKLIST.md`
- [X] T041 Execute quickstart validation scenarios and record outcomes in `specs/019-pen-test-hardening/quickstart.md`
- [X] T042 Run full regression and deploy checks in Docker, validate 100% Sensitive Endpoint Baseline coverage for SC-001, and document pass evidence in `specs/019-pen-test-hardening/research.md`
- [X] T043 Map FR-011 Required Production Security Controls to explicit runtime validator checks and CI assertions in `django_app/config/settings.py` and `django_app/sitesync/tests/test_pen_test_hardening_runtime.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2; can proceed independently of US1 once foundation is complete.
- **Phase 5 (US3)**: Depends on Phase 2; can proceed independently of US1/US2 once foundation is complete.
- **Phase 6 (Polish)**: Depends on completion of desired user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories.
- **US2 (P2)**: No dependency on US1/US3; shares foundational security primitives only.
- **US3 (P3)**: No dependency on US1/US2; shares foundational security primitives only.

### Within Each User Story

- Tests first and expected to fail before implementation.
- Behavior changes before documentation alignment.
- Story must pass its independent test criteria before considered complete.

---

## Parallel Opportunities

- Setup tasks `T003` and `T004` can run in parallel after `T002`.
- Polish documentation tasks `T039` and `T040` can run in parallel.
- After Phase 2, implementation can run in parallel across stories on different files: `T014` (`views.py`), `T026` (`auth_service.py`), and `T037` (`settings.py`).

---

## Parallel Example: User Story 1

```bash
# Parallel work after Phase 2 across different files
T014 django_app/sitesync/views.py
T026 django_app/sitesync/auth_service.py
T037 django_app/config/settings.py
```

## Parallel Example: User Story 2

```bash
# Parallel documentation updates in different files
T039 docs/SECRET_MANAGEMENT.md
T040 deployment/PLATFORM_FOUNDATION_CHECKLIST.md
```

## Parallel Example: User Story 3

```bash
# Parallel setup scaffolding in different files
T003 django_app/sitesync/tests/test_pen_test_hardening_credentials.py
T004 django_app/sitesync/tests/test_pen_test_hardening_runtime.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Deliver US1 (Phase 3) to close highest-risk unauthorized access paths.
3. Validate with Docker-based regression tests and endpoint access checks.

### Incremental Delivery

1. Ship US1 to eliminate critical exposure first.
2. Add US2 credential hardening.
3. Add US3 deployment-grade fail-closed and trust-boundary controls.
4. Complete polish and release evidence tasks.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. Split story implementation after Phase 2:
   - Engineer A: US1 endpoint protection and authz
   - Engineer B: US2 credential flow hardening
   - Engineer C: US3 runtime/deployment hardening
3. Converge in Phase 6 for integrated validation and documentation.

---

## Notes

- `[P]` tasks are marked only where work can proceed without unresolved dependencies.
- User-story labels provide traceability from `spec.md` to implementation.
- All validation commands should run in Docker environment per constitution.
- No task omits a target file path; all tasks are execution-ready for LLM implementation.
