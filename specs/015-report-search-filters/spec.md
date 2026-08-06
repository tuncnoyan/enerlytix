# Feature Specification: Saved Reports Search and Filters

**Feature Branch**: `[015-report-search-filters]`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "I want to add search and filter features to the saved reports page. Site and User search boxes should be added, and reporting month, report status, and validation status filters should be available with all status options selected by default."

## Clarifications

### Session 2026-08-06

- Q: How should the reporting month date range boundaries be interpreted? -> A: Inclusive on both ends (Start Month <= report month <= End Month).
- Q: What should happen if all report-status or validation-status checkboxes are unticked? -> A: Allow it and show zero results with a clear empty-state message.
- Q: What matching rule should Site and User search use? -> A: Case-insensitive partial match (contains).
- Q: Should Reporting month filters use day-level dates or month-only values? -> A: Month-year precision only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find Reports by Site and User (Priority: P1)

As a report user, I want to search saved reports by site name and by user name so that I can quickly find relevant reports without scanning long tables.

**Why this priority**: Users first need direct search to locate reports quickly; this is the most immediate productivity gain on the page.

**Independent Test**: Enter a site name and a username on the saved reports page and confirm that only matching reports remain visible.

**Acceptance Scenarios**:

1. **Given** the saved reports page contains reports from multiple sites, **When** the user enters text in the Site search box, **Then** only reports whose site names case-insensitively contain the search term are shown.
2. **Given** reports have OWNER, LAST EDITED BY, and VALIDATOR values, **When** the user enters a username in the User search box, **Then** reports are shown only when at least one of those three column values case-insensitively contains the entered username.
3. **Given** both Site and User searches are populated, **When** the result list updates, **Then** only reports matching both search criteria are shown.

---

### User Story 2 - Narrow by Month and Statuses (Priority: P1)

As a report user, I want to filter reports by reporting month range, report status, and validation status so that I can reduce the list to the exact records I need.

**Why this priority**: Filtering is essential for reducing high-volume report lists and supports common review workflows.

**Independent Test**: Apply a reporting month range and change status checkboxes; verify that the list reflects only reports that meet all active filter selections.

**Acceptance Scenarios**:

1. **Given** the page is opened for the first time, **When** the filters load, **Then** both Report Status options (Draft and Final) and all Validation Status options (Draft, Awaiting validation, Validated) are selected by default.
2. **Given** a Start Month and End Month are selected for Reporting month, **When** the list refreshes, **Then** only reports with reporting months from Start Month through End Month (inclusive) are shown.
3. **Given** a user unticks one or more status checkboxes, **When** filters are applied, **Then** reports with unticked statuses are excluded from the list.
4. **Given** a user unticks all options in Report Status or Validation Status, **When** filters are applied, **Then** the list shows zero matching reports and a clear empty-state message.

---

### User Story 3 - Maintain Clear Results Under Combined Filters (Priority: P2)

As a report user, I want predictable behavior when filters are combined or too restrictive so that I can adjust criteria confidently.

**Why this priority**: Combined filtering improves trust and usability by ensuring users understand why records appear or disappear.

**Independent Test**: Apply multiple restrictive criteria and verify that the page shows an explicit empty-state result when no records match.

**Acceptance Scenarios**:

1. **Given** filters are set to a combination with no matching reports, **When** the results update, **Then** the page shows a clear empty-state message instead of stale or unrelated rows.
2. **Given** one filter is cleared while others remain active, **When** the results update, **Then** the list recalculates using only the remaining active criteria.

### Edge Cases

- Site and User search terms include partial matches, different letter casing, or extra whitespace.
- A username appears in more than one of OWNER, LAST EDITED BY, and VALIDATOR for the same report.
- Start Month is set later than End Month.
- Users untick all options in Report Status or all options in Validation Status.
- Filters return zero results for a valid criteria set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The saved reports page MUST provide a Site search input for matching reports by site name.
- **FR-002**: The saved reports page MUST provide one User search input that searches across OWNER, LAST EDITED BY, and VALIDATOR values.
- **FR-003**: A report MUST be included in User search results only when at least one of OWNER, LAST EDITED BY, or VALIDATOR case-insensitively contains the entered username.
- **FR-003a**: Site search MUST use case-insensitive partial matching (contains).
- **FR-004**: The saved reports page MUST provide Reporting month range filters with Start Month and End Month inputs (month-year precision only).
- **FR-005**: The saved reports page MUST provide a Report Status filter with Draft and Final checkbox options.
- **FR-006**: The Report Status filter MUST default to both options selected when the page initially loads.
- **FR-007**: The saved reports page MUST provide a Validation Status filter with Draft, Awaiting validation, and Validated checkbox options.
- **FR-008**: The Validation Status filter MUST default to all three options selected when the page initially loads.
- **FR-009**: The results list MUST apply Site search, User search, Reporting month range, Report Status, and Validation Status together as combined criteria.
- **FR-010**: When Start Month and End Month are both provided, the results list MUST include only reports where Start Month <= reporting month <= End Month (both boundaries inclusive).
- **FR-011**: When no reports match active search or filter criteria, the page MUST show an explicit empty-state result.
- **FR-012**: The page MUST allow users to clear or adjust individual criteria and immediately receive recalculated results.
- **FR-013**: If Start Month is after End Month, the page MUST enforce deterministic correction behavior: HTML mode shows inline validation with no rows; JSON mode returns HTTP 400 with a structured `invalid_month_range` error.
- **FR-014**: The page MUST allow all status options in either status group to be unticked, and in that state MUST show zero matching reports with a clear empty-state message.

### Key Entities *(include if feature involves data)*

- **Saved Report**: A report record shown in the saved reports list, including site, reporting month, report status, and validation status fields.
- **Report User Attribution**: The set of user-name fields tied to a report (OWNER, LAST EDITED BY, VALIDATOR) used for cross-column user search.
- **Filter Criteria Set**: The active combination of Site text, User text, date range, report status selections, and validation status selections that determines visible results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a usability check, at least 90% of users can find a known report by site or user within 30 seconds.
- **SC-002**: Applying any single search or filter criterion updates the visible report list in under 2 seconds for typical daily usage volumes.
- **SC-003**: In acceptance testing, 100% of first page loads show both report status options and all validation status options selected by default.
- **SC-004**: In test runs covering combined criteria, returned results match the active criteria set with 100% accuracy across site, user, month range, report status, and validation status.
- **SC-005**: For scenarios with no matching records, 100% of tests show a clear empty-state message and no unrelated report rows.

## Assumptions

- The saved reports page already shows report rows with site name, reporting month, report status, validation status, and user attribution columns.
- Users applying these searches and filters are already authenticated and authorized to view the reports currently listed on the page.
- Reporting month values are available in a format that supports month-year range filtering using Start Month and End Month inputs.
- Search and filter behavior applies to the current saved reports dataset displayed to the user and does not expand user access scope.
