# Feature Specification: Monthly Report Draft and Final Workflow

**Feature Branch**: `004-report-draft-workflow`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Add a report workflow where monthly reports can be saved as drafts using the site name and reporting date, only one report can exist per site for a specific month, reports can later be saved as final versions, final reports can be edited after a warning, previous month's final comments are carried into the next month's report with reference warnings, and users can browse saved reports on a new page."

## Clarifications

### Session 2026-07-16

- Q: When a final report is edited after the warning, should the original final stay immutable or be edited in place? → A: Option C — keep the original final report immutable and create a separate replacement final version for the same site and month.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save a Monthly Draft Report (Priority: P1)

An energy manager creates a report for a specific site and reporting month. They can save the report as a draft that is identified by the site name and reporting date, then return to the same report later to continue editing.

**Why this priority**: Draft saving is the foundation of the workflow. Without a reliable monthly draft, the rest of the report lifecycle cannot function.

**Independent Test**: Can be tested by creating a report for one site and month, saving it as a draft, and reopening the same site/month to confirm the same report is loaded instead of a new one being created.

**Acceptance Scenarios**:

1. **Given** a site and reporting month with no existing report, **When** the user saves the report as a draft, **Then** the report is stored as a draft identified by that site and month.
2. **Given** a draft already exists for the same site and month, **When** the user returns to that month, **Then** the existing draft is reopened rather than creating a duplicate report.
3. **Given** a report already exists for a site and month, **When** the user attempts to create another report for the same site and month, **Then** the system prevents a second report from being created.

---

### User Story 2 - Finalise and Revise a Report (Priority: P2)

An energy manager finishes editing a report and saves it as a final version. If they later need to adjust a final report, the system warns them that the report has already been finalised and shared before allowing edits to continue.

**Why this priority**: Final reports are the client-facing deliverable. The workflow must clearly distinguish the final version while still allowing controlled corrections when needed.

**Independent Test**: Can be tested by saving a report as final, reopening it, confirming the warning appears, and then saving the edited report as a new final version.

**Acceptance Scenarios**:

1. **Given** a draft report is complete, **When** the user saves it as final, **Then** the report is marked as final and becomes the version used for client delivery.
2. **Given** a report is marked as final, **When** the user chooses to edit it, **Then** the system shows a clear warning that the report was already finalised and shared.
3. **Given** the user confirms they want to edit a final report, **When** they save their changes, **Then** the system creates a separate replacement final version for that site and month while preserving the original final report.

---

### User Story 3 - Carry Comments Forward to the Next Month (Priority: P3)

When a new month starts, the energy manager opens the next report for the same site. The report begins with comments copied from the previous month's final report so that useful context is retained, while each copied comment clearly shows it is only a reference from the previous month.

**Why this priority**: Carrying forward prior comments saves time and keeps reporting consistent from month to month.

**Independent Test**: Can be tested by finalising a report for one month, starting a new month for the same site, and verifying the previous month's comments appear in the new report with reference warnings.

**Acceptance Scenarios**:

1. **Given** a previous month has a final report with comments, **When** a report is created for the next month on the same site, **Then** the new report starts with those comments already filled in.
2. **Given** a carried-forward comment appears in a new month's report, **When** the user views the comment box, **Then** the comment is visibly labelled as coming from the previous month and for reference only.
3. **Given** the previous month does not have a final report, **When** the new month's report is created, **Then** the comment boxes start empty.

---

### User Story 4 - Browse Saved Reports (Priority: P4)

An energy manager opens a saved reports page to review past drafts and final reports. They can scan the list by site and reporting month, see which reports are drafts or finals, and open the report they need.

**Why this priority**: A browsing page gives users a reliable way to revisit completed work and resume unfinished reports without relying on memory or manual tracking.

**Independent Test**: Can be tested by opening the saved reports page and confirming that reports are listed with their site, month, and status, then opening a selected report from the list.

**Acceptance Scenarios**:

1. **Given** there are saved reports for multiple sites and months, **When** the user opens the saved reports page, **Then** the reports are listed with their site, reporting month, and status.
2. **Given** a user is looking for a specific report, **When** they browse the saved reports page, **Then** they can locate the report by site and month and open it.
3. **Given** both drafts and final reports exist, **When** the user scans the list, **Then** the report status is visible so they can distinguish unfinished work from client-ready work.

---

### Edge Cases

- What happens when a user tries to create a report for a site and month that already has a draft or final report? The existing report must be reopened and no duplicate must be created.
- What happens when a new month is started but the previous month only has a draft report? No comments are carried forward because there is no final report to reference.
- What happens when the previous month has fewer comments than the current report layout? Only matching comments are carried forward and the remaining comment boxes stay blank.
- What happens when a final report is edited after a PDF has already been produced for the client? The latest saved final version becomes the current client-facing copy for that site and month.
- What happens when the saved reports page contains many entries? Reports remain browsable by site and month so users can still find the correct report without ambiguity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a report to be saved as a draft for a specific site and reporting month, using the site name and reporting date as the report identity shown to users.
- **FR-002**: The system MUST enforce a one-report-per-site-per-month rule so that a site can have only one report for any given calendar month.
- **FR-003**: If a user opens a site and month that already has a report, the system MUST reopen the existing report instead of creating a new one.
- **FR-004**: The system MUST allow a report to be saved as a final version when the editing process is complete.
- **FR-005**: Final reports MUST be clearly identified as final and treated as the client-facing version for that site and month.
- **FR-006**: If a user attempts to edit a final report, the system MUST present a warning before allowing changes to continue.
- **FR-007**: After the warning is accepted, the user MUST be able to edit the final report and save the changes as a separate replacement final version for that site and month while preserving the original final report.
- **FR-008**: When a new report is created for a month and the prior month has a final report for the same site, the system MUST carry forward the previous month’s comments into the new report.
- **FR-009**: Each carried-forward comment MUST visibly indicate that it comes from the previous month and is intended only as a reference.
- **FR-010**: If there is no final report for the previous month, the new report MUST start with blank comments.
- **FR-011**: The system MUST provide a saved reports page that lists stored reports by site, reporting month, and status.
- **FR-012**: The saved reports page MUST allow users to open a selected report from the list.
- **FR-013**: Final reports MUST remain available for future review on the saved reports page alongside draft reports.
- **FR-014**: The report workflow MUST preserve the latest saved final version as the report used for client delivery while retaining the original final report as an immutable historical version.

### Key Entities *(include if feature involves data)*

- **Report**: A monthly report for one site, identified by site and reporting month, with a status of draft or final and a current saved version for editing or delivery.
- **Report Version**: A saved draft, final, or replacement final snapshot for a monthly report, where the original final version remains immutable and later corrections are stored as replacement final versions.
- **Report Comment**: A text entry attached to a report section or comment box, including whether it was copied forward from the previous month.
- **Saved Report Entry**: The summary information shown on the saved reports page, including the site, reporting month, and report status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can save a report draft for a site and month and reopen the same report later without creating a duplicate record in 100% of tested cases.
- **SC-002**: Every site and calendar month resolves to exactly one saved report, regardless of whether the report was first saved as a draft or as a final version.
- **SC-003**: Users can finalise a report, reopen it after a warning, and save the revised report as the latest final version in under 3 minutes.
- **SC-004**: When a previous month has a final report, all carried-forward comments appear in the next month’s report with the reference warning visible before the user edits them.
- **SC-005**: Users can find and open a saved report from the browsing page in three clicks or fewer.

## Assumptions

- The reporting month is treated as a calendar month and the reporting date shown to users refers to that month.
- Draft and final are states within one monthly report identity, while post-warning edits to a final report create a separate replacement final version rather than overwriting the original final.
- The latest saved final version is the one shown to users for that site and month after any edits are accepted, but the original final remains available as an immutable historical version.
- Carried-forward comments come from the immediately previous month’s final report for the same site.
- If a previous month final report contains no comments for a section, that section remains blank in the new report.
- Existing site data, report content, and user access controls continue to work as they do today; this feature adds workflow, carry-forward, and browsing behavior.
