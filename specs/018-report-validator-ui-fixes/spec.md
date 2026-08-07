# Feature Specification: Report Validator UI Fixes

**Feature Branch**: `[018-report-validator-ui-fixes]`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "I want to implement some improvements and bug fixes. I listed them below:
1. Remove the first comment and validation boxes from the first page, and adjust the second comment and validation boxes' width as they are in other pages.
2. Validators should open reports read-only. They shouldn't be allowed to save the report as draft or final. They should only be allowed to tick validation boxes and enter comments into the validation text boxes. And, they should be saved automatically.
3. Checkboxes on the first column of the list to select reports are missing on the saved reports page in production environment, even though they are properly displayed and functioning in development and test environment. That also causes misaligned columns. The template and related details should be checked and fixed."

## Clarifications

### Session 2026-08-07

- Q: How should validator validation-note autosave behave? -> A: Autosave on field blur with 300 ms debounce.
- Q: What should happen for users who are both validator and editor/admin on the same report? -> A: Enforce validator-only actions when assigned as validator for that report.
- Q: Which roles should see row-selection checkboxes on Saved Reports? -> A: Admin-authorized users only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Saved Reports Selection Layout (Priority: P1)

As an admin user, I need the Saved Reports selection checkboxes to appear consistently so I can select reports for bulk actions and view correctly aligned table columns.

**Why this priority**: Missing checkboxes directly blocks bulk operations and causes incorrect table interpretation, which affects day-to-day administrative work.

**Independent Test**: Can be fully tested by opening Saved Reports in production-like conditions as an admin, confirming checkbox visibility for each row, and verifying every data cell appears under its correct header.

**Acceptance Scenarios**:

1. **Given** an admin user opens Saved Reports, **When** report rows are rendered, **Then** each row includes a selectable checkbox in the selection column.
2. **Given** an admin user views Saved Reports, **When** the list loads, **Then** each row’s values align with the correct table headers without shifted columns.
3. **Given** an admin user selects one or more report rows, **When** a bulk action is initiated, **Then** the selected report IDs are correctly captured from the visible checkbox controls.
4. **Given** a non-admin user opens Saved Reports, **When** report rows are rendered, **Then** row-selection checkboxes and bulk-selection controls are not shown.

---

### User Story 2 - Restrict Validator Editing Rights (Priority: P1)

As a validator, I need a review-focused, read-only report experience for report content so that I can validate pages without making business-content edits or changing report publication state.

**Why this priority**: This enforces separation of duties and protects report integrity during validation workflow.

**Independent Test**: Can be fully tested by opening a report as an assigned validator and confirming that content-editing and draft/final save actions are unavailable, while validation checkboxes and validation note fields remain usable.

**Acceptance Scenarios**:

1. **Given** a user is assigned as validator for a report, **When** the user opens the report, **Then** report content inputs are read-only.
2. **Given** a validator is viewing a report, **When** they attempt to save as draft or finalize the report, **Then** those actions are not available and no report content save occurs.
3. **Given** a validator is viewing a report, **When** they tick or untick page validation and enter validation notes, **Then** those validation interactions are allowed and persisted.
4. **Given** a validator edits a validation note, **When** the note field loses focus, **Then** the note is automatically saved after a 300 ms debounce without requiring explicit save actions.
5. **Given** a user has editor/admin privileges and is also assigned validator for the report, **When** they open that report in validation workflow context, **Then** only validator-allowed actions are enabled and content-edit/save actions remain blocked.

---

### User Story 3 - Clean First Overview Validation Block Layout (Priority: P2)

As a report reviewer, I need the first report page to show only the intended validation/comment area with consistent sizing, so the page layout matches the rest of the report and avoids duplicate/confusing controls.

**Why this priority**: Duplicate comment & validation boxes create confusion and reduce trust in the review flow.

**Independent Test**: Can be fully tested by opening a report and verifying the first page overview section has no duplicate top validation/comment box and that the remaining validation/comment box width matches the standard layout used on other pages.

**Acceptance Scenarios**:

1. **Given** a report is opened on the first overview page, **When** the validation/comment sections render, **Then** the duplicate first validation/comment box is not shown.
2. **Given** the remaining validation/comment box is shown on the first overview page, **When** compared to other pages, **Then** it uses the same visual width and layout behavior.
3. **Given** a validator interacts with the remaining first-page validation/comment box, **When** they add notes or toggle validation, **Then** behavior matches equivalent controls on other pages.

---

### Edge Cases

- A report contains legacy first-page validation/comment data that was previously attached to the removed duplicate box; the system still retains historical data without displaying duplicate controls.
- A user has multiple roles (for example, admin and validator); if assigned validator for the report, validator-only restrictions take precedence for that report session.
- Saved Reports loads with zero rows, one row, or many rows; header and body alignment remains correct in all cases.
- A stale browser cache exists after deployment; the page still resolves to the latest rendered structure and does not reintroduce missing checkbox/misaligned-column behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render exactly one validation/comment interaction block for the first overview section, removing the duplicate first block currently shown above the intended block.
- **FR-002**: System MUST ensure the remaining first-page validation/comment block uses the same effective width and horizontal alignment behavior as equivalent validation/comment blocks on other report pages.
- **FR-003**: System MUST present report business-content fields as read-only to users acting in validator role while they are in validation workflow context.
- **FR-004**: System MUST prevent validator-role users from executing report save-as-draft and save-as-final actions.
- **FR-005**: System MUST continue allowing validator-role users to mark page validation state and submit validation-note comments.
- **FR-005a**: System MUST automatically persist validator validation-note text when the note field loses focus, using a 300 ms debounce to avoid redundant write operations.
- **FR-005b**: System MUST apply validator-only interaction restrictions for a report whenever the current user is assigned as that report's validator, including users who also hold editor or admin roles.
- **FR-006**: System MUST display row-selection checkboxes on Saved Reports only for admin-authorized users.
- **FR-007**: System MUST keep Saved Reports table headers and row cells structurally aligned so each value appears under the correct header in production and non-production environments.
- **FR-008**: System MUST preserve existing Saved Reports filtering and bulk-selection behavior after checkbox visibility/layout corrections.
- **FR-009**: System MUST ensure production-rendered assets and templates for Saved Reports and report validation UI are consistent with the intended latest behavior after deployment.

### Key Entities *(include if feature involves data)*

- **Report Review Session**: The user-facing report view context containing report content, page-level validation state, and validation comments.
- **Validator Permission Context**: Effective interaction rights for a user assigned to validate a report, including allowed validation actions and blocked report-content save actions.
- **Saved Reports Row Selection State**: Per-row selectable state used for bulk operations, including selected report identifiers and count.
- **Page Validation Comment Block**: The per-page interaction area for validation checkbox and validation notes, including placement and display characteristics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In production verification, 100% of sampled Saved Reports rows display a visible selection checkbox for admin-authorized users and show no header/data-column shift.
- **SC-002**: In role-based acceptance testing, 100% of validator sessions are unable to perform draft/final save actions while retaining ability to update page validation state and validation notes.
- **SC-002a**: In validator acceptance testing, validation notes are automatically saved on field blur with a 300 ms debounce and no explicit save action required in at least 95% of sampled interactions.
- **SC-003**: On the first overview page, duplicate validation/comment block occurrence rate is 0% across tested reports.
- **SC-004**: Reviewers confirm the first-page remaining validation/comment block visually matches standard page-width behavior used on at least three other report pages.
- **SC-005**: Post-release, no new high-priority incidents are raised for these three behaviors during the first 14 days of production use.

## Assumptions

- Existing role assignments already distinguish report owners/editors from assigned validators.
- Validator users may still need to access validation controls and validation note text areas while report business-content fields remain non-editable.
- Bulk selection on Saved Reports remains an admin-only workflow and does not expand permissions to unauthorized users.
- The issue observed only in production is caused by environment-specific rendering or asset consistency differences rather than intentional behavior differences.
- This scope focuses on report view and saved-reports behavior; no new user roles or approval-process redesign is included.
