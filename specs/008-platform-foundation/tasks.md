# Tasks: Platform Foundation

**Input**: Design documents from `/specs/008-platform-foundation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/user-management.md

**Tests**: Docker-integrated tests executed via `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test`

**Organization**: Tasks organized by implementation phase. Phases 1-3 are complete and verified; Phases 4-7 require implementation.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story reference (e.g., [US1], [US2], [US3], [US4], [US5])
- File paths are exact and relative to `django_app/` directory

---

## Phase 1: Authentication and Account Access ✅ COMPLETE & VERIFIED

**Purpose**: Secure user authentication and personal account management

**Status**: 3 integration tests passing in Docker environment:
- `tests/integration/test_auth_flow.py`: Login, logout, profile access

**Verified Artifacts**:
- ✅ `sitesync/views.py`: `user_login_view()`, `user_logout_view()`, `profile_view()`
- ✅ `sitesync/urls.py`: `/login/`, `/logout/`, `/profile/` routes
- ✅ `templates/registration/login.html`, `sitesync/profile.html`
- ✅ `sitesync/forms.py`: User authentication forms
- ✅ Route protection with `@login_required` decorator

**Test Execution**:
```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_auth_flow
```

### Phase 1 Tasks (Verified Complete)

- [x] T001 [US1] Authentication views (login, logout, profile) in `sitesync/views.py` — VERIFIED
- [x] T002 [US1] Authentication forms in `sitesync/forms.py` — VERIFIED
- [x] T003 [US1] Authentication templates (login, profile) in `templates/registration/` — VERIFIED
- [x] T004 [US1] URL routing for auth flows in `sitesync/urls.py` — VERIFIED
- [x] T005 [US1] Route protection with `@login_required` and role checks — VERIFIED

---

## Phase 2: Invitation-Based Onboarding ✅ COMPLETE & VERIFIED

**Purpose**: Controlled user registration through invitation-only access

**Status**: 3 integration tests passing in Docker environment:
- `tests/integration/test_invitations.py`: Invitation validity, expiry, acceptance

**Verified Artifacts**:
- ✅ `sitesync/models.py`: `Invitation` model with 7-day expiry, status tracking, `is_valid()` and `accept()` methods
- ✅ `sitesync/views.py`: `accept_invitation_view()` for invitation acceptance
- ✅ `sitesync/forms.py`: `InvitationAcceptanceForm` for new user creation
- ✅ `templates/sitesync/invite_accept.html`
- ✅ Migrations: 0001-0013 completed with Invitation model

**Test Execution**:
```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_invitations
```

### Phase 2 Tasks (Verified Complete)

- [x] T006 [US2] Invitation model in `sitesync/models.py` with expiry logic — VERIFIED
- [x] T007 [US2] Invitation acceptance view in `sitesync/views.py` — VERIFIED
- [x] T008 [US2] Invitation acceptance form in `sitesync/forms.py` — VERIFIED
- [x] T009 [US2] Invitation acceptance template in `templates/sitesync/invite_accept.html` — VERIFIED
- [x] T010 [US2] Database migrations for Invitation model — VERIFIED

---

## Phase 3: User Administration and Roles ✅ COMPLETE & VERIFIED

**Purpose**: Administrator user management and multi-role support

**Status**: 4 integration tests passing in Docker environment:
- `tests/integration/test_user_admin.py`: User listing, invitation creation, account actions

**Verified Artifacts**:
- ✅ `sitesync/models.py`: User model with role support
- ✅ `sitesync/views.py`: `user_admin_view()` for user listing and actions
- ✅ `sitesync/forms.py`: `InvitationForm`, `AccountActionForm`
- ✅ `templates/sitesync/user_admin.html`: Admin UI
- ✅ Admin access control via `is_staff` / `is_superuser` checks
- ✅ Account actions: enable, disable, rename, password reset, delete

**Test Execution**:
```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_user_admin
```

### Phase 3 Tasks (Verified Complete)

- [x] T011 [US3] User administration view in `sitesync/views.py` — VERIFIED
- [x] T012 [P] [US3] User listing template in `templates/sitesync/user_admin.html` — VERIFIED
- [x] T013 [P] [US3] Invitation creation form in `sitesync/forms.py` — VERIFIED
- [x] T014 [US3] Account action handlers (enable, disable, rename, reset, delete) in `sitesync/views.py` — VERIFIED
- [x] T015 [US3] Admin role enforcement and access control — VERIFIED
- [x] T016 [P] [US3] Password reset implementation and templates in `templates/registration/password_reset*.html` — VERIFIED

---

## Phase 4: Team Hierarchy and Management 🎯 READY FOR IMPLEMENTATION

**Goal**: Enable hierarchical team structures with user assignments and role management within teams.

**Independent Test**: Create a root team, assign a manager, create a sub-team under it, assign users, change the manager, and verify the hierarchy structure and role assignments are persisted correctly.

**Dependencies**: Must complete Phase 3 first. Phases 4 and 5 can run in parallel after Phase 3.

### Tests for Phase 4 (OPTIONAL - recommended for TDD)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US4] Contract test for Team CRUD endpoints in `tests/contract/test_team_management.md` — Define POST /teams/, GET /teams/{id}, PUT /teams/{id}, DELETE /teams/{id}
- [ ] T018 [P] [US4] Contract test for user team assignment in `tests/contract/test_user_team_assignment.md` — Define POST /users/{id}/assignments, GET /users/{id}/assignments
- [ ] T019 [US4] Integration test for team creation and hierarchy in `tests/integration/test_team_hierarchy.py` — Test creating root team, sub-team, verifying parent_team FK, hierarchy traversal

### Implementation for Phase 4

- [ ] T020 [P] [US4] Create Team model in `sitesync/models.py` with parent_team FK, manager, team_lead fields — Includes parent reference, manager FK, team_lead FK, created_at, updated_at
- [ ] T021 [P] [US4] Create UserTeamAssignment model in `sitesync/models.py` — Tracks user-to-team membership with assigned_at, assigned_by fields
- [ ] T022 [P] [US4] Create RoleAssignment model in `sitesync/models.py` — Multi-valued role storage (user + role_name pairs) for overlapping roles
- [ ] T023 [US4] Create database migrations for Team, UserTeamAssignment, RoleAssignment models in `sitesync/migrations/` — New migration file (e.g., 0014_team.py)
- [ ] T024 [P] [US4] Create TeamForm in `sitesync/forms.py` — Form for team creation, name, parent_team selection, manager selection
- [ ] T025 [P] [US4] Create UserTeamAssignmentForm in `sitesync/forms.py` — Form for assigning users to teams
- [ ] T026 [P] [US4] Create RoleAssignmentForm in `sitesync/forms.py` — Form for assigning roles to users
- [ ] T027 [US4] Create team management view in `sitesync/views.py`: `team_list_view()` — GET returns paginated team list with hierarchy info; POST creates new team
- [ ] T028 [US4] Create team detail and edit view in `sitesync/views.py`: `team_detail_view()` — GET returns team details and members; PUT/POST edits team properties, manager, team_lead
- [ ] T029 [US4] Create user team assignment view in `sitesync/views.py`: `user_team_assignment_view()` — GET lists assignments for a user; POST creates new assignment; DELETE removes assignment
- [ ] T030 [US4] Create role assignment view in `sitesync/views.py`: `role_assignment_view()` — GET lists roles for a user; POST assigns new role; DELETE revokes role
- [ ] T031 [US4] Create team templates for UI in `templates/sitesync/team_list.html`, `team_detail.html` — List view with create button, detail view with edit form
- [ ] T032 [US4] Implement team deletion cascade logic in `sitesync/models.py` — Handle deletion of team with sub-teams and reassignment of users
- [ ] T033 [US4] Add team hierarchy traversal helper methods in `sitesync/models.py`: `get_parent_teams()`, `get_sub_teams()`, `get_all_reports_in_scope()` — For manager/lead access scoping later
- [ ] T034 [US4] Add role checking utility functions in `sitesync/models.py`: `has_role()`, `get_user_roles()`, `is_admin_or_manager()` — Reusable role checks across views
- [ ] T035 [US4] Add URL routes for team management in `sitesync/urls.py` — /teams/, /teams/<id>/, /teams/<id>/edit/, /users/<id>/assignments/, /users/<id>/roles/
- [ ] T036 [US4] Add admin decorators and access checks to team views — Ensure only admins/managers can create/edit teams; users can only see their own teams
- [ ] T037 [US4] Add logging for team operations in `sitesync/views.py` — Log team creation, modifications, user assignments for audit trail

**Checkpoint**: Team hierarchy model, CRUD operations, and user assignments fully functional and tested independently.

---

## Phase 5: Consolidated Admin Panel 🎯 READY FOR IMPLEMENTATION

**Goal**: Create a branded, consolidated admin panel at `/panel/` consolidating all admin functions (users, teams, roles, hierarchy view).

**Independent Test**: Sign in as administrator, navigate to home page, confirm admin panel link is visible in top-right menu, open `/panel/`, verify layout and colour scheme match home page, navigate through Users, Teams, and Hierarchy sections, and perform sample actions in each section.

**Dependencies**: Requires Phase 3 (user admin complete). Can run in parallel with Phase 4 (team management), but Phase 5 implementation should integrate Phase 4 models once available. Suggested approach: T038-T043 independent of team model; T044-T046 depend on Phase 4 completion.

### Tests for Phase 5 (OPTIONAL - recommended for TDD)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T038 [P] [US5] Contract test for admin panel routes in `tests/contract/test_admin_panel.md` — Define GET /panel/, GET /panel/users/, GET /panel/teams/, GET /panel/hierarchy/
- [ ] T039 [US5] Integration test for admin panel access and rendering in `tests/integration/test_admin_panel.py` — Test admin can access /panel/, non-admin denied; verify styling consistency with home page

### Implementation for Phase 5

- [ ] T040 [P] [US5] Create admin panel base template in `templates/sitesync/panel_base.html` — Match home page layout (header, navbar, colour scheme, footer). Base template with content blocks for sections.
- [ ] T041 [P] [US5] Create admin panel home view in `sitesync/views.py`: `admin_panel_view()` — GET renders /panel/ with sidebar menu and overview section; POST routes to sub-sections (users, teams, hierarchy)
- [ ] T042 [P] [US5] Create admin panel navigation menu UI in `templates/sitesync/panel_base.html` — Sidebar with links: Users, Teams, Hierarchy; includes quick-links to common actions (Create User, Create Team, View Org Chart)
- [ ] T043 [US5] Add admin panel link to home page navigation in `templates/sitesync/home.html` (or main template) — Render link in top-right menu only for admins using role check
- [ ] T044 [US5] Create admin panel users section in `templates/sitesync/panel_users.html` — Integrate existing user listing and actions from Phase 3 into panel format; maintain forms for invite, enable/disable, rename, reset, delete
- [ ] T045 [US5] Create admin panel teams section in `templates/sitesync/panel_teams.html` — Integrate team CRUD operations from Phase 4 into panel format; display team list, hierarchy tree, team detail forms
- [ ] T046 [US5] Create admin panel hierarchy view in `templates/sitesync/panel_hierarchy.html` — Visualize org structure as tree or table showing parent-child relationships, managers, team leads; allow inline editing of manager/lead assignments
- [ ] T047 [US5] Create admin panel role assignments section in `templates/sitesync/panel_roles.html` — Show users and their current roles; provide forms to add/remove roles; highlight overlapping roles
- [ ] T048 [US5] Update `sitesync/urls.py` to add panel routes — /panel/, /panel/users/, /panel/users/<action>/, /panel/teams/, /panel/teams/<id>/, /panel/teams/<action>/, /panel/hierarchy/, /panel/roles/
- [ ] T049 [US5] Add admin-only access control to panel view in `sitesync/views.py` — Decorator or check: if not (is_staff or has_admin_role), redirect to home or access denied page
- [ ] T050 [P] [US5] Create CSS styling for admin panel in `static/sitesync/panel.css` — Apply colour scheme from home page; style sidebar, sections, forms to match product brand
- [ ] T051 [US5] Add breadcrumb navigation for panel sections in `templates/sitesync/panel_base.html` — Help users understand navigation hierarchy within panel
- [ ] T052 [P] [US5] Add success/error flash messages to panel actions in `sitesync/views.py` — Provide feedback when user/team created, deleted, edited, etc.
- [ ] T053 [US5] Test panel responsiveness and accessibility — Verify panel works on mobile/tablet, keyboard navigation, screen reader compatibility

**Checkpoint**: Consolidated admin panel fully functional with all four sections (Users, Teams, Roles, Hierarchy) accessible, styled consistently with home page, and all admin operations available from a single entry point.

---

## Phase 6: Report Access Scoping and Validation 🎯 READY FOR IMPLEMENTATION

**Goal**: Implement team-gated report access where users see reports only from assigned teams; hierarchical access for managers (see managed team + sub-teams); empty-state for unassigned users.

**Independent Test**: Create a hierarchy with root team and sub-teams, assign users with different roles (admin, manager, team_lead, user) to different teams, generate sample reports, verify each user sees only reports from their assigned scope, verify new unassigned user sees empty state with prompt to request assignment.

**Dependencies**: Requires Phase 3 (user auth complete) and Phase 4 (team model complete). Phase 6 can run in parallel with Phase 5 but should integrate with the admin panel in Phase 5.

**Note**: This phase assumes reports are already generated/available in the application; tasks focus on access control and filtering, not report generation.

### Tests for Phase 6 (RECOMMENDED - access scoping is security-critical)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T054 [P] [US6] Unit test for team-gated report access in `tests/unit/test_report_access.py` — Test `get_reports_for_user()` filters by team membership, test hierarchical access returns parent + child reports
- [ ] T055 [P] [US6] Unit test for hierarchical access logic in `tests/unit/test_hierarchical_access.py` — Test manager sees own team + sub-teams; lead sees team + sub-teams within scope; user sees only own team
- [ ] T056 [US6] Integration test for report visibility across roles in `tests/integration/test_report_visibility.py` — Create team hierarchy, assign users, verify report visibility matches role and team assignment
- [ ] T057 [US6] Integration test for empty-state and onboarding messaging in `tests/integration/test_empty_state_messaging.py` — New user (no team) should see empty state; after assignment, should see reports

### Implementation for Phase 6

- [ ] T058 [P] [US6] Create report access utility function in `sitesync/services.py`: `get_reports_for_user(user)` — Returns QuerySet of reports scoped to user's team membership and role; handles null team assignment
- [ ] T059 [P] [US6] Implement hierarchical access logic in `sitesync/services.py`: `get_accessible_reports(user)` — For managers: return reports from managed team + all sub-teams; for team_lead: return team + sub-teams within scope; for user: return only assigned team; for admin: return all
- [ ] T060 [P] [US6] Add helper method in `sitesync/models.py` on UserTeamAssignment: `get_report_scope(self)` — Returns all reports accessible via this team assignment based on user role in that team
- [ ] T061 [US6] Create or update report views in sitesync app to use access scoping — Modify report list views (e.g., `report_list_view()`) to filter via `get_reports_for_user()` instead of returning all reports
- [ ] T062 [P] [US6] Create empty-state template in `templates/sitesync/reports_empty_state.html` — Show when user has no team assignment; provide button/link to request team assignment or contact admin
- [ ] T063 [US6] Update report list view to render empty state when user has no reports in `sitesync/views.py` — Check if user has any teams via UserTeamAssignment; if none, render empty state template instead of empty table
- [ ] T064 [P] [US6] Create onboarding message for newly assigned users in `templates/sitesync/reports_welcome.html` — Brief welcome message after first team assignment; explain team structure and how to access reports
- [ ] T065 [US6] Add role-based column visibility in report views in `templates/sitesync/report_list.html` or report table template — Show/hide sensitive columns based on user role (e.g., budget columns only visible to managers/admins)
- [ ] T066 [P] [US6] Add team/hierarchy filter in report list UI in `templates/sitesync/report_list.html` — Dropdown or tree to filter reports by team; only show teams user has access to
- [ ] T067 [US6] Add logging for report access events in `sitesync/services.py` — Log when user accesses reports, which reports were retrieved, filtering applied (for audit trail)
- [ ] T068 [P] [US6] Add caching for report access scopes in `sitesync/services.py` — Cache `get_accessible_reports()` result per user session to reduce database queries (use Django cache framework)
- [ ] T069 [US6] Add notification for users with no team assignment in home page template in `templates/sitesync/home.html` — Show banner or alert: "You haven't been assigned to a team. Contact your admin to get started."
- [ ] T070 [US6] Create view for users to request team assignment (optional feature) in `sitesync/views.py`: `request_team_assignment_view()` — Allow users to submit request; admin sees in panel; improves UX

**Checkpoint**: Report access fully scoped by team and role; hierarchical inheritance working; new users see empty state; all access changes logged for audit.

---

## Phase 7: Validation and Hardening 🎯 READY FOR IMPLEMENTATION

**Goal**: Comprehensive integration testing, Docker-based regression validation, documentation, and production-readiness hardening.

**Independent Test**: Execute full test suite in Docker environment; verify all auth, invitation, user admin, team, access scoping, and admin panel flows work end-to-end; test team hierarchy changes propagate correctly; validate performance with sample data load.

**Dependencies**: Requires all Phases 1-6 complete. This phase is final validation and is not blocking other phases.

### Comprehensive Test Suite for Phase 7

> **NOTE: These tests cover all user stories end-to-end and should be run continuously during implementation**

- [ ] T071 [P] [US1] Integration test for complete authentication flow in `tests/integration/test_auth_full.py` — Sign up via invitation, login, password reset, logout, profile access — ALREADY VERIFIED, review coverage
- [ ] T072 [P] [US2] Integration test for complete invitation flow in `tests/integration/test_invitation_full.py` — Create invitation, expire it, create new one, accept, create user account — ALREADY VERIFIED, review coverage
- [ ] T073 [P] [US3] Integration test for user admin operations in `tests/integration/test_user_admin_full.py` — Create user, list users, enable/disable, rename, reset password, delete — ALREADY VERIFIED, review coverage
- [ ] T074 [US4] Integration test for team hierarchy creation and changes in `tests/integration/test_team_hierarchy_full.py` — Create root team, add sub-team, change manager, change hierarchy, move team, delete team with cascade
- [ ] T075 [US4] Integration test for user assignment to multiple teams in `tests/integration/test_multi_team_assignment.py` — Assign user to 2+ teams, verify role assignments in each team, verify role overlapping, change assignments
- [ ] T076 [US5] Integration test for admin panel access and layout in `tests/integration/test_admin_panel_full.py` — Admin sees panel link and can access; non-admin cannot; verify all sections load
- [ ] T077 [US5] Integration test for admin panel user operations in `tests/integration/test_admin_panel_users.py` — Invite, enable, disable, rename, delete from panel
- [ ] T078 [US5] Integration test for admin panel team operations in `tests/integration/test_admin_panel_teams.py` — Create, edit, delete, reassign manager/lead from panel
- [ ] T079 [P] [US6] Integration test for report visibility by team in `tests/integration/test_report_access_team.py` — User sees reports only from assigned team; manager sees team + sub-teams; admin sees all
- [ ] T080 [P] [US6] Integration test for report access after hierarchy change in `tests/integration/test_report_access_hierarchy_update.py` — Create reports, create hierarchy, change manager, verify reports accessible to new manager
- [ ] T081 [P] [US6] Integration test for empty-state on unassigned user in `tests/integration/test_empty_state_unassigned.py` — New user without team sees empty state; after assignment, sees reports
- [ ] T082 [US*] Performance test with sample data load in `tests/performance/test_load_hierarchy.py` — Load 100 users, 10 teams, 5-level hierarchy; verify report access queries complete in <500ms; admin panel load in <1s

### Docker Environment Validation

- [ ] T083 Integration test execution in Docker in `.specify/scripts/powershell/test-integration.ps1` — Script to run full test suite via docker compose exec: `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test`
- [ ] T084 [P] Manual validation checklist for all user stories via running Docker app — Start app, test sign-in, create team, assign users, access reports from different roles; document steps and screenshot expectations

### Documentation and Hardening

- [ ] T085 Update quickstart.md with team hierarchy setup scenarios in `specs/008-platform-foundation/quickstart.md` — Add scenario for creating multi-level team, assigning users, verifying access
- [ ] T086 Create admin onboarding guide in `specs/008-platform-foundation/ADMIN_GUIDE.md` — How to set up org structure, create teams, assign users, manage roles, troubleshoot access issues
- [ ] T087 [P] Review and update data-model.md with finalized schema in `specs/008-platform-foundation/data-model.md` — Confirm entity definitions, relationships, migration order
- [ ] T088 [P] Create API documentation for team and role endpoints in `specs/008-platform-foundation/contracts/team-management.md` (if REST API added) — Request/response examples for all team CRUD and assignment endpoints
- [ ] T089 Security review: Audit all role checks and access control logic in `sitesync/views.py` and `sitesync/services.py` — Ensure no access bypass, test with role boundary cases
- [ ] T090 Security hardening: Add CSRF tokens to all POST forms in templates in `templates/sitesync/` — Verify Django's {% csrf_token %} present in all user-modifying forms
- [ ] T091 [P] Security hardening: Add input validation and sanitization to all forms in `sitesync/forms.py` — Review email validation, username constraints, team name length limits, etc.
- [ ] T092 Security hardening: Add rate limiting to invitation creation and password reset in `sitesync/views.py` — Prevent brute-force attacks (e.g., Django-ratelimit or custom decorator)
- [ ] T093 [P] Review and update error handling and logging throughout codebase — Ensure no sensitive data logged; all exceptions caught and handled gracefully
- [ ] T094 Create deployment checklist in `deployment/PLATFORM_FOUNDATION_CHECKLIST.md` — Pre-deployment validation steps: test suite pass, manual validation complete, Docker image tested, database backup, rollback plan

### Final Verification & Release Readiness

- [ ] T095 All tests passing in Docker environment — Run full suite: `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test`; capture test report
- [ ] T096 Manual end-to-end validation on running Docker app — Verify all 5 user stories work as documented; capture screenshots; validate performance
- [ ] T097 Code review and merge to main branch — All code reviewed, linting passed, documentation complete
- [ ] T098 Tag release and update CHANGELOG in `README.md` — Document features added, breaking changes (if any), upgrade instructions

**Checkpoint**: Platform foundation fully implemented, tested, documented, and ready for production deployment. All user stories verified. No open security or performance issues.

---

## Dependencies & Parallel Execution

### Execution Strategy

1. **Phase 1-3: Sequential completion (ALREADY DONE)** ✅
   - Each phase builds on previous; all verified with Docker tests

2. **Phase 4 & 5: Parallel execution possible after Phase 3**
   - Phase 4 (Team hierarchy): T020-T037
   - Phase 5 (Admin panel): T040-T053 (independent UI until integration with team model)
   - Merge point: T044-T046 (admin panel teams section) requires Phase 4 models
   - Suggested: Start Phase 4 and Phase 5 in parallel; Phase 5 completes core sections (users, roles, hierarchy view) first; finalize teams section after Phase 4

3. **Phase 6: Depends on Phase 4, can start after Phase 3**
   - Report access scoping requires team model
   - Suggested: Start T058-T070 after Phase 4 models available (T023 migration complete)

4. **Phase 7: Final validation across all phases**
   - Runs after Phase 6 complete
   - Tests all end-to-end flows

### Dependency Graph

```
Phase 1 (Auth) ✅
  ↓
Phase 2 (Invitations) ✅
  ↓
Phase 3 (User Admin) ✅
  ├─→ Phase 4 (Team Hierarchy) ─→ ┐
  │                                ├─→ Phase 5 (Admin Panel) ─┐
  ├────────────────────────────→ ┘                           ├─→ Phase 7 (Validation)
  │                                                            │
  └─→ Phase 6 (Report Access Scoping) ─────────────────────────┘

Parallel Opportunities:
- Phase 4 & 5 models: T020-T026 (models/forms) can run in parallel with T040-T043 (base panel UI)
- Phase 4 & 5 views: T027-T031 (team views) and T044-T049 (panel integration) can run in parallel if separated
- Phase 6 tests: T054-T056 can be written before Phase 6 implementation (TDD approach)
- Phase 7 tests: T071-T082 can be written in parallel with Phase 4-6 implementation
```

### Suggested MVP Scope

**Minimum Viable Product** (recommend as first release):
- ✅ Phases 1-3: Complete (auth, invitations, user admin)
- ✅ Phase 4: Complete (team hierarchy, essential for org structure)
- ⚠️ Phase 5: Simplified (basic team listing in existing user_admin page, defer consolidated panel to v1.1)
- ⚠️ Phase 6: Simplified (basic team-gated access for unassigned users; defer hierarchical inheritance to v1.1)
- ✅ Phase 7: Complete (comprehensive testing)

**v1.0 Release Deliverables**:
- Multi-user auth with password reset
- Invitation-based onboarding with 7-day expiry
- User administration (enable/disable, rename, delete)
- Team hierarchy with sub-teams
- Multi-role support (admin, manager, team_lead, user)
- Team-gated report access (basic)
- Docker-based regression test suite (11 tests → 25+ tests)

**Deferred to v1.1**:
- Consolidated admin panel at `/panel/`
- Advanced hierarchical report access (managers see sub-teams)
- Org chart visualization
- Request team assignment workflow

---

## Testing Strategy

### Test Execution (Docker-Native)

All tests run inside the Docker web container against live PostgreSQL:

```bash
# Full suite
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test

# By phase
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_auth_flow
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_invitations
docker compose -f django_app/docker/django-compose.yml exec -T web python manage.py test tests.integration.test_user_admin
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_team_hierarchy
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_admin_panel
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_report_access_team
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_report_visibility

# With coverage report
docker compose -f django_app/docker/docker-compose.yml exec -T web coverage run --source='sitesync' manage.py test && coverage report
```

### Test Organization

```
tests/
├── integration/
│   ├── test_auth_flow.py ✅
│   ├── test_invitations.py ✅
│   ├── test_user_admin.py ✅
│   ├── test_team_hierarchy.py (NEW)
│   ├── test_admin_panel.py (NEW)
│   ├── test_report_access_team.py (NEW)
│   ├── test_report_visibility.py (NEW)
│   └── test_empty_state_messaging.py (NEW)
├── contract/
│   ├── test_team_management.md (NEW)
│   ├── test_user_team_assignment.md (NEW)
│   └── test_admin_panel.md (NEW)
├── unit/
│   ├── test_report_access.py (NEW)
│   └── test_hierarchical_access.py (NEW)
├── performance/
│   └── test_load_hierarchy.py (NEW)
└── __init__.py
```

---

## Checkpoints & Success Criteria

| Phase | Tasks | Checkpoint | Success Criteria |
|-------|-------|------------|------------------|
| 1 | T001-T005 | Auth complete | Login, logout, profile access work; 3 tests passing |
| 2 | T006-T010 | Invitations complete | Invite creation, 7-day expiry, acceptance flow work; 3 tests passing |
| 3 | T011-T016 | User admin complete | User listing, invite, enable/disable, rename, delete work; 4 tests passing |
| 4 | T017-T037 | Team hierarchy complete | Team creation, hierarchy, user assignment, role assignment work; hierarchy tests passing |
| 5 | T038-T053 | Admin panel complete | Panel at /panel/ accessible to admins, all sections functional, styled consistently |
| 6 | T054-T070 | Report access scoped | Users see reports only for assigned teams; hierarchical access; empty state for unassigned |
| 7 | T071-T098 | Platform ready | All 25+ tests passing; manual validation complete; documentation updated; security review passed |

---

## Known Constraints & Assumptions

- **Django Version**: 3.12 (existing project)
- **Database**: PostgreSQL via Docker Compose (existing setup in `django_app/docker/docker-compose.yml`)
- **UI Framework**: Django templates (server-rendered, no frontend framework)
- **Authentication**: Django's built-in auth system with custom User model for roles
- **Deployment**: Docker Compose (containerized, Windows-native host)
- **Performance Baseline**: ~100 users, ~10 teams, reports query <500ms expected
- **Admin Panel Styling**: Must match existing home page colour scheme and layout (TBD by design review in T050)

