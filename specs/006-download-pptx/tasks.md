# Tasks: Download as PPTX

**Input**: Design documents from `/specs/006-download-pptx/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The feature spec does not require automated tests, so this task list focuses on implementation and validation tasks. Manual browser verification is included where it is the only practical check.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Add the PPTX library script include and a new export button placeholder to `django_app/templates/sitesync/report.html`
- [X] T004 [P] Prepare the client-side export entrypoint and shared slide-building helpers in `django_app/static/sitesync/js/report.js`
- [X] T005 Define the 16:9 slide size and export guard conditions in `django_app/static/sitesync/js/report.js`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download a PPTX report from the report page (Priority: P1) 🎯 MVP

**Goal**: Add a Download as PPTX action beside Download as PDF and produce a downloadable PowerPoint file for the current report.

**Independent Test**: Open a report page, click Download as PPTX, and confirm a `.pptx` file downloads and opens in a PowerPoint-compatible editor.

### Implementation for User Story 1

- [X] T006 [US1] Add the Download as PPTX button beside the PDF button in `django_app/templates/sitesync/report.html`
- [X] T007 [US1] Implement the PPTX export function and click handler in `django_app/static/sitesync/js/report.js`
- [X] T008 [US1] Reuse the current report-section iteration, export lifecycle, and filename generation in `django_app/static/sitesync/js/report.js`
- [X] T009 [US1] Verify the PPTX export starts cleanly without changing the PDF export path in `django_app/static/sitesync/js/report.js`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Preserve editable comments and headers in the exported deck (Priority: P1)

**Goal**: Keep exported comment boxes and key text labels editable after download so the deck can be revised in PowerPoint.

**Independent Test**: Export a PPTX, open it in a PowerPoint-compatible editor, and edit a comment box and section header without recreating the file.

### Implementation for User Story 2

- [X] T010 [US2] Rebuild comment boxes as editable text objects during PPTX export in `django_app/static/sitesync/js/report.js`
- [X] T011 [US2] Rebuild section headers and key labels as editable text objects during PPTX export in `django_app/static/sitesync/js/report.js`
- [X] T012 [US2] Preserve the comment/reference warning treatment while exporting editable comment text in `django_app/static/sitesync/js/report.js`
- [X] T013 [US2] Validate that exported comment boxes and headers remain editable in PowerPoint-compatible software using the validation steps in `specs/006-download-pptx/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Adjust slide content after export (Priority: P2)

**Goal**: Allow exported slide elements to be moved or resized so the deck can be fine-tuned after download.

**Independent Test**: Export a PPTX, open it, and confirm the slide image, header text, and other elements can be repositioned or resized.

### Implementation for User Story 3

- [X] T014 [US3] Place report visuals and section images as independent slide objects that can be resized in `django_app/static/sitesync/js/report.js`
- [X] T015 [US3] Position header text and comment boxes as separate movable slide objects in `django_app/static/sitesync/js/report.js`
- [X] T016 [US3] Keep slide margins, logo placement, and content bounds adjustable within the 16:9 layout in `django_app/static/sitesync/js/report.js`

**Checkpoint**: At this point, User Stories 1, 2, and 3 should remain independently usable

---

## Phase 6: User Story 4 - Keep report visuals readable and correctly laid out (Priority: P2)

**Goal**: Preserve report fidelity in the exported deck so charts, tables, headings, and ordering match the source report page.

**Independent Test**: Export a report with charts, tables, and headings, then compare the slide deck to the source report page.

### Implementation for User Story 4

- [X] T017 [US4] Capture report visuals and tables as images that preserve the on-screen appearance in `django_app/static/sitesync/js/report.js`
- [X] T018 [US4] Keep the exported deck in landscape 16:9 format and one slide per report section in `django_app/static/sitesync/js/report.js`
- [X] T019 [US4] Preserve report ordering, headers, and section structure across the exported PPTX in `django_app/static/sitesync/js/report.js`
- [X] T020 [US4] Tune image scale and compression for acceptable file size and render time in `django_app/static/sitesync/js/report.js`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T021 Update `specs/006-download-pptx/quickstart.md` with the final validation flow and export assumptions
- [X] T022 Run a focused diagnostics pass on `django_app/templates/sitesync/report.html` and `django_app/static/sitesync/js/report.js` after the PPTX export changes
- [ ] T023 Perform manual end-to-end validation of PDF and PPTX export flows from the report page
- [X] T024 [US1] Add user-facing PPTX export failure messaging and recovery handling in `django_app/static/sitesync/js/report.js`
- [ ] T025 [US1] Verify the report page remains usable after a failed PPTX export in `django_app/static/sitesync/js/report.js`

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US3 but should be independently testable

### Within Each User Story

- Start with the export button and shared export scaffolding
- Build editable slide objects before tuning layout and fidelity
- Keep the PDF export path unchanged while adding PPTX behavior
- Story complete before moving to the next priority

### Parallel Opportunities

- Setup tasks marked [P] can run in parallel
- Foundational tasks marked [P] can run in parallel within Phase 2
- After foundational work, user stories can proceed in parallel if capacity allows
- Any task touching a different file from an in-progress task can be marked [P]

---

## Parallel Example: User Story 1

```bash
Task: "Add the Download as PPTX button beside the PDF button in django_app/templates/sitesync/report.html"
Task: "Implement the PPTX export function and click handler in django_app/static/sitesync/js/report.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify export behavior manually in a PowerPoint-compatible editor
- Commit after each task or logical group
- Stop at each checkpoint to validate story independently
- Avoid vague tasks, same file conflicts, and cross-story dependencies that break independence
