# Feature Specification: Capacity Upload Results UX

**Feature Branch**: `[017-capacity-upload-results]`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "Each time the Available Capacity Upload process creates a useless error list. Also, that list could be multi-pages long and make the function unusable. I want to improve it. The issues list should be removed. Only the sections I marked with green rectangles should remain. There should also be a button to download the upload results in Excel format, which should include both successes and failures with explanations."

## Clarifications

### Session 2026-08-06

- Q: Which upload run should the Excel download export? -> A: Export results for the latest completed upload shown in the settings page.
- Q: What workbook structure should the upload results Excel file use? -> A: Use two sheets: Successes and Failures.
- Q: How should multiple validation failures for one row be represented? -> A: One failed row with all failure reasons combined in a single explanation field.
- Q: Which columns must be included in each exported result row? -> A: Row number, original upload columns, outcome, and explanation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Streamlined Upload Outcome View (Priority: P1)

As an admin user, I want the upload outcome area to show only concise summary sections so that the settings page remains usable after large uploads.

**Why this priority**: The current long inline issue list can make the page difficult to use and blocks core workflow completion.

**Independent Test**: Complete an upload that produces many issues and verify the page keeps only summary/status sections without rendering a long inline issue list.

**Acceptance Scenarios**:

1. **Given** an upload finishes with mixed results, **When** the page renders the outcome area, **Then** the per-row inline issue list is not displayed.
2. **Given** an upload finishes, **When** the page renders the outcome area, **Then** summary sections remain visible, including overall result message and upload status details.
3. **Given** a very large upload result set, **When** outcome content is shown, **Then** page length remains stable and does not expand with row-by-row issue text.

---

### User Story 2 - Downloadable Full Results (Priority: P1)

As an admin user, I want a download button for upload results so that I can review all successful and failed rows outside the page.

**Why this priority**: Removing inline issue details requires an equivalent way to inspect full outcomes without losing auditability.

**Independent Test**: Complete an upload and click the results download button; confirm the downloaded Excel file includes both success and failure rows with explanations.

**Acceptance Scenarios**:

1. **Given** an upload has completed, **When** the user chooses to download results, **Then** an Excel file is generated and downloaded.
2. **Given** an upload contains successful and failed rows, **When** the results file is opened, **Then** both success and failure entries are present.
3. **Given** a failed row exists, **When** its result is reviewed in the downloaded file, **Then** the failure explanation is included.

---

### User Story 3 - Actionable Result Records for Follow-up (Priority: P2)

As an admin user, I want each downloaded result row to be self-explanatory so that I can quickly correct source data and retry only what failed.

**Why this priority**: Better post-upload remediation reduces repeated failed imports and support effort.

**Independent Test**: Use the downloaded file to identify at least one failed row and determine why it failed without needing the inline page list.

**Acceptance Scenarios**:

1. **Given** a downloaded results file, **When** a user reviews a row entry, **Then** the row outcome is clearly labeled as success or failure.
2. **Given** a failed row in the downloaded file, **When** a user reviews it, **Then** the explanation is specific enough to guide correction of the source upload file.

### Edge Cases

- Upload completes with zero failures; the results download still works and clearly marks all rows as success.
- Upload completes with zero successes; the results download still works and clearly marks all rows as failure.
- Upload result explanations are long or contain special characters; exported explanations remain readable.
- A user opens the download action for an upload that has no stored row outcomes; the user receives clear feedback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The available capacity upload outcome area MUST remove the inline per-row issues list from the settings page.
- **FR-002**: The upload outcome area MUST keep concise summary sections visible, including overall completion status and aggregate counts.
- **FR-003**: The system MUST provide a visible download action for upload results after an upload completes.
- **FR-003a**: The download action MUST export the latest completed upload run currently shown in the Available Capacity Upload section.
- **FR-004**: The results download MUST be in Excel format.
- **FR-004a**: The Excel file MUST contain exactly two worksheets named "Successes" and "Failures".
- **FR-005**: The downloaded results file MUST include both successful and failed row outcomes for the upload.
- **FR-006**: Each downloaded result row MUST include an outcome label indicating success or failure.
- **FR-007**: Each failed downloaded row MUST include an explanation of why that row failed.
- **FR-007a**: If a failed row has multiple validation failures, the export MUST include all reasons combined in that row's explanation field.
- **FR-007b**: Each exported result row MUST include the source row number and all original upload columns.
- **FR-007c**: Each exported result row MUST include both an outcome field and an explanation field.
- **FR-008**: The system MUST preserve current access control so only authorized users can view and download upload results.
- **FR-009**: If full row results are unavailable for a completed upload, the system MUST return a clear user-facing message.

### Key Entities *(include if feature involves data)*

- **Capacity Upload Run Summary**: High-level outcome for an upload run, including completion message, accepted count, rejected count, and last-upload status context.
- **Capacity Upload Result Row**: A single processed row outcome with row identifier, source values, outcome state, and explanation.
- **Upload Results Export**: Downloadable spreadsheet representation of the full upload run outcomes for offline review and correction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability checks with large failed uploads, 100% of sessions keep the settings page readable without multi-page inline issue lists.
- **SC-002**: In acceptance testing, 100% of completed uploads provide a working results download action.
- **SC-003**: In validation samples, 100% of downloaded files include both success and failure outcomes when both are present in the upload run.
- **SC-004**: In validation samples, 100% of failed rows in downloads include a human-readable explanation.
- **SC-005**: In task-based testing, users can identify and explain at least one failed row cause from the downloaded file within 2 minutes.

## Assumptions

- The existing available capacity upload workflow and run tracking remain in place and are reused.
- Authorized users who currently access capacity upload settings are the same users allowed to download results.
- The page continues to show concise run summary/status details while detailed row outcomes are shifted to downloadable format.
- The feature scope is limited to capacity upload results presentation and export behavior, not changes to upload validation rules.
