# Tasks: Etainabl Site & Supply Sync

**Input**: Design documents from `specs/001-etainabl-site-supply-sync/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Django project**: `django_app/`
- **Tests**: `tests/`
- **Docker**: `django_app/docker/`
- **Sitesync app**: `django_app/sitesync/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Docker containerization

- [ ] T001 Create Django project structure per implementation plan at `django_app/`
- [ ] T002 Create `django_app/requirements.txt` with Django 5.x, djangorestframework, requests, psycopg2-binary, pytest, pytest-django dependencies
- [ ] T003 [P] Create `django_app/docker/Dockerfile` for Python 3.12 + Django application
- [ ] T004 [P] Create `django_app/docker/docker-compose.yml` with Django web service and PostgreSQL database service
- [ ] T005 Create `.env.example` in repository root with ETAINABL_API_KEY, DATABASE_URL, DEBUG, ALLOWED_HOSTS placeholders
- [ ] T006 Create `django_app/config/settings.py` with database configuration, installed apps (sitesync, rest_framework), logging, and secret key setup
- [ ] T007 [P] Create `django_app/config/urls.py` with root URL routing for sitesync app
- [ ] T008 [P] Create `django_app/config/wsgi.py` for WSGI application
- [ ] T009 Create `django_app/manage.py` Django management script

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can proceed

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Create Django sitesync app structure in `django_app/sitesync/` with __init__.py, admin.py, apps.py
- [ ] T011 [P] Create `django_app/sitesync/models.py` with Site model (id, external_id, name, description, created_at, updated_at) and Supply model (id, site_id, external_id, name, utility_type, device_id, created_at, updated_at)
- [ ] T012 [P] Create `django_app/sitesync/serializers.py` with SiteSerializer and SupplySerializer for JSON response formatting
- [ ] T013 Create database migrations for Site and Supply models
- [ ] T014 Create `django_app/sitesync/services.py` with EtainaibleSyncService class that:
  - Fetches assets from Etainabl API endpoint
  - Fetches accounts from Etainabl API endpoint
  - Handles pagination and retries on failures
  - Deduplicates records by external_id
  - Performs upsert (create or update) operations for Site and Supply models
- [ ] T015 [P] Create `django_app/sitesync/admin.py` to register Site and Supply models in Django admin for debugging
- [ ] T016 Create `django_app/sitesync/apps.py` with AppConfig and ready() hook to trigger initial sync on app startup
- [ ] T017 Create integration test in `tests/integration/test_etainabl_sync.py` to verify sync service can fetch, parse, and persist site/supply records
- [ ] T018 Create unit test in `tests/unit/test_models.py` to verify Site and Supply model creation, uniqueness constraints, and relationships

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load and Persist Etainabl Site/Supply Data (Priority: P1) 🎯 MVP

**Goal**: Ensure the app fetches and persists the full Etainabl site and supply catalog on startup or manual sync

**Independent Test**: Verify app starts, calls Etainabl API, and populates Site and Supply tables without errors or duplicates

### Implementation for User Story 1

- [ ] T019 [US1] Create API client helper in `django_app/sitesync/services.py` to authenticate with Etainabl using API key from environment
- [ ] T020 [US1] Implement asset sync method in `django_app/sitesync/services.py` to fetch all assets from Etainabl endpoint
- [ ] T021 [US1] Implement account sync method in `django_app/sitesync/services.py` to fetch all accounts from Etainabl endpoint
- [ ] T022 [US1] Add deduplication logic in `django_app/sitesync/services.py` to prevent duplicate Site and Supply records by external_id
- [ ] T023 [US1] Add error handling and logging in `django_app/sitesync/services.py` for API failures and sync exceptions
- [ ] T024 [US1] Implement automatic sync trigger on application startup in `django_app/sitesync/apps.py`
- [ ] T025 [US1] Create integration test in `tests/integration/test_initial_sync.py` to verify full sync flow end-to-end
- [ ] T026 [US1] Add logging output to console and file to verify sync completion with record counts

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Searchable Site List Display (Priority: P2)

**Goal**: Display sites on a web page and allow users to search by site name

**Independent Test**: Access the web page, verify site list appears, and search text narrows the site list

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create `django_app/sitesync/views.py` with SiteListView to render searchable site list template
- [ ] T027b [P] [US2] Create `django_app/sitesync/urls.py` to route site list view to `/` root path
- [ ] T028 [US2] Create `django_app/sitesync/templates/sitesync/site_supply_list.html` template with searchable site list pane (left column)
- [ ] T029 [US2] Add JavaScript search/filter functionality in template to filter sites by name in real-time
- [ ] T030 [US2] Style site list according to constitution principle and basic readability (name, site count)
- [ ] T031 [US2] Create unit test in `tests/unit/test_views.py` to verify SiteListView returns all sites and filters by search query
- [ ] T032 [US2] Create integration test in `tests/integration/test_site_search.py` to verify end-to-end site list display and search

**Checkpoint**: At this point, User Story 2 should display a searchable site list

---

## Phase 5: User Story 3 - Supply Detail Presentation (Priority: P3)

**Goal**: When a site is selected, display its related supplies with name, utility type, and device ID

**Independent Test**: Select a site and verify supplies appear with required fields

### Implementation for User Story 3

- [ ] T033 [P] [US3] Add supply list display section to `django_app/sitesync/templates/sitesync/site_supply_list.html` (right column)
- [ ] T034 [US3] Add JavaScript event handler in template to fetch and display supplies when site is selected
- [ ] T035 [P] [US3] Create AJAX endpoint in `django_app/sitesync/views.py` to return supplies for a selected site in JSON format
- [ ] T036 [US3] Add supply table rendering with name, utility_type, and device_id columns in template
- [ ] T037 [US3] Add messaging when a site has no supplies available
- [ ] T038 [US3] Create unit test in `tests/unit/test_views.py` to verify supply detail endpoint returns correct fields
- [ ] T039 [US3] Create integration test in `tests/integration/test_supply_display.py` to verify supply list renders for selected site

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Add containerization validation: build Docker image in `django_app/docker/`
- [ ] T041 [P] Add Docker Compose startup test: verify containers start and PostgreSQL is accessible
- [ ] T042 Create `django_app/docker/.dockerignore` to exclude unnecessary files from image
- [ ] T043 Add manual sync/refresh button to `django_app/sitesync/templates/sitesync/site_supply_list.html` to allow users to re-sync from Etainabl
- [ ] T044 Create endpoint in `django_app/sitesync/views.py` to handle manual sync trigger
- [ ] T045 Add comprehensive error handling UI in template to display API failures with recoverable message
- [ ] T046 [P] Add pytest configuration in `tests/pytest.ini` or `pyproject.toml`
- [ ] T047 Run full test suite in `tests/` (unit + integration) to ensure all user stories pass
- [ ] T048 Create validation summary in console output showing sync status, record counts, and any errors
- [ ] T049 [P] Documentation: Update `specs/001-etainabl-site-supply-sync/quickstart.md` with actual Docker commands and validation steps
- [ ] T050 Documentation: Create `django_app/README.md` with setup, development, and deployment instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - MVP core functionality
- **User Story 2 (P2)**: Can start after US1 is complete - Depends on populated Site table
- **User Story 3 (P3)**: Can start after US2 is complete - Depends on populated Supply table and site selection

### Within Each User Story

- Implementation tasks before integration tests
- API/service layer before view/template layer
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 Setup** (tasks marked [P]):
- T003, T004 (Docker setup) can run in parallel
- T007, T008, T009 (Django config files) can run in parallel

**Phase 2 Foundational** (tasks marked [P]):
- T011 (models) and T012 (serializers) can run in parallel
- T015 (admin) and T016 (apps) can run in parallel after models

**Phase 3 User Story 1**:
- All tasks should be sequential (sync logic is interdependent)

**Phase 4 User Story 2**:
- T027/T027b (view + routing) can start in parallel
- T031 (unit test) can start after T027

**Phase 5 User Story 3**:
- T033 (template updates) and T035 (supply endpoint) can run in parallel
- T036 (rendering) depends on T035

**Phase 6 Polish**:
- T040 (Docker build) and T041 (Docker Compose) can run in parallel
- T046, T047 (testing) can run in parallel

---

## Parallel Example: Phase 1 Setup

```bash
# Launch Docker setup tasks in parallel:
Task: "Create Dockerfile in django_app/docker/"
Task: "Create docker-compose.yml in django_app/docker/"

# Launch Django config tasks in parallel:
Task: "Create urls.py"
Task: "Create wsgi.py"
```

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch model/serializer tasks in parallel:
Task: "Create models in django_app/sitesync/models.py"
Task: "Create serializers in django_app/sitesync/serializers.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (MVP core)
4. **STOP and VALIDATE**: Verify sync works, database populates, logs show success
5. Test against quickstart.md scenarios

### Full Feature (All User Stories)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (P1)
4. Complete Phase 4: User Story 2 (P2)
5. Complete Phase 5: User Story 3 (P3)
6. Complete Phase 6: Polish & testing
7. Run full test suite and validate all user stories pass independently

---

## Task Execution Summary

- **Total Tasks**: 50
- **Phase 1 (Setup)**: 9 tasks (1 critical path, 4 parallelizable)
- **Phase 2 (Foundational)**: 9 tasks (4 parallelizable)
- **Phase 3 (User Story 1 - P1)**: 8 tasks (MVP, highest priority)
- **Phase 4 (User Story 2 - P2)**: 6 tasks (UI layer)
- **Phase 5 (User Story 3 - P3)**: 7 tasks (Detail pane)
- **Phase 6 (Polish)**: 11 tasks (Testing, docs, validation)

**Suggested MVP Scope**: Phases 1 + 2 + 3 = 26 tasks (Sync and persist Etainabl data)

**Suggested Full Scope**: Phases 1-6 = 50 tasks (Complete searchable UI with supply details)
