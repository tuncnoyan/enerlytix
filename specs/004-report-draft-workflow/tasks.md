# Tasks: Monthly Report Draft and Final Workflow

**Input**: Design documents from `/specs/004-report-draft-workflow/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included because the feature specification defines independent test criteria for each user story.

**Organization**: Tasks are grouped by user story so each workflow increment can be built and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Wire the new report workflow entry points into the existing Django app

- [ ] T001 [P] Add monthly report editor and saved reports browser routes in `django_app/sitesync/urls.py`
- [ ] T002 [P] Add view entry points for the monthly report editor and saved reports browser in `django_app/sitesync/views.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core monthly report identity, versioning, and carry-forward infrastructure required by all stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Add `MonthlyReport`, `MonthlyReportVersion`, and `ReportComment` models plus migration `django_app/sitesync/migrations/0006_monthly_report_workflow.py`
- [ ] T004 [P] Add report workflow helper functions for report lookup, version creation, and comment carry-forward in `django_app/sitesync/services.py`
- [ ] T005 [P] Add shared report editor context assembly and saved-report list query helpers in `django_app/sitesync/views.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Save and Reopen a Monthly Draft (Priority: P1) 🎯 MVP

**Goal**: Save a monthly report as a draft, enforce one report per site/month, and reopen the same report instead of creating duplicates

**Independent Test**: Create a report for one site/month, save it as a draft, then revisit the same site/month and confirm the same report is reopened

### Tests for User Story 1

- [ ] T006 [P] [US1] Add draft-save and reopen tests in `django_app/sitesync/tests/test_report_drafts.py`

### Implementation for User Story 1

- [ ] T007 [US1] Implement draft report lookup and unique-month reopen logic in `django_app/sitesync/services.py`
- [ ] T008 [US1] Implement draft save handling and monthly report state responses in `django_app/sitesync/views.py`
- [ ] T009 [US1] Update the report editor controls for draft saving in `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Finalise and Revise a Report (Priority: P2)

**Goal**: Save a report as final, warn before editing a final report, and create a replacement final version while preserving the original final

**Independent Test**: Finalise a report, reopen it, accept the warning, and confirm the edited save creates a separate replacement final version

### Tests for User Story 2

- [ ] T010 [P] [US2] Add finalise-and-revise tests in `django_app/sitesync/tests/test_report_finalisation.py`

### Implementation for User Story 2

- [ ] T011 [US2] Implement final-version creation and immutable original-final tracking in `django_app/sitesync/services.py`
- [ ] T012 [US2] Implement the final-save warning and replacement-version flow in `django_app/sitesync/views.py`
- [ ] T013 [US2] Update the report editor UI to surface final status and confirmation messaging in `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js`

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Carry Comments Forward (Priority: P3)

**Goal**: Seed a new month from the previous month’s final report comments and clearly mark copied comments as reference-only

**Independent Test**: Finalise a report with comments, start the next month for the same site, and confirm the comment boxes are prefilled with reference warnings

### Tests for User Story 3

- [ ] T014 [P] [US3] Add carry-forward comment tests in `django_app/sitesync/tests/test_report_comment_carry_forward.py`

### Implementation for User Story 3

- [ ] T015 [US3] Implement previous-month final comment cloning in `django_app/sitesync/services.py`
- [ ] T016 [US3] Seed carried-forward comments when opening a new month in `django_app/sitesync/views.py`
- [ ] T017 [US3] Render reference warnings for carried-forward comments in `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js`

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all be independently functional

---

## Phase 6: User Story 4 - Browse Saved Reports (Priority: P4)

**Goal**: Browse saved draft and final reports by site and month, and open the selected report from the list

**Independent Test**: Open the saved reports page, confirm reports are listed with site/month/status, and open one report from the list

### Tests for User Story 4

- [ ] T018 [P] [US4] Add saved-reports browser tests in `django_app/sitesync/tests/test_saved_reports_view.py`

### Implementation for User Story 4

- [ ] T019 [US4] Implement saved-report list querying and page context in `django_app/sitesync/views.py`
- [ ] T020 [US4] Build the saved reports browser page in `django_app/templates/sitesync/saved_reports.html`
- [ ] T021 [US4] Add opening and filtering interactions for the saved reports browser in `django_app/static/sitesync/js/saved_reports.js`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and small cleanup that affects the whole workflow

- [ ] T022 [P] Run `python manage.py test` from `django_app/` and fix workflow regressions in `django_app/sitesync/tests/`
- [ ] T023 [P] Update `specs/004-report-draft-workflow/quickstart.md` with final validation notes and any route changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May build on the same report versioning helpers, but remains independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on report version history but not on the saved reports page
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on report browsing query helpers but not on the comment workflow

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services when a story adds schema changes
- Services before views/templates
- Core implementation before UI polish
- Story complete before moving to the next priority

### Parallel Opportunities

- Setup tasks T001 and T002 can run in parallel because they touch different files
- Foundational tasks T003, T004, and T005 can run in parallel because they touch different files
- User story test tasks T006, T010, T014, and T018 can run in parallel because each targets a separate test file
- User story implementation can proceed in parallel across stories once the foundational phase is complete

---

## Parallel Example: User Story 1

```bash
Task: "Add draft-save and reopen tests in django_app/sitesync/tests/test_report_drafts.py"
Task: "Implement draft report lookup and unique-month reopen logic in django_app/sitesync/services.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. Stop and validate User Story 1 independently
5. Demo the draft/reopen workflow if ready

### Incremental Delivery

1. Complete Setup + Foundational → report identity and versioning foundation ready
2. Add User Story 1 → test independently → release the draft workflow MVP
3. Add User Story 2 → test independently → preserve final-report history
4. Add User Story 3 → test independently → seed next-month comments
5. Add User Story 4 → test independently → browse saved reports

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Each story is validated independently before merge
