# Quickstart - Available Capacity Integration Validation

## Prerequisites
- Project dependencies installed and Django app runnable.
- Database migrations applied.
- Access to Settings page.
- A valid `.xlsx` file with columns:
  - `Name`
  - `eSight Meter Code`
  - `Av Cap (kVA)`

## Scenario 1: Successful Upload and Report Display
1. Start app and open Settings page.
2. In the Available Capacity section, upload a valid `.xlsx` file.
3. Submit upload.
4. Confirm success message includes accepted row count and zero rejected rows.
5. Open report page for a site with electricity meters that match uploaded eSight Meter Codes.
6. Navigate to Electricity Load Factor card and confirm:
   - metric label is `Available Capacity (kVA)`
   - value is numeric (not `N/A`) for matched meters.

Expected outcome:
- Uploaded values are persisted and shown in load-factor output for matching meters.

## Scenario 2: Partial Import with Row Errors
1. Prepare `.xlsx` containing a mix of valid and invalid rows (blank code, non-numeric capacity, duplicate code).
2. Upload through Settings page.
3. Confirm UI shows partial-success summary with accepted/rejected counts.
4. Confirm row-level error messages identify rejected rows.
5. Re-open report and verify only meters with valid imported rows show numeric capacity.

Expected outcome:
- Valid rows are imported; invalid rows are skipped with clear error details.

## Scenario 3: Required-Column Validation
1. Upload `.xlsx` missing one required column (for example, remove `Av Cap (kVA)`).
2. Submit upload.

Expected outcome:
- Upload is rejected as failed.
- Missing-column feedback is displayed.
- No capacity-reference rows are changed.

## Scenario 4: Incremental Refresh Behavior
1. Upload baseline valid `.xlsx`.
2. Upload second `.xlsx` with changed values for a subset of existing eSight Meter Codes and no entries for others.
3. Open report for affected and unaffected meters.

Expected outcome:
- Matching keys use latest uploaded values.
- Previously stored unmatched keys remain available.

## Execution Notes (2026-07-17)

- Focused automated validation command:
  - `python manage.py test sitesync.tests.test_capacity_upload sitesync.tests.test_settings_view sitesync.tests.test_report_drafts`
  - Result: `OK` (8 tests)
- SC-001 measurement (`valid rows available for report use within 1 minute`):
  - Local measurement result: `0.0766s` for a 200-row valid `.xlsx` import.
  - Accepted rows: `200/200`.
- SC-003 measurement (`>=95% matched electricity meters display numeric capacity`):
  - Local measurement result: `100.0% (5/5)` matched electricity supplies returned numeric `available_capacity_kva`.
