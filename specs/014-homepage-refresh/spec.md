# Feature Specification: Homepage Refresh

**Feature Branch**: `[014-homepage-refresh]`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: "I want to optimise Enerlytix's home page. I also want to improve its design. I want to begin with two sections, which are marked in red and blue in the image I uploaded. 1. Red box, currently only site filter is necessary from a user standpoint. The 'Refresh data' button could be moved to the 'Admin panel' dashboard. Similarly, the available site and supplies could be moved to the dashboard, too. 2. Blue box: This section is no longer necessary for regular users. It could be moved to the admin panel as a new separate page, which would also require to have a similar page layout and functionality as the home page has, except the 'Create Report' section. 3. Green box (second image): There should be a supply filter in this section. Another checkbox as 'Include Inactive Meters' would be also great. The default setting should be unticked, and the list beneath should exclude inactive supplies. Those changes would also create more space in the top section of the page, therefore the sites and supply lists could be taller. 4. Usage and Invoice Import: Those functions were added for diagnostic purposes in the beginning. They can still allow admins to download and review data from Etainabl. That's why there should be a page in the admin panel section. The downloaded data is currently displayed on a separate page (consumption-display). This page should also be updated accordingly. For instance, the current 'Back to Dashboard' button should lead to the new page in the admin panel section. Additionally, 'Export as CSV' and 'Export as Excel' buttons/functions would increase its usability."

## Clarifications

### Session 2026-08-05

- Q: When admins export CSV or Excel from the import review page, what should be exported? → A: The current filtered view only, matching what the admin is reviewing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Simplified Home Page (Priority: P1)

As a regular user, I want the home page to focus on finding and selecting sites so that the page is easier to understand and use.

**Why this priority**: The home page is the default entry point, so reducing clutter delivers immediate value to most users.

**Independent Test**: Open the home page as a non-admin user and verify that the main controls are limited to site discovery and site-specific viewing.

**Acceptance Scenarios**:

1. **Given** a regular user opens the home page, **When** the page loads, **Then** the page shows the site filter as the primary control and hides admin-oriented actions such as data refresh, usage import, and report creation.
2. **Given** a regular user views the home page, **When** the page renders on a standard desktop screen, **Then** the site and supply lists use more visible space than before the redesign.

---

### User Story 2 - Supply Filtering and Inactive Meter Toggle (Priority: P1)

As a regular user, I want to filter the supplies shown for a site and control whether inactive meters are included so that I can focus on the supplies that matter.

**Why this priority**: Supply selection is a core task on the home page, and the inactive-meter option directly affects what users review.

**Independent Test**: Select a site, use the supply filter, and toggle the inactive-meter option to confirm the visible supply list updates correctly.

**Acceptance Scenarios**:

1. **Given** a user has selected a site, **When** they enter a supply filter term, **Then** only supplies that match the filter remain visible.
2. **Given** the inactive-meter option is unticked by default, **When** the page loads or a new selection is made, **Then** inactive supplies are excluded from the list until the user explicitly includes them.
3. **Given** a user ticks the inactive-meter option, **When** the supply list refreshes, **Then** inactive supplies become visible alongside active supplies.

---

### User Story 3 - Admin Dashboard Controls (Priority: P2)

As an admin user, I want the administrative summary and refresh controls moved out of the public home page so that administrative actions live in the admin area.

**Why this priority**: These controls are useful, but only to admins, so separating them improves the default experience for regular users.

**Independent Test**: Open the admin area and verify that the moved summary and refresh actions are available there instead of on the home page.

**Acceptance Scenarios**:

1. **Given** an admin user opens the admin dashboard, **When** the page loads, **Then** the moved summary information and refresh action are available in the admin area.
2. **Given** a regular user opens the home page, **When** the page loads, **Then** they do not see the moved summary information or refresh action.

---

### User Story 4 - Admin Import Review Page (Priority: P2)

As an admin user, I want a dedicated page for usage and invoice import review so that I can inspect imported data and export it when needed.

**Why this priority**: Import review remains important for administrative diagnostics, but it should no longer crowd the public home page.

**Independent Test**: Open the admin review page, confirm the imported data is visible, export the data, and use back navigation to return to the admin dashboard.

**Acceptance Scenarios**:

1. **Given** an admin user opens the import review page, **When** the page loads, **Then** the imported usage and invoice data is shown in a layout consistent with the rest of the admin experience, without the report-creation section.
2. **Given** an admin user is reviewing imported data, **When** they choose to export it, **Then** they can export the current filtered view as CSV or as a spreadsheet format.
3. **Given** an admin user is on the import review page, **When** they use the back action, **Then** they return to the admin dashboard page rather than the public home page.

### Edge Cases

- No sites match the active site filter.
- No supplies match the supply filter for the selected site.
- The inactive-meter option is disabled and every matching supply is inactive, leaving the list empty.
- The imported usage or invoice dataset contains no rows, but the admin still needs a clear empty-state view and export controls.
- A user follows a legacy link to the old consumption-display page and should still arrive at the updated admin review experience.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The home page MUST present the site filter as the primary control for regular users.
- **FR-002**: The home page MUST hide administrative actions from regular users, including data refresh, usage import, and report creation.
- **FR-003**: The home page MUST give the site and supply lists more usable vertical space than the current layout.
- **FR-004**: The home page MUST allow users to filter the visible supplies for a selected site.
- **FR-005**: The home page MUST provide an "Include Inactive Meters" option for the supply list.
- **FR-006**: The "Include Inactive Meters" option MUST be unticked by default.
- **FR-007**: When the "Include Inactive Meters" option is unticked, the supply list MUST exclude inactive supplies.
- **FR-008**: When the "Include Inactive Meters" option is ticked, the supply list MUST include inactive supplies alongside active supplies.
- **FR-009**: The admin area MUST include the summary and refresh controls that are removed from the public home page.
- **FR-010**: The admin area MUST include a dedicated page for usage and invoice import review.
- **FR-011**: The dedicated import review page MUST present the imported data in a layout that is consistent with the admin experience and exclude the report-creation section.
- **FR-012**: The dedicated import review page MUST provide export options for CSV and spreadsheet formats for the current filtered view.
- **FR-013**: The import review page back action MUST return the user to the admin dashboard page.
- **FR-014**: Any existing route or entry point for consumption-display MUST lead users to the updated admin review experience.

### Key Entities *(include if feature involves data)*

- **Site**: A selectable location that can be filtered and inspected by users.
- **Supply**: A utility supply associated with a site, including whether it is active or inactive.
- **Imported Usage Data**: Administrative usage and invoice information loaded for review and export.
- **Admin Dashboard**: The administrative landing area that contains controls and summaries not needed by regular users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Regular users can identify the site filter as the primary home-page control in under 10 seconds during moderated testing.
- **SC-002**: On a standard desktop viewport, the redesigned home page shows more site and supply list content above the fold than the current layout.
- **SC-003**: The inactive-meter option defaults to off in 100% of fresh page loads and excluded supplies remain hidden until the user explicitly enables them.
- **SC-004**: Admin users can open the import review page, export the current filtered data in CSV or spreadsheet form, and return to the admin dashboard without needing an extra navigation step.
- **SC-005**: In usability testing, at least 90% of participants can complete the main home-page site-selection task without encountering admin-only actions.

## Assumptions

- The public home page is the default landing page for regular users after sign-in.
- The admin area already exists as a separate authenticated section of the product.
- Inactive supplies can be identified from existing supply or meter status information.
- The supply filter is expected to search within the currently selected site's supplies using the labels already visible to users.
- The export formats are expected to reflect the data currently shown on the import review page.