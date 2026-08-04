# Tasks: Invitation-Only User Authentication

**Input**: Design documents from `/specs/013-invitation-auth-flow/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`

**Tests**: No new test-first tasks are included because the specification does not explicitly require a TDD workflow. Verification tasks run the existing and updated auth test suites.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish shared auth/email scaffolding used by multiple stories.

- [ ] T001 Create shared auth helper module in `django_app/sitesync/auth_service.py`
- [ ] T002 [P] Create invitation email templates in `django_app/templates/emails/sitesync/invitation_email.txt`
- [ ] T003 [P] Create invitation email HTML template in `django_app/templates/emails/sitesync/invitation_email.html`
- [ ] T004 [P] Create password reset email templates in `django_app/templates/registration/password_reset_email.html`
- [ ] T005 [P] Create password reset email text template in `django_app/templates/registration/password_reset_email.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core lifecycle and routing updates that block all user story implementation.

**CRITICAL**: No user story work starts until this phase is complete.

- [ ] T006 Update invitation lifecycle states and validation methods in `django_app/sitesync/models.py`
- [ ] T007 Create invitation lifecycle migration in `django_app/sitesync/migrations/`
- [ ] T008 Update invitation validation and duplicate handling form logic in `django_app/sitesync/forms.py`
- [ ] T009 Refactor invitation email send/render helpers to use templates in `django_app/sitesync/views.py`
- [ ] T010 Wire password reset and token routes in `django_app/config/urls.py`
- [ ] T011 Configure password reset template usage and backend consistency in `django_app/config/settings.py`
- [ ] T041 Add redirect from legacy `/users/` to `/panel/users/` in `django_app/sitesync/urls.py`

**Checkpoint**: Foundation complete; user stories can be implemented independently.

---

## Phase 3: User Story 1 - Admin Manages Invitation-Only Access (Priority: P1) 🎯 MVP

**Goal**: Admins can create, reuse, copy, resend, and revoke invitations from admin UI even if email delivery is unavailable.

**Independent Test**: Admin creates an invitation, sees a full invitation link, copies it successfully, and can revoke a pending invitation.

### Implementation for User Story 1

- [ ] T012 [US1] Implement pending invitation reuse/revoke action handling in `django_app/sitesync/views.py`
- [ ] T013 [US1] Add revoke invitation audit action constants in `django_app/sitesync/services.py`
- [ ] T014 [US1] Add revoke action and copy-link controls in `django_app/templates/sitesync/panel_users.html`
- [ ] T015 [P] [US1] Add admin invitation action styles in `django_app/static/sitesync/panel.css`
- [ ] T016 [P] [US1] Add copy invitation link behavior script in `django_app/static/sitesync/panel-users.js`
- [ ] T017 [US1] Load invitation action script in the canonical admin users page in `django_app/templates/sitesync/panel_users.html`

**Checkpoint**: User Story 1 is complete and independently demonstrable.

---

## Phase 4: User Story 2 - Invited User Completes Sign-Up (Priority: P1)

**Goal**: Invited users can register only via valid invitation links; invalid, used, or revoked links are blocked clearly.

**Independent Test**: A valid invite link allows sign-up and marks invite used; revoked/used/invalid links show a clear blocked state.

### Implementation for User Story 2

- [ ] T018 [US2] Enforce pending-only invitation acceptance and clear invalid states in `django_app/sitesync/views.py`
- [ ] T042 [US2] Add regression test that direct self-registration routes are unavailable in `django_app/sitesync/tests/test_auth_flow.py`
- [ ] T043 [US2] Enforce no direct signup endpoint exposure in route configuration in `django_app/config/urls.py`
- [ ] T019 [US2] Update invitation acceptance page branding and messaging in `django_app/templates/sitesync/invite_accept.html`
- [ ] T020 [P] [US2] Update login page invitation-only guidance in `django_app/templates/registration/login.html`
- [ ] T021 [P] [US2] Add invitation acceptance page styling updates in `django_app/static/sitesync/cxg-base.css`

**Checkpoint**: User Story 2 is complete and independently demonstrable.

---

## Phase 5: User Story 3 - Password Reset Support (Priority: P2)

**Goal**: Existing users can complete a secure, branded password reset through tokenized Django auth flow.

**Independent Test**: User requests reset, gets branded reset email, opens reset link, and sets a new password successfully.

### Implementation for User Story 3

- [ ] T022 [US3] Define canonical Django password reset route set (request, done, confirm, complete) in `django_app/config/urls.py`
- [ ] T023 [US3] Update app-level alias route and all internal links to the canonical reset flow in `django_app/sitesync/urls.py` and relevant templates under `django_app/templates/`
- [ ] T024 [US3] Update reset request handling and fallback messaging in `django_app/sitesync/views.py`
- [ ] T025 [US3] Create branded reset request template in `django_app/templates/registration/password_reset_form.html`
- [ ] T026 [P] [US3] Create branded reset confirmation template in `django_app/templates/registration/password_reset_done.html`
- [ ] T027 [P] [US3] Create branded reset token-entry template in `django_app/templates/registration/password_reset_confirm.html`
- [ ] T028 [P] [US3] Create branded reset completion template in `django_app/templates/registration/password_reset_complete.html`
- [ ] T029 [US3] Add password reset subject template in `django_app/templates/registration/password_reset_subject.txt`

**Checkpoint**: User Story 3 is complete and independently demonstrable.

---

## Phase 6: User Story 4 - Logout Requires Confirmation (Priority: P2)

**Goal**: Users must explicitly confirm logout in an in-place modal before session termination.

**Independent Test**: Clicking logout opens modal; cancel preserves session; confirm logs out and redirects to signed-out state.

### Implementation for User Story 4

- [ ] T030 [US4] Create reusable logout confirmation modal partial in `django_app/templates/sitesync/_logout_confirm_modal.html`
- [ ] T031 [US4] Integrate modal trigger and form wiring in `django_app/templates/sitesync/_topbar.html`
- [ ] T032 [US4] Integrate modal trigger and form wiring in `django_app/templates/sitesync/panel_base.html`
- [ ] T033 [US4] Integrate modal trigger and form wiring in `django_app/templates/sitesync/profile.html`
- [ ] T034 [P] [US4] Implement logout modal client behavior in `django_app/static/sitesync/logout-confirm.js`
- [ ] T035 [P] [US4] Add modal styling for user pages in `django_app/static/sitesync/cxg-base.css`
- [ ] T036 [P] [US4] Add modal styling for admin panel pages in `django_app/static/sitesync/panel.css`

**Checkpoint**: User Story 4 is complete and independently demonstrable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cross-story hardening, verification, and documentation alignment.

- [ ] T037 Update auth and invitation API behavior notes in `docs/API.md`
- [ ] T038 Run auth-focused Docker test suite from `specs/013-invitation-auth-flow/quickstart.md`
- [ ] T039 Run Django system checks in Docker using `django_app/manage.py check`
- [ ] T040 [P] Validate manual quickstart scenarios and record outcomes in `specs/013-invitation-auth-flow/quickstart.md`
- [ ] T044 Measure and record SC-002 invitation-copy completion times (target under 30 seconds) in `specs/013-invitation-auth-flow/quickstart.md`
- [ ] T045 Measure and record SC-004 password-reset email usability timing (target within 2 minutes) in `specs/013-invitation-auth-flow/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion; blocks all user stories.
- **Phases 3-6 (User Stories)**: Depend on Phase 2 completion.
- **Phase 7 (Polish)**: Depends on completion of all required user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after foundational completion; no dependency on other stories.
- **US2 (P1)**: Starts after foundational completion; independent from US1 implementation tasks.
- **US3 (P2)**: Starts after foundational completion; can run in parallel with US1/US2.
- **US4 (P2)**: Starts after foundational completion; can run in parallel with US1-US3.

### Within Each User Story

- View/controller logic before template wiring where both touch the same action flow.
- Template markup before story-specific JS/CSS polish.
- Story implementation before cross-cutting verification tasks.

---

## Parallel Opportunities

- Setup templates in T002-T005 can run in parallel.
- US1 UI polish tasks T015-T016 can run in parallel after T014.
- US2 guidance/style tasks T020-T021 can run in parallel after T018.
- US3 template tasks T026-T028 can run in parallel after route wiring.
- US4 style/script tasks T034-T036 can run in parallel after modal partial and wiring tasks.
- Polish validation task T040 can run in parallel with T038/T039 once implementation is complete.

---

## Parallel Example: User Story 1

```bash
# Parallelize admin invitation UI assets after core template update
Task T015: Add admin invitation action styles in django_app/static/sitesync/panel.css
Task T016: Add copy invitation link behavior script in django_app/static/sitesync/panel-users.js
```

## Parallel Example: User Story 2

```bash
# Parallelize UX refinements after acceptance logic update
Task T020: Update login page invitation-only guidance in django_app/templates/registration/login.html
Task T021: Add invitation acceptance page styling updates in django_app/static/sitesync/cxg-base.css
```

## Parallel Example: User Story 3

```bash
# Build reset completion templates in parallel
Task T026: Create branded reset confirmation template in django_app/templates/registration/password_reset_done.html
Task T027: Create branded reset token-entry template in django_app/templates/registration/password_reset_confirm.html
Task T028: Create branded reset completion template in django_app/templates/registration/password_reset_complete.html
```

## Parallel Example: User Story 4

```bash
# Parallelize logout modal behavior and styling
Task T034: Implement logout modal client behavior in django_app/static/sitesync/logout-confirm.js
Task T035: Add modal styling for user pages in django_app/static/sitesync/cxg-base.css
Task T036: Add modal styling for admin panel pages in django_app/static/sitesync/panel.css
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1 and Phase 2.
2. Deliver US1 admin invitation management.
3. Deliver US2 invitation-only sign-up acceptance.
4. Validate invitation-only onboarding end to end.

### Incremental Delivery

1. Foundation first (Phases 1-2).
2. Add US1 and validate independently.
3. Add US2 and validate independently.
4. Add US3 and validate independently.
5. Add US4 and validate independently.
6. Finish with Phase 7 verification and docs alignment.

### Parallel Team Strategy

1. Team completes setup and foundational phases together.
2. Split US1/US2/US3/US4 across developers after Phase 2 checkpoint.
3. Merge for final polish and Docker-based validation runs.
