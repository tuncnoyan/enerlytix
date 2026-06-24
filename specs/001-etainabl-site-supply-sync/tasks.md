# Tasks: Etainabl Site & Supply Sync

**Input**: Design documents from `specs/001-etainabl-site-supply-sync/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Contract and integration tests are included (TDD approach).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Django project**: `django_app/`
- **Tests**: `tests/`
- **Docker**: `django_app/docker/`
- **Sitesync app**: `django_app/sitesync/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Docker containerization

- [x] T001 Create Django project structure per implementation plan at `django_app/`
- [x] T002 Create `django_app/requirements.txt` with Django 5.x, djangorestframework, requests, psycopg2-binary, pytest, pytest-django dependencies
- [x] T003 [P] Create `django_app/docker/Dockerfile` for Python 3.12 + Django application
- [x] T004 [P] Create `django_app/docker/docker-compose.yml` with Django web service and PostgreSQL database service
- [x] T005 Create `.env.example` in repository root with ETAINABL_API_KEY, DATABASE_URL, DEBUG, ALLOWED_HOSTS placeholders
- [x] T006 Create `django_app/config/settings.py` with database configuration, installed apps (sitesync, rest_framework), logging, and secret key setup
- [x] T007 [P] Create `django_app/config/urls.py` with root URL routing for sitesync app
- [x] T008 [P] Create `django_app/config/wsgi.py` for WSGI application
- [x] T009 Create `django_app/manage.py` Django management script

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can proceed

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Create Django sitesync app structure in `django_app/sitesync/` with __init__.py, admin.py, apps.py
- [x] T011 [P] Create `django_app/sitesync/models.py` with Site model (id, external_id, name, description, created_at, updated_at) and Supply model (id, site_id, external_id, name, utility_type, device_id, created_at, updated_at)
- [x] T012 [P] Create `django_app/sitesync/serializers.py` with SiteSerializer and SupplySerializer for JSON response formatting
- [x] T013 Create database migrations for Site and Supply models
- [x] T014 Create `django_app/sitesync/services.py` with EtainaibleSyncService class that:
  - Fetches assets from Etainabl API endpoint
  - Fetches accounts from Etainabl API endpoint
  - Handles pagination and retries on failures
  - Deduplicates records by external_id
  - Performs upsert (create or update) operations for Site and Supply models
- [x] T015 [P] Create `django_app/sitesync/admin.py` to register Site and Supply models in Django admin for debugging
- [x] T016 Create `django_app/sitesync/apps.py` with AppConfig and ready() hook to trigger initial sync on app startup
- [ ] T017 Create integration test in `tests/integration/test_etainabl_sync.py` to verify sync service can fetch, parse, and persist site/supply records
- [ ] T018 Create unit test in `tests/unit/test_models.py` to verify Site and Supply model creation, uniqueness constraints, and relationships
- [ ] T018b Create unit test in `tests/unit/test_deduplication.py` to verify that repeated sync calls do not create duplicate Site or Supply records when external_id matches
- [x] T018c [P] Create `django_app/sitesync/environment_config.py` to load and validate Etainabl API key, base URL, and other config from environment variables (ETAINABL_API_KEY, ETAINABL_API_URL); raise error if required env vars missing
- [x] T018d [P] Update `django_app/config/settings.py` to enforce HTTPS in production, configure Django session and CSRF security settings, and set database SSL requirement
- [x] T018e [P] Create `.env.example` in repository root with ETAINABL_API_KEY, ETAINABL_API_URL, DATABASE_URL, DEBUG, SECRET_KEY, ALLOWED_HOSTS placeholders (emphasize .env should NOT be committed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load and Persist Etainabl Site/Supply Data (Priority: P1) 🎯 MVP

**Goal**: Ensure the app fetches and persists the full Etainabl site and supply catalog on startup or manual sync

**Independent Test**: Verify app starts, calls Etainabl API, and populates Site and Supply tables without errors or duplicates

### Implementation for User Story 1

- [x] T019 [US1] Create API client helper in `django_app/sitesync/services.py` to authenticate with Etainabl using API key from environment (implemented as `api_client.py`)
- [x] T020 [US1] Implement asset sync method in `django_app/sitesync/services.py` to fetch all assets from Etainabl endpoint
- [x] T021 [US1] Implement account sync method in `django_app/sitesync/services.py` to fetch all accounts from Etainabl endpoint
- [x] T022 [US1] Add deduplication logic in `django_app/sitesync/services.py` to prevent duplicate Site and Supply records by external_id
- [x] T023 [US1] Add error handling and logging in `django_app/sitesync/services.py` for API failures and sync exceptions
- [x] T024 [US1] Implement automatic sync trigger on application startup in `django_app/sitesync/apps.py`
- [x] T025 [US1] Create integration test in `tests/integration/test_initial_sync.py` to verify full sync flow end-to-end
- [x] T026 [US1] Add logging output to console and file to verify sync completion with record counts

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

**Goal**: Display supply details (name, utility type, device ID) adjacent to selected site

**Independent Test**: Verify supplies for a selected site display with all required fields

### Tests for User Story 3

- [ ] T033 [P] Contract test for supply list endpoint in `tests/contract/test_supply_endpoints.py`
- [ ] T034 [P] Unit test for supply filtering by site in `tests/unit/test_supply_filtering.py`
- [ ] T035 Integration test for supply list display in `tests/integration/test_supply_list_view.py`

### Implementation for User Story 3

- [ ] T036 [P] Create supply list API view/serializer in `django_app/sitesync/views.py` (extend from T026)
- [ ] T037 Create URL route for supplies by site in `django_app/sitesync/urls.py`
- [ ] T038 Add supply list template/partial in `django_app/sitesync/templates/sitesync/supply_list.html`
- [ ] T039 Extend site list template to include adjacent supply pane in `django_app/sitesync/templates/sitesync/site_list.html`
- [ ] T040 [P] Add JavaScript to handle site selection and supply panel update in `django_app/static/js/site_selection.js`
- [ ] T041 Add "no supplies" message handling for sites with no related supplies in `django_app/sitesync/templates/sitesync/supply_list.html`

**Checkpoint**: User Stories 1, 2, and 3 are fully functional and independently testable

---

## Phase 6: User Story 4 - Settings Panel for Runtime Configuration (Priority: P2)

**Goal**: Display and allow editing of runtime configuration parameters on a single settings page

**Independent Test**: Verify settings page loads configuration values and persists user edits

### Tests for User Story 4

- [ ] T042 [P] Contract test for settings endpoint in `tests/contract/test_settings_endpoints.py`
- [ ] T043 [P] Unit test for settings model save/load in `tests/unit/test_settings_model.py`
- [ ] T044 Integration test for settings page flow in `tests/integration/test_settings_view.py`

### Implementation for User Story 4

- [ ] T045 Create AppSettings model in `django_app/sitesync/models.py` to persist edited configuration values (api_url, page_size, timeout, etc.)
- [ ] T046 Create settings serializer and API view in `django_app/sitesync/serializers.py` and `django_app/sitesync/views.py`
- [ ] T047 Create URL routes for GET and POST settings in `django_app/sitesync/urls.py`
- [ ] T048 Create settings configuration loader in `django_app/sitesync/services/config_service.py` to load from `.env` in dev/test and from AppSettings model
- [ ] T049 Create settings form in `django_app/sitesync/forms.py` with validation for configuration parameters
- [ ] T050 Create settings page template in `django_app/sitesync/templates/sitesync/settings_panel.html` displaying Etainabl base URL, page sizes, timeout values
- [ ] T051 [P] Add JavaScript for settings form submission in `django_app/static/js/settings.js`
- [ ] T052 Add link to settings panel in site list template navigation in `django_app/sitesync/templates/sitesync/site_list.html`
- [ ] T053 Implement settings persistence logic that saves user edits to the database in `django_app/sitesync/services/config_service.py`

**Checkpoint**: All user stories 1-4 are complete and independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, error handling, logging, and final validation

- [ ] T054 [P] Add comprehensive logging to all services in `django_app/sitesync/`
- [ ] T055 [P] Add error handling for empty site/supply states in templates and views
- [ ] T056 Add manual sync refresh button to site list page in `django_app/sitesync/templates/sitesync/site_list.html`
- [ ] T057 Implement API error response formatting in `django_app/sitesync/views.py`
- [ ] T058 [P] Create README documentation in `django_app/README.md` with setup and configuration instructions
- [ ] T059 [P] Create API documentation in `docs/API.md` describing all endpoints
- [ ] T060 Run quickstart validation scenarios from `specs/001-etainabl-site-supply-sync/quickstart.md` and verify all acceptance criteria
- [ ] T061 [P] Add unit tests for edge cases (no sites, API timeouts, malformed responses) in `tests/unit/`
- [ ] T062 Create performance test for site list load in `tests/performance/test_load_time.py` (validate <3 second load time)
- [ ] T063 [P] Create integration test in `tests/integration/test_sync_success_rate.py` to validate SC-002: at least 95% of records persisted on first sync (minimum 100 test records)
- [ ] T064 Document .env fallback behavior and secret management approach in `docs/SECRET_MANAGEMENT.md` including supported platforms (Kubernetes, Azure, Docker Secrets)
- [ ] T065 [P] Create TLS/HTTPS and database SSL configuration in `django_app/config/settings.py` to enforce encryption in transit and database SSL per Constitution III
- [ ] T066 [P] Create deployment approval workflow documentation in `deployment/APPROVAL_PROCESS.md` requiring code review and security sign-off before any production deployment (Constitution IV)
- [ ] T067 [P] Create security hardening checklist: verify secrets sourced from env vars, database SSL enabled, no secrets in logs, TLS/HTTPS enforced
- [ ] T068 Test Docker Compose startup on Windows (Docker Desktop) to validate Windows-native compatibility and confirm no admin privileges required

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

- **User Story 1 (P1)**: No dependencies on other stories - can start immediately after Foundational
- **User Story 2 (P2)**: Depends on US1 data being available - site list requires synced sites
- **User Story 3 (P3)**: Depends on US2 UI - supply display is adjacent to site selection
- **User Story 4 (P2)**: No dependencies on US1-3 - can be worked in parallel after Foundational

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

## Incremental Delivery Plan

1. **Release 1.0 (MVP)**: US1 complete - automatic sync works, data persisted ✅ US1
2. **Release 1.1**: Add US2 - searchable site display ✅ US1 + US2
3. **Release 1.2**: Add US3 - supply details ✅ US1 + US2 + US3
4. **Release 1.3**: Add US4 - settings panel ✅ US1 + US2 + US3 + US4

---
