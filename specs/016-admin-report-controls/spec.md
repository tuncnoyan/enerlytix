# Feature Specification: Saved Reports Admin Controls

**Feature Branch**: `[016-admin-report-controls]`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "I want to add two features to the saved reports page: (1) reports can be deleted only by admins using left-side checkboxes for multi-select, with password re-entry confirmation and audit logging; (2) reports should be sortable by each column using a dropdown field selector."

## Clarifications

### Session 2026-08-06

- Q: For delete authorization, which role should be treated as "admin" for this feature? -> A: Only platform admins can bulk-delete saved reports.
- Q: For dropdown sorting, what default sort direction should apply when a field is selected? -> A: Field-based default (dates newest-first, text A-Z, numbers high-low).
- Q: If some selected reports cannot be deleted (for example already removed in parallel), how should bulk delete behave? -> A: All-or-nothing: delete none, show which items blocked the request.
- Q: For audit logging scope, should unauthorized non-admin delete attempts (for example direct POST/API calls) also be logged? -> A: Yes, log all unauthorized attempts with actor and target references.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Platform Admin Bulk Report Deletion with Verification (Priority: P1)

As a platform admin user, I want to select multiple saved reports and delete them only after re-entering my password so that high-impact deletions are deliberate and secure.

**Why this priority**: This introduces destructive data control and must be protected and role-restricted before broader list usability enhancements.

**Independent Test**: Sign in as a platform admin, select multiple reports via left-side checkboxes, confirm deletion with the correct password, and verify only selected reports are removed.

**Acceptance Scenarios**:

1. **Given** a platform admin user is on the saved reports page, **When** they view the report table, **Then** each row includes a left-side selection checkbox for multi-report selection.
2. **Given** a platform admin user selected one or more reports, **When** they submit a delete action and re-enter the correct password, **Then** all selected reports are deleted in one operation.
3. **Given** a non-admin user is on the saved reports page, **When** they view available controls, **Then** they cannot access row-selection delete controls or execute report deletion.
4. **Given** a platform admin user starts deletion with an incorrect password, **When** confirmation is submitted, **Then** no selected reports are deleted and a clear failure message is shown.
5. **Given** a platform admin user successfully or unsuccessfully attempts deletion, **When** the operation completes, **Then** the action outcome and relevant report references are recorded in the audit log.
6. **Given** a platform admin user selected multiple reports and at least one selected report is no longer deletable, **When** deletion is submitted, **Then** no selected reports are deleted and the response identifies which report references blocked the request.
7. **Given** a non-admin user attempts deletion through a direct request, **When** authorization is evaluated, **Then** deletion is denied and the unauthorized attempt is recorded in the audit log with actor and target references.

---

### User Story 2 - Sort Saved Reports by Dropdown Field Selection (Priority: P2)

As a reports user, I want to sort the saved reports list by choosing a field name from a dropdown so that I can quickly reorder records by the information I care about.

**Why this priority**: Sorting improves list usability and navigation, but is lower risk than secure deletion controls.

**Independent Test**: Choose each available field from the sort dropdown and verify the full list order updates according to the selected field.

**Acceptance Scenarios**:

1. **Given** a user is on the saved reports page, **When** they open the sort dropdown, **Then** the dropdown lists all sortable report columns shown in the table.
2. **Given** a user chooses a field from the sort dropdown, **When** sorting is applied, **Then** the report list is reordered by the selected field.
3. **Given** filters are active on the saved reports page, **When** a sort field is selected, **Then** sorting is applied to the filtered result set without clearing active filters.
4. **Given** a user selects a date, text, or numeric sort field, **When** sorting is applied, **Then** the default direction is date newest-first, text A-Z, and numeric high-low.

---

### User Story 3 - Safe and Transparent Bulk-Delete UX (Priority: P3)

As a platform admin user, I want clear selection feedback and confirmation behavior during bulk deletion so that I can avoid accidental report loss.

**Why this priority**: Clear UX safeguards reduce operational error and support accountable administrative workflows.

**Independent Test**: Attempt deletion with no selected rows, then with selected rows, and confirm the page consistently communicates what will be deleted.

**Acceptance Scenarios**:

1. **Given** a platform admin user has not selected any reports, **When** they try to start deletion, **Then** the page prevents execution and shows a clear "no reports selected" message.
2. **Given** a platform admin user selected multiple reports, **When** the deletion confirmation appears, **Then** the interface clearly indicates how many reports will be removed.

### Edge Cases

- Platform admin selects reports, then table state changes before confirmation (for example, sorting or filter changes).
- Platform admin tries to delete reports where at least one is no longer deletable; the operation fails atomically and returns blocking report references.
- Password confirmation input is blank.
- Mixed report ownership/team visibility exists; platform admin deletion remains role-authorized while non-admins remain blocked.
- Sorting is requested for columns containing blank or fallback values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The saved reports table MUST display a left-side selection checkbox for each report row for platform admin users.
- **FR-002**: The system MUST allow platform admin users to select multiple reports and submit a single bulk-delete operation.
- **FR-003**: The system MUST require platform admin users to re-enter their password before executing report deletion.
- **FR-004**: The system MUST deny report deletion for all users who are not platform admins.
- **FR-004a**: For this feature, platform admin MUST map to authenticated users where `is_staff` is true or `is_superuser` is true.
- **FR-005**: If password confirmation fails, the system MUST not delete any selected reports and MUST return a clear error message.
- **FR-006**: If no report is selected, the system MUST block deletion and display a clear "no reports selected" message.
- **FR-007**: Every delete attempt (authorized or unauthorized, success or failure) MUST be written to the audit log with actor identity, action outcome, and target report references.
- **FR-007a**: Bulk deletion MUST be atomic; if any selected report cannot be deleted, no selected reports are deleted in that request.
- **FR-007b**: When a bulk deletion fails because one or more selected reports are not deletable, the system MUST return the blocking report references in the failure message.
- **FR-008**: The saved reports page MUST provide a sort-field dropdown that includes all sortable table columns.
- **FR-009**: When a sort field is selected, the saved reports list MUST reorder by that field.
- **FR-010**: Active filters and search criteria MUST remain applied when sorting changes.
- **FR-011**: Sorting and deletion controls MUST preserve existing report visibility and access scoping rules.
- **FR-012**: Default sort direction MUST be field-based: date fields newest-first, text fields ascending alphabetical (A-Z), and numeric fields descending (high-low).

### Key Entities *(include if feature involves data)*

- **Saved Report Row**: A report entry in the saved reports table including sortable display attributes and selection state.
- **Bulk Delete Request**: The platform admin action payload containing selected report identifiers and password confirmation.
- **Delete Audit Entry**: The audit-log record capturing which platform admin attempted deletion, what reports were targeted, and whether the operation succeeded or failed.
- **Sort Selection State**: The currently selected sort field used to order the report list.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of non-admin deletion attempts are blocked and no reports are removed.
- **SC-002**: In acceptance testing, 100% of successful platform admin bulk deletions require password re-entry and remove exactly the selected reports.
- **SC-003**: In acceptance testing, 100% of deletion attempts (success and failure) produce corresponding audit-log entries with actor, outcome, and targeted report references.
- **SC-004**: Users can reorder saved reports by any available dropdown sort field in under 10 seconds during moderated usability checks.
- **SC-005**: In combined search/filter/sort scenarios, 100% of test runs preserve the active filtered result set while applying sort order.
- **SC-006**: In authorization tests, 100% of unauthorized non-admin delete requests are denied and logged with actor and targeted report references.

## Assumptions

- Existing platform admin determination is the runtime boundary where `is_staff` is true or `is_superuser` is true, and this boundary is reused for bulk-delete authorization.
- Deleting a report from this page means permanent removal from the saved reports list, not archive-only behavior.
- Sort direction is fixed to field-based defaults for this feature and user-selectable direction controls are out of scope.
- Audit logging infrastructure already exists and can store both successful and failed admin deletion attempts.

## Implementation Outcome (Release Evidence)

- Implementation date: 2026-08-06
- Scope delivered: platform-admin-only bulk delete controls, password re-confirmation, atomic all-or-nothing delete handling, denied-attempt audit logging, and dropdown-based saved-report sorting with field-based default directions.
- Targeted Docker validation: 32 tests passed for saved-reports and audit scenarios.
- Full Docker regression validation: 234 tests passed (final status: OK).
- SC-004 usability/timing validation: 5 timed runs of dropdown sorting completed in 0.2952s, 0.1073s, 0.1137s, 0.1088s, and 0.1046s; all runs were <= 10s.
- Evidence details and exact commands/results are recorded in quickstart.md and aligned contract behavior is recorded in contracts/saved-reports-admin-controls.md.
