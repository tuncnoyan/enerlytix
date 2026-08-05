# Tasks: Homepage Refresh

**Input**: Design documents from `/specs/014-homepage-refresh/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are not included because the feature request did not ask for a TDD workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the shared routing and template structure for the homepage refresh work

- [ ] T001 Add an admin navigation placeholder for the upcoming import review page in `django_app/templates/sitesync/panel_base.html`
- [ ] T002 Add a reusable export/navigation contract stub for the new admin import page in `specs/014-homepage-refresh/contracts/routes.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core plumbing that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create the admin import review view shell and redirect handling for legacy `consumption-display` in `django_app/sitesync/views.py`
- [ ] T004 Create the new admin import review template shell in `django_app/templates/sitesync/consumption_display.html`
- [ ] T005 [P] Extend the shared dashboard JavaScript in `django_app/static/sitesync/js/site_selection.js` to support mode-aware rendering for the public home page and the admin import page
- [ ] T006 [P] Extend the supply panel endpoint contract in `django_app/sitesync/views.py` and `django_app/templates/sitesync/supply_list.html` so the supply panel can accept supply search and inactive-meter state
- [ ] T007 Add a small shared helper in `django_app/sitesync/services.py` or `django_app/sitesync/views.py` for exportable import-review row selection so both page rendering and exports use the same filtered data

**Checkpoint**: The public dashboard, admin dashboard, and admin import review page can now share the same underlying request/response model

---

## Phase 3: User Story 1 - Simplified Home Page (Priority: P1) 🎯 MVP

**Goal**: Make the public home page focus on site discovery and site selection for regular users

**Independent Test**: Open the home page as a regular user and confirm only the site-search and site-selection controls remain in the public surface

- [ ] T008 [US1] Remove the public refresh and create-report controls from `django_app/templates/sitesync/site_list.html`
- [ ] T009 [US1] Rework the page layout spacing in `django_app/templates/sitesync/site_list.html` so the site and supply columns gain more vertical room
- [ ] T010 [US1] Update the dashboard state logic in `django_app/static/sitesync/js/site_selection.js` so the public page no longer initializes report-trigger behavior
- [ ] T011 [US1] Adjust the public dashboard context in `django_app/sitesync/views.py` so the home page only supplies data needed for site filtering and supply viewing

**Checkpoint**: The public home page is usable as a simplified, regular-user entry point

---

## Phase 4: User Story 2 - Supply Filtering and Inactive Meter Toggle (Priority: P1)

**Goal**: Let users filter supplies for the selected site and control whether inactive meters are shown

**Independent Test**: Select a site, enter a supply filter, and toggle the inactive-meter option to confirm inactive supplies are hidden by default and become visible only when enabled

- [ ] T012 [US2] Add supply-search handling to the supply panel request path in `django_app/sitesync/views.py`
- [ ] T013 [US2] Add supply-search and inactive-meter controls to `django_app/templates/sitesync/supply_list.html`
- [ ] T014 [US2] Update the supply filtering logic in `django_app/static/sitesync/js/site_selection.js` so the new supply-search term and inactive-meter flag are sent with each load
- [ ] T015 [US2] Filter inactive supplies out by default in `django_app/sitesync/views.py` and preserve them only when the inactive-meter flag is enabled
- [ ] T016 [P] [US2] Update the selected-supply count and empty-state text in `django_app/templates/sitesync/supply_list.html` so the new filters are reflected clearly to the user

**Checkpoint**: Supply inspection now supports search and inactive-meter filtering without exposing inactive supplies by default

---

## Phase 5: User Story 3 - Admin Dashboard Controls (Priority: P2)

**Goal**: Move refresh and summary controls into the admin area for staff users

**Independent Test**: Open the admin dashboard and confirm the moved refresh and summary controls are available there, while the public home page stays clean

- [ ] T017 [US3] Add the moved refresh action and summary cards to `django_app/templates/sitesync/panel_dashboard.html`
- [ ] T018 [US3] Update `django_app/sitesync/views.py` so `admin_panel_view` provides the summary metrics needed by the admin dashboard
- [ ] T019 [US3] Wire the admin dashboard navigation in `django_app/templates/sitesync/panel_base.html` so the moved controls are discoverable from the admin shell
- [ ] T020 [US3] Update `django_app/static/sitesync/js/site_selection.js` so the admin-facing refresh behavior is available from the admin context rather than the public page

**Checkpoint**: Admin-only summary and refresh behavior lives in the panel area rather than the public home page

---

## Phase 6: User Story 4 - Admin Import Review Page (Priority: P2)

**Goal**: Provide a dedicated admin import review page with export actions for the current filtered view

**Independent Test**: Open the new admin import review page, confirm the data loads in the admin shell, export the current filtered view, and use the back action to return to the admin dashboard

- [ ] T021 [US4] Add the new admin import review route and namespaced URL entries in `django_app/sitesync/urls.py`
- [ ] T022 [US4] Implement the admin import review page view in `django_app/sitesync/views.py`
- [ ] T023 [US4] Update `django_app/templates/sitesync/consumption_display.html` so it uses the admin shell, omits the create-report section, and renders Export CSV / Export XLSX controls wired to the admin import export endpoints
- [ ] T024 [US4] Update `django_app/static/sitesync/js/consumption_display.js` so the page loads the admin review data and exposes the current filtered export state
- [ ] T025 [US4] Implement CSV export for the current filtered import review view in `django_app/sitesync/views.py`
- [ ] T026 [US4] Implement XLSX export for the current filtered import review view in `django_app/sitesync/views.py`
- [ ] T027 [US4] Update the Back to Dashboard navigation in `django_app/templates/sitesync/consumption_display.html` so it returns to `django_app/sitesync/views.py::admin_panel_view`

**Checkpoint**: Admin users can review imported usage and invoice data in a dedicated page and export the filtered results

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, navigation, and documentation cleanup across all stories

- [ ] T028 [P] Clean up any leftover public-page report-control references in `django_app/templates/sitesync/site_list.html` and `django_app/static/sitesync/js/site_selection.js`
- [ ] T029 [P] Verify the legacy `consumption-display` path preserves query parameters in `django_app/sitesync/urls.py` and `django_app/sitesync/views.py`
- [ ] T030 Update the homepage-refresh quickstart and route contract documentation in `specs/014-homepage-refresh/quickstart.md` and `specs/014-homepage-refresh/contracts/routes.md` if implementation details changed during build

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion
- **Polish (Phase 7)**: Depends on all intended user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - may reuse shared dashboard plumbing but remains independently testable
- **User Story 3 (P2)**: Can start after Foundational - depends on existing admin panel shell only
- **User Story 4 (P2)**: Can start after Foundational - depends on the shared import-review plumbing and admin shell only

### Within Each User Story

- Shared plumbing first, then page-specific template and view work
- Story complete before moving to the next priority
- Keep the public home page and admin page behavior aligned where they intentionally share code

### Parallel Opportunities

- T005 and T006 can run in parallel because they touch different parts of the shared dashboard pipeline
- T016 can run in parallel with T014/T015 once the supply filtering contract is in place
- T017 and T018 can run in parallel because one is template work and the other is view/context work
- T028 and T029 can run in parallel because they touch separate cleanup paths

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the public home page as the MVP

### Incremental Delivery

1. Complete Setup + Foundational
2. Deliver User Story 1 and confirm the public page is simplified
3. Deliver User Story 2 and confirm supply filtering works independently
4. Deliver User Story 3 and move admin refresh/summary controls into the panel
5. Deliver User Story 4 and complete the admin import review flow

### Parallel Team Strategy

With multiple developers:

1. One developer can implement the public home page simplification
2. One developer can implement the supply filtering and inactive-meter behavior
3. One developer can implement the admin dashboard relocation work
4. One developer can implement the admin import review page and exports

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- The feature should remain independently shippable after each story phase