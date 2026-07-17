# Feature Specification: Available Capacity Upload

**Feature Branch**: `[005-available-capacity-upload]`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "The \"Available Capacity\" value is currently displayed as \"N/A\" in the electricity load factor section of the report because it is missing from the data structure. I want to add a new feature to upload the required data manually as an Excel file. I've attached a sample Excel file containing the Average Capacity (Av Cap (kVA)) values. The number of columns in that Excel file may vary. However, there are just a couple of essential columns that should be present. They are the \"Name\", \"eSight Meter Code\" and \"Av Cap (kVA)\" columns. The first two of those three are key fields. To upload the file, I want to add a new section and function to the \"Settings\" page. The data would be static but may require updates from time to time. The \"Available Capacity (kW)\" title on the \"Electricity Load Factor\" page should also be updated to \"Available Capacity (kVA)\". Could you now update the spec document accordingly, please?"

## Clarifications

### Session 2026-07-17

- Q: Which meter-matching rule should be used when applying uploaded capacity values to report meters? -> A: Match by eSight Meter Code only.
- Q: Which upload file format should be accepted for this feature? -> A: Accept .xlsx files only.
- Q: How should imports behave when some rows are invalid? -> A: Use partial import; import valid rows and skip invalid rows with row-level error reporting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Available Capacity File (Priority: P1)

As an operations user, I want to upload a spreadsheet from the Settings page so that each electricity meter can show a maintained Available Capacity value instead of N/A in load factor reporting.

**Why this priority**: The current report output is incomplete without capacity values, which directly impacts the usefulness of electricity load factor analysis.

**Independent Test**: Upload a valid .xlsx spreadsheet that includes Name, eSight Meter Code, and Av Cap (kVA), then open a report where those meters appear and verify that Available Capacity values are populated.

**Acceptance Scenarios**:

1. **Given** I am on Settings and have a valid file, **When** I upload it, **Then** the system stores rows keyed by eSight Meter Code and reports successful update counts.
2. **Given** uploaded rows contain eSight Meter Codes that match meters used in electricity reports, **When** I open the load factor section, **Then** Available Capacity values display in kVA rather than N/A for matched meters.

---

### User Story 2 - Validate File Structure and Data Quality (Priority: P2)

As an operations user, I want clear validation feedback during upload so that I can fix format issues quickly and avoid loading bad or ambiguous capacity data.

**Why this priority**: Data quality controls prevent silent errors and maintain trust in report values.

**Independent Test**: Upload files with missing required columns, blank key fields, duplicate key combinations, and non-numeric capacity values; verify each upload is rejected with actionable feedback.

**Acceptance Scenarios**:

1. **Given** a file is missing one or more required columns, **When** I upload it, **Then** the upload fails and lists the missing column names.
2. **Given** a row has blank Name or eSight Meter Code, **When** I upload it, **Then** the row is flagged as invalid and is not imported.
3. **Given** duplicate eSight Meter Code values exist in one upload, **When** I submit the file, **Then** duplicate rows are flagged and skipped while non-duplicate valid rows are imported.
4. **Given** Av Cap (kVA) is not numeric in a row, **When** I upload it, **Then** that row is flagged with a data-type validation error.
5. **Given** a file contains both valid and invalid rows, **When** I upload it, **Then** valid rows are imported and invalid rows are skipped with row-level error reasons.

---

### User Story 3 - Refresh Static Capacity Data Over Time (Priority: P3)

As an operations user, I want to re-upload newer capacity files when data changes so that reports continue to reflect current agreed values.

**Why this priority**: Capacity data is mostly static but requires occasional maintenance.

**Independent Test**: Upload an initial file, then upload a revised file with changed capacity values for existing keys and verify the latest values are used in subsequent reports.

**Acceptance Scenarios**:

1. **Given** a key already exists from a prior upload, **When** a new file includes that key with a different Av Cap (kVA), **Then** the latest uploaded value is used for future reporting.
2. **Given** a new upload omits previously imported keys, **When** the upload completes, **Then** existing previously stored keys remain available unless explicitly replaced by matching keys.

### Edge Cases

- Upload .xlsx file has many additional non-required columns in varying order; required columns are still detected and processed.
- Required-column detection trims leading/trailing whitespace and is case-insensitive.
- Only canonical required headers are accepted after normalization: Name, eSight Meter Code, Av Cap (kVA).
- Header aliases beyond normalized canonical names are not accepted in this release.
- Upload contains eSight Meter Code values with surrounding whitespace; keys are normalized before matching.
- Upload file is empty or contains only headers; no data is imported and a clear warning is shown.
- A report meter has no matching stored eSight Meter Code; Available Capacity remains unavailable for that meter.
- Uploaded file is not .xlsx (for example .xls or .csv); upload is rejected with a supported-format message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a dedicated Available Capacity upload section on the Settings page.
- **FR-002**: System MUST accept manual upload of .xlsx spreadsheet files for available capacity maintenance.
- **FR-003**: System MUST require the columns Name, eSight Meter Code, and Av Cap (kVA) to be present in an uploaded file.
- **FR-004**: System MUST treat eSight Meter Code as the business key for identifying each capacity record.
- **FR-005**: System MUST validate Av Cap (kVA) as numeric before accepting a row.
- **FR-006**: System MUST ignore non-required columns during import processing.
- **FR-007**: System MUST treat rows with duplicate eSight Meter Code values within the same upload as invalid rows, skip those duplicate rows, continue importing non-duplicate valid rows, and include duplicate-row details in the row-level error report.
- **FR-008**: System MUST provide a user-visible import result summary including total rows read, accepted rows, and rejected rows with reasons.
- **FR-009**: System MUST store uploaded capacity records so they persist across sessions and are available for report rendering.
- **FR-010**: System MUST use stored available capacity values when rendering electricity load factor outputs for matched meters.
- **FR-011**: System MUST update the label from "Available Capacity (kW)" to "Available Capacity (kVA)" in the electricity load factor section.
- **FR-012**: System MUST allow later uploads to refresh existing eSight Meter Code-matched records with newly provided Av Cap (kVA) values.
- **FR-013**: System MUST use append-update mode for incremental uploads: only eSight Meter Code keys present in the upload are created or updated; existing records with keys not present in the upload remain unchanged.
- **FR-014**: System MUST reject non-.xlsx uploads and return a user-visible supported-format validation message.
- **FR-015**: System MUST perform partial import for data-row validation failures: valid rows are imported, invalid rows are skipped, and row-level errors are reported.
- **FR-016**: System MUST normalize uploaded header values by trimming surrounding whitespace and comparing case-insensitively against canonical required headers only.

### Key Entities *(include if feature involves data)*

- **Capacity Upload File**: User-provided spreadsheet containing variable columns, with required fields Name, eSight Meter Code, and Av Cap (kVA).
- **Capacity Record**: Persisted available-capacity data identified by eSight Meter Code and containing Name, Av Cap (kVA), source upload timestamp, and record status.
- **Capacity Import Result**: Summary artifact returned after each upload, including processed row counts and validation outcomes.
- **Electricity Meter Match Context**: Reporting-time mapping between report meter identity and stored capacity record key to determine whether capacity can be displayed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid rows from a correctly formatted upload are available for report use within one minute of upload completion.
- **SC-002**: 100% of uploads with missing required columns are rejected with explicit missing-column feedback.
- **SC-003**: At least 95% of electricity meters that have matching eSight Meter Code values display a numeric Available Capacity (kVA) value instead of N/A.
- **SC-004**: Users can complete a routine capacity refresh upload from Settings in under 2 minutes.
- **SC-005**: For files containing known invalid rows, 100% of invalid rows are reported with row-level reasons.

## Assumptions

- Capacity values in Av Cap (kVA) are provided and maintained by authorized operations users.
- eSight Meter Code values in uploaded files correspond to the meter identifiers used by report data.
- This feature covers manual upload and maintenance only; no external automatic synchronization is introduced.
- Existing settings access controls are reused for who can perform uploads.
- Uploaded capacity records are considered business reference data and remain in place between periodic manual updates.
- Source files for this feature are provided in .xlsx format.
- Full replacement or purge mode is out of scope for this release.
