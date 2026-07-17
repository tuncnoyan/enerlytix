# Contract: Settings Capacity Upload

## Endpoint
- Route: `POST /settings/` (same page endpoint)
- Purpose: Process settings updates and available-capacity workbook uploads from the settings page.

## Request Shape
- Content type: `multipart/form-data`
- Form controls:
  - `settings_submit` (optional action discriminator)
  - existing settings fields: `etainabl_api_url`, `page_size`, `api_timeout`
  - `capacity_upload_file` (optional file input, `.xlsx` only)

## Validation Contract
- File-level validation:
  - Reject if file extension is not `.xlsx`
  - Reject if workbook cannot be opened
  - Reject if required columns are missing: `Name`, `eSight Meter Code`, `Av Cap (kVA)`
- Row-level validation (partial import semantics):
  - Blank `Name`: reject row
  - Blank `eSight Meter Code`: reject row
  - Non-numeric `Av Cap (kVA)`: reject row
  - Negative `Av Cap (kVA)`: reject row
  - Duplicate `eSight Meter Code` inside upload: reject duplicate rows

## Processing Contract
- Valid rows are upserted into capacity-reference storage by normalized `eSight Meter Code`.
- When an incoming row matches an existing normalized `eSight Meter Code`, the stored `Name` and `Av Cap (kVA)` are both replaced with the latest uploaded row values.
- Invalid rows are skipped.
- Existing reference rows without incoming key matches remain unchanged.

## Response/Render Contract
- HTTP status: `200` for rendered settings page (including partial success)
- Template context must include upload result summary:
  - `capacity_upload_total_rows`
  - `capacity_upload_accepted_rows`
  - `capacity_upload_rejected_rows`
  - `capacity_upload_errors` (row-indexed/user-readable list)
  - `capacity_upload_status` (`success`, `partial_success`, `failed`)

## User Messaging Contract
- Success: visible notice with accepted count.
- Partial success: visible warning with accepted/rejected counts and row-level reasons.
- Failure: visible error with reason (e.g., missing required columns or invalid file format).
