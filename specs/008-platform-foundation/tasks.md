# Tasks: Platform Foundation

**Input**: Design documents from `/specs/008-platform-foundation/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the Django app structure for the multi-user foundation work.

- [ ] T001 Create or confirm the Django auth templates and routes needed for the new feature in django_app/templates/registration/ and django_app/config/urls.py
- [ ] T002 Ensure the existing Django app can run with local authentication settings and test database access in django_app/docker/docker-compose.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user-story implementation can begin.

- [ ] T003 Add a reusable user-management base model and migration scaffolding for invitations and role-related state in django_app/sitesync/models.py
- [ ] T004 [P] Add authentication-related forms and validation helpers in django_app/sitesync/forms.py
- [ ] T005 [P] Register new routes and views for authentication, password reset, profile, invitation, and administration in django_app/sitesync/urls.py and django_app/sitesync/views.py
- [ ] T006 Configure access control so authenticated users are required for protected app routes and anonymous users are redirected to sign-in in django_app/config/urls.py and django_app/sitesync/views.py

---

## Phase 3: User Story 1 - Sign in securely and manage personal access (Priority: P1) 🎯 MVP

**Goal**: Deliver secure sign-in, sign-out, password reset, and profile access for authenticated users.

**Independent Test**: Create a user, sign in, request a password reset, and verify the profile page is available after authentication.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add authentication integration tests for login, logout, and profile access in django_app/sitesync/tests/test_auth_flow.py
- [ ] T008 [P] [US1] Add password reset flow tests in django_app/sitesync/tests/test_password_reset.py

### Implementation for User Story 1

- [ ] T009 [US1] Implement login and logout handling and template rendering in django_app/config/urls.py and django_app/templates/registration/login.html
- [ ] T010 [US1] Implement password reset request and confirmation handling in django_app/sitesync/views.py and related templates
- [ ] T011 [US1] Implement the user profile page and account-information display in django_app/sitesync/views.py and django_app/templates/sitesync/
- [ ] T012 [US1] Enforce authentication redirection and session-based access control in django_app/sitesync/views.py

---

## Phase 4: User Story 2 - Join the platform through invited access (Priority: P1)

**Goal**: Deliver invitation-only onboarding with expiry handling and invitation acceptance.

**Independent Test**: Issue an invitation, accept it, and confirm the new account becomes active.

### Tests for User Story 2

- [ ] T013 [P] [US2] Add invitation acceptance and expiry tests in django_app/sitesync/tests/test_invitations.py
- [ ] T014 [P] [US2] Add registration-gating tests so only valid invitations can create accounts in django_app/sitesync/tests/test_invitation_registration.py

### Implementation for User Story 2

- [x] T015 [US2] Add invitation persistence and status handling in django_app/sitesync/models.py
- [x] T016 [US2] Implement invitation creation and listing for administrators in django_app/sitesync/views.py and django_app/templates/sitesync/
- [x] T017 [US2] Implement invitation acceptance and account activation in django_app/sitesync/views.py
- [x] T018 [US2] Enforce 7-day invitation expiry and clear error handling for expired or invalid invitations in django_app/sitesync/views.py

---

## Phase 5: User Story 3 - Administer users and access rights (Priority: P1)

**Goal**: Deliver administrator-side user management and role-based access controls.

**Independent Test**: Sign in as an administrator, list users, and perform enable/disable, rename, password reset, and delete actions.

### Tests for User Story 3

- [ ] T019 [P] [US3] Add user-listing and admin-action tests in django_app/sitesync/tests/test_user_admin.py
- [ ] T020 [P] [US3] Add role-enforcement tests for administrator and standard-user access in django_app/sitesync/tests/test_roles.py

### Implementation for User Story 3

- [x] T021 [US3] Add administrator-only user listing and account-state display in django_app/sitesync/views.py and django_app/templates/sitesync/
- [x] T022 [US3] Implement enable/disable, rename, password reset, and delete actions in django_app/sitesync/views.py
- [x] T023 [US3] Implement role-based access checks so administrators can access admin functions and standard users cannot in django_app/sitesync/views.py
- [x] T024 [US3] Add user-management forms and validation for account state changes in django_app/sitesync/forms.py

---

## Phase 6: User Story 4 - Use role-based access correctly (Priority: P2)

**Goal**: Ensure the platform behaves correctly for both administrator and standard users across the new flows.

**Independent Test**: Sign in as each role and verify the expected available actions and denied actions.

### Tests for User Story 4

- [ ] T025 [P] [US4] Add end-to-end role-based access tests in django_app/sitesync/tests/test_role_access.py

### Implementation for User Story 4

- [ ] T026 [US4] Wire role checks into the relevant views and templates so admin-only features are hidden or blocked for standard users in django_app/sitesync/views.py and django_app/templates/sitesync/
- [ ] T027 [US4] Validate disabled users are blocked from sign-in and receive a clear status message in django_app/sitesync/views.py

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, docs, and hardening across all stories.

- [ ] T028 [P] Update the user-facing documentation and quickstart guidance in docs/ and specs/008-platform-foundation/quickstart.md
- [ ] T029 Run migration and test validation for the full multi-user flow using the existing Django/Docker workflow
- [ ] T030 Review access control, error handling, and account-state messages for consistency across the new user-management experience

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Stories (Phases 3-6)**: Depend on Foundational completion
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1**: No dependencies on other stories
- **User Story 2**: Depends on the authentication and account foundation from User Story 1
- **User Story 3**: Depends on the authentication and invitation foundation from User Stories 1-2
- **User Story 4**: Depends on the role model and access-control behavior from User Story 3

### Parallel Opportunities

- T004 and T005 can be implemented in parallel
- Tests within each story can be prepared in parallel
- User Story 2 and User Story 3 can proceed in parallel once the foundational work is complete

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks
2. Deliver User Story 1 as the MVP increment
3. Add User Story 2 and then User Story 3 to complete the multi-user foundation

### Incremental Delivery

1. Authentication and profile flows first
2. Invitation-based onboarding next
3. Administration and role enforcement last

## Phase 8: Convergence

- [x] T031 Implement a complete email-based password reset flow with request and confirmation handling per FR-002 (partial)
- [x] T032 Add invitation issuance, listing, and acceptance workflows for administrators and invited users per FR-004, FR-006, FR-008 (partial)
- [x] T033 Add administrator account-state controls for enable/disable, rename, password reset, and delete actions per FR-009, FR-010, FR-011, FR-012, FR-016 (partial)
- [x] T034 Enforce explicit role-based access and disabled-user sign-in blocking for administrator and standard-user workflows per FR-013, FR-014, FR-015, US4/AC1-3 (partial)
- [x] T035 Add end-to-end invitation registration and role-access regression tests plus supporting documentation updates per SC-001, SC-002, T014, T025, T028 (partial)
