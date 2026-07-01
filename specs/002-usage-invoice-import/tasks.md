# Tasks: Usage Invoice Import

**Input**: Design documents from `/specs/002-usage-invoice-import/`

**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Not explicitly requested in spec as TDD-first; implementation tasks include validation via existing test suite and quickstart scenarios.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare configuration and entry points for new import/display capability.

- [X] T001 Add Xcelerate import config keys and retention default in django_app/config/settings.py
- [X] T002 Add environment variable examples for import and retention settings in .env.example
- [X] T003 [P] Add consumption import/display URL stubs in django_app/sitesync/urls.py
- [X] T004 [P] Register new route includes for sitesync in django_app/config/urls.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and shared services that block all user stories.

**CRITICAL**: Complete this phase before user story implementation.

- [X] T005 Create ImportRun, HalfHourlyConsumption, MonthlyConsumption, and InvoiceCost models in django_app/sitesync/models.py
- [X] T006 Create database migration for new consumption/invoice models in django_app/sitesync/migrations/0003_usage_invoice_import_models.py
- [X] T007 [P] Register new models in Django admin in django_app/sitesync/admin.py
- [X] T008 Implement UTC month-window helpers and canonical month key utilities in django_app/sitesync/services.py
- [X] T009 Implement Xcelerate consumption and invoices API client methods in django_app/sitesync/api_client.py
- [X] T010 Implement shared import run status/error logging helpers in django_app/sitesync/services.py
- [X] T011 Implement shared upsert repository helpers keyed by supply and source period in django_app/sitesync/services.py

**Checkpoint**: Foundation ready for independent user story execution.

---

## Phase 3: User Story 1 - Import selected supply usage and invoice data (Priority: P1) MVP

**Goal**: User selects supplies and a reporting month; system imports required half-hourly, monthly, and invoice windows and stores records.

**Independent Test**: Trigger import for one known supply and reporting month; confirm two half-hourly months, 24 monthly rows, and 12 invoice rows are stored with UTC-normalized period keys.

- [X] T012 [US1] Add request/response serializers for consumption import trigger in django_app/sitesync/serializers.py
- [X] T013 [US1] Implement import orchestration service for selected supplies and reporting month in django_app/sitesync/services.py
- [X] T014 [US1] Implement half-hourly window fetch for selected month and prior-year same month in django_app/sitesync/services.py
- [X] T015 [US1] Implement monthly consumption fetch for previous 24 months in django_app/sitesync/services.py
- [X] T016 [US1] Implement invoice cost fetch for previous 12 months in django_app/sitesync/services.py
- [X] T017 [US1] Persist imported half-hourly/monthly/invoice records with canonical month keys in django_app/sitesync/services.py
- [X] T018 [US1] Add POST import endpoint view to trigger import run in django_app/sitesync/views.py
- [X] T019 [US1] Wire POST import endpoint in django_app/sitesync/urls.py

**Checkpoint**: MVP import flow works for initial load.

---

## Phase 4: User Story 2 - Refresh previously imported values on demand (Priority: P2)

**Goal**: Re-running import updates existing records and inserts only missing ones, with retry and partial-failure behavior.

**Independent Test**: Run import twice for same supply/month; verify row counts do not duplicate, changed source values overwrite existing records, and partial failures are logged with one retry.

- [X] T020 [US2] Add refresh mode input handling for existing import endpoint in django_app/sitesync/serializers.py
- [X] T021 [US2] Implement one-retry continue-on-error policy per failed supply-period in django_app/sitesync/services.py
- [X] T022 [US2] Implement strict upsert update path for repeated imports in django_app/sitesync/services.py
- [X] T023 [US2] Enforce duplicate prevention via model constraints and conflict handling in django_app/sitesync/models.py
- [X] T024 [US2] Update import run status transitions for success/partial_failure/failed in django_app/sitesync/services.py
- [X] T025 [US2] Expose refresh behavior and run summary in POST import endpoint response in django_app/sitesync/views.py

**Checkpoint**: Refresh/update behavior is idempotent and auditable.

---

## Phase 5: User Story 3 - View imported usage and invoice values in a dedicated table page (Priority: P3)

**Goal**: User views imported records on a separate table page filtered by reporting month and supply.

**Independent Test**: Open display page for a month with imported data and verify table rows, period fields, value type, and empty-state behavior.

- [X] T026 [US3] Add display query serializers for reporting month, supply, and data type filters in django_app/sitesync/serializers.py
- [X] T027 [US3] Implement display query service for canonical month-key and source-period filtering in django_app/sitesync/services.py
- [X] T028 [US3] Add GET API endpoint returning filtered table-ready records in django_app/sitesync/views.py
- [X] T029 [US3] Wire GET display endpoint route in django_app/sitesync/urls.py
- [X] T030 [US3] Create dedicated table page template in django_app/templates/sitesync/consumption_display.html
- [X] T031 [US3] Add template-rendering view for the consumption display page in django_app/sitesync/views.py
- [X] T032 [US3] Add client-side month/supply filter interactions for display page in django_app/static/sitesync/js/consumption_display.js

**Checkpoint**: Dedicated table page is usable and matches imported dataset.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete retention, documentation, and final validation.

- [X] T033 Implement configurable retention cleanup management command in django_app/sitesync/management/commands/cleanup_expired_consumption.py
- [X] T034 [US2] Add auditable import outcome fields and persistence for per-supply and per-period results (attempt count, retry_used, failure_reason, response_code, request_window) in django_app/sitesync/models.py and django_app/sitesync/services.py
- [X] T035 [US2] Expose ImportRun audit detail endpoint/view for authorized users in django_app/sitesync/views.py and django_app/sitesync/urls.py
- [X] T036 [P] Add/update API documentation for import and display endpoints in docs/API.md
- [X] T037 [P] Document operational flow and retention behavior in django_app/README.md
- [ ] T038 Run quickstart scenario validation and record outcomes in specs/002-usage-invoice-import/plan.md
- [ ] T039 Define and execute UAT protocol for SC-004 (90% users locate/verify within 2 minutes) and record evidence in specs/002-usage-invoice-import/quickstart.md
- [ ] T040 Create import timing instrumentation and run benchmark for up to 20 supplies over required windows; document pass/fail against 95% within 10 minutes in specs/002-usage-invoice-import/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies.
- Foundational (Phase 2): depends on Setup; blocks all user stories.
- User Story phases (Phases 3-5): depend on Foundational completion.
- Polish (Phase 6): depends on completion of selected user stories.

### User Story Dependencies

- User Story 1 (P1): starts after Phase 2; no story dependency.
- User Story 2 (P2): starts after Phase 2; functionally builds on import flow from US1.
- User Story 3 (P3): starts after Phase 2; independent implementation, but validation depends on data imported via US1/US2.

### Story Completion Order

- Recommended: US1 -> US2 -> US3.
- Parallel-capable after Phase 2: US3 can be developed alongside US2 by separate contributors.

---

## Parallel Opportunities

- Setup: T003 and T004 can run in parallel.
- Foundational: T007 can run in parallel with T008-T011.
- US1: T014, T015, and T016 can be implemented in parallel once T013 starts.
- US3: T030 and T032 can run in parallel after T031 route/view context is defined.
- Polish: T036 and T037 can run in parallel.

## Parallel Example: User Story 1

```bash
Task: "T014 [US1] Implement half-hourly window fetch in django_app/sitesync/services.py"
Task: "T015 [US1] Implement monthly window fetch in django_app/sitesync/services.py"
Task: "T016 [US1] Implement invoice window fetch in django_app/sitesync/services.py"
```

## Parallel Example: User Story 3

```bash
Task: "T030 [US3] Create table template in django_app/templates/sitesync/consumption_display.html"
Task: "T032 [US3] Add filter script in django_app/static/sitesync/js/consumption_display.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (T012-T019).
3. Validate independent test criteria for US1.
4. Demo/import a real sample month before moving on.

### Incremental Delivery

1. Deliver US1 for initial import value.
2. Deliver US2 for reliable refresh/upsert behavior.
3. Deliver US3 for operational table visibility.
4. Finish retention/docs polish tasks.

### Team Parallel Strategy

1. One engineer completes Phase 1-2 foundation.
2. After checkpoint:
   - Engineer A: US1 and US2 import pipeline.
   - Engineer B: US3 display page and API.
3. Merge at Phase 6 with shared validation.

---

## Notes

- [P] tasks are parallelizable because they target different files or non-blocking workstreams.
- All task descriptions include concrete file paths for immediate execution.
- Each user story section has explicit independent test criteria.
- This task list is immediately executable with existing repository structure.


