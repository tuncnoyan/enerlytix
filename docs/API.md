# API Documentation

## Site list

- `GET /`
- Returns the searchable site dashboard.

## Report editor and cover pages

- `GET /report/?site_id=<id>&end_month=YYYY-MM`
- Renders report visuals with integrated cover pages:
  - Front cover page 1
  - Front cover page 2
  - Report body pages
  - Back cover page
- Front cover page 1 editable fields:
  - Site title
  - Reporting month title (`[Month Year] Energy Report`)
  - Date (`DD MMMM YYYY`)
  - Optional client logo
- Front cover page 1 background replacement rules:
  - Allowed: JPG/JPEG/PNG/WebP
  - Max size: 10 MB
- Client logo replacement rules:
  - Allowed: PNG/JPG/SVG
  - Max size: 2 MB

## Manual sync

- `POST /sync/`
- Triggers a manual refresh from the Etainabl API.
- Success redirects back to the dashboard.
- Errors return JSON in the form:

```json
{
  "error": {
    "message": "Unable to complete sync",
    "details": "..."
  }
}
```

## Supplies by site

- `GET /supplies/?site_id=<id>`
- Returns the supply panel HTML for a selected site.

## Settings

- `GET /settings/`
- `POST /settings/`
- Loads and saves the runtime Etainabl configuration.

### Available capacity upload via Settings

- Route: `POST /settings/`
- Content type: `multipart/form-data`
- Required file field: `capacity_upload_file` (`.xlsx` only)
- Action marker: `capacity_upload_submit=1`

Required columns in uploaded workbook:

- `Name`
- `eSight Meter Code`
- `Av Cap (kVA)`

Behavior:

- Performs partial import for row-level validation failures.
- Valid rows are upserted by normalized `eSight Meter Code`.
- When an incoming row matches an existing normalized `eSight Meter Code`, the stored `Name` and `Av Cap (kVA)` are replaced with the latest uploaded values.
- Invalid rows are skipped and returned as row-level messages.
- Blank, non-numeric, or negative `Av Cap (kVA)` values are rejected at row level.
- Existing records not referenced by incoming keys remain unchanged.

Rendered response context includes:

- `capacity_upload_status` (`success`, `partial_success`, `failed`)
- `capacity_upload_total_rows`
- `capacity_upload_accepted_rows`
- `capacity_upload_rejected_rows`
- `capacity_upload_errors` (row-level messages)

## Consumption import

- `POST /api/consumption-import/`
- Triggers usage and invoice import for selected supplies and reporting month.

Request payload:

```json
{
  "supply_ids": ["6584fdd1c9ec42556202eaa2"],
  "reporting_month": "2026-05",
  "refresh_mode": true
}
```

Response payload:

```json
{
  "import_run_id": "2bf3cfc6-a264-4cc9-8bfd-565e2a8f8507",
  "status": "success",
  "supplies_count": 1,
  "records_imported": 305,
  "records_failed": 0,
  "retry_count": 0,
  "error_details": {},
  "outcome_details": []
}
```

## Consumption display API

- `GET /api/consumption-display/?reporting_month=YYYY-MM&data_type=monthly&supply_id=<external_id>`
- Returns table-ready imported records for selected filters.

Response payload:

```json
{
  "reporting_month": "2026-05",
  "data_type": "monthly",
  "total_records": 24,
  "records": [
    {
      "id": "9aeeea50-62df-4f45-ba11-96ab190f6081",
      "supply_id": 12,
      "supply_external_id": "6584fdd1c9ec42556202eaa2",
      "supply_name": "Main Meter",
      "data_type": "monthly",
      "source_period_start": "2025-01-01T00:00:00Z",
      "source_period_end": "2025-02-01T00:00:00Z",
      "canonical_month_key": "2025-02",
      "value": "2078.115000"
    }
  ]
}
```

## Report data API

- `GET /api/report-data/?site_id=<id>&end_month=YYYY-MM`
- Includes a `cover_defaults` object for shared cover rendering in draft/final/PDF/PPTX workflows.
- `cover_defaults` includes:
  - `sequence`: `front_cover_1`, `front_cover_2`, `body_pages`, `back_cover`
  - `front_cover_1` defaults
  - `front_cover_2` defaults and contents entries
  - `back_cover` static asset descriptor

## Consumption display page

- `GET /consumption-display/`
- Renders the dedicated usage/invoice table UI with month, supply, and data-type filters.

## Import run audit detail

- `GET /api/import-runs/<import_run_id>/`
- Returns full persisted audit details for a single import run.
- Requires authentication.

## Admin audit log viewer

- `GET /panel/audit-logs/`
- Authentication required; admin privileges required.

Query parameters:

- `user` (optional): actor user id
- `keyword` (optional): message/target/actor keyword
- `start` (optional): start datetime (UTC comparison)
- `end` (optional): end datetime (UTC comparison)
- `action_type` (optional): normalized action code
- `page` (optional): page number

Behavior:

- Returns HTML viewer page with filter controls and paginated results.
- Invalid filters return HTTP 200 with inline field validation errors.
- One-sided date range filters (`start`-only or `end`-only) are supported.

## Admin audit log CSV export

- `GET /panel/audit-logs/export.csv`
- Authentication required; admin privileges required.
- Uses exactly the same filter parameters and semantics as the viewer route.

Behavior:

- `Content-Type: text/csv`
- Header row always present.
- Matching rows include UTC timestamp label for unambiguous interpretation.
- Invalid filters return HTTP 400 JSON payload with `errors`.
- If matching row count exceeds 50,000, returns HTTP 400 with clear "narrow filters" message and does not generate partial file.

## Admin audit log XLSX export

- `GET /panel/audit-logs/export.xlsx`
- Authentication required; admin privileges required.
- Uses exactly the same filter parameters and semantics as the viewer route.

Behavior:

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Header row always present.
- Matching rows include UTC timestamp label for unambiguous interpretation.
- Invalid filters return HTTP 400 JSON payload with `errors`.
- If matching row count exceeds 50,000, returns HTTP 400 with clear "narrow filters" message and does not generate partial file.
