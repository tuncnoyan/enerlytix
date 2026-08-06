# Contract: Saved Reports Search and Filter Interface

Feature: 015-report-search-filters  
Date: 2026-08-06  
Status: Draft

## Scope

Defines request parameters, filter semantics, and response expectations for the saved reports listing route used by the Saved Reports page.

## Route

```text
GET /reports/
```

Route name: `sitesync:saved_reports`

## Query Parameters

All parameters are optional. When omitted, defaults apply.

- `site_query`: string
- `user_query`: string
- `start_month`: month key (`YYYY-MM`)
- `end_month`: month key (`YYYY-MM`)
- `report_status`: repeatable (`draft` | `final`)
- `validation_status`: repeatable (`draft` | `awaiting_validation` | `validated`)
- `format`: optional (`json`) for JSON payload mode

### Parameter Semantics

- Site and User queries use case-insensitive contains matching.
- `user_query` applies across OWNER, LAST EDITED BY, and VALIDATOR fields.
- Month range uses month-year precision only and inclusive boundaries.
- Default status selection on first load:
  - `report_status`: `draft`, `final`
  - `validation_status`: `draft`, `awaiting_validation`, `validated`
- Empty status selection in either group is valid and produces zero matching rows for that dimension.

## Validation Rules

- If both `start_month` and `end_month` are present and `start_month > end_month`, response must prevent misleading results and indicate range correction is required.
- Unknown status values must not expand result scope.
- Access/team scoping from existing authorization rules remains mandatory before filters are applied.

## HTML Response Contract

For standard page load (`GET /reports/` without `format=json`):

- Render filter controls:
  - Site search input
  - User search input
  - Start Month selector
  - End Month selector
  - Report Status checkboxes (Draft, Final)
  - Validation Status checkboxes (Draft, Awaiting validation, Validated)
- Render rows matching active combined criteria.
- Show explicit empty-state message when no rows match active criteria.
- Preserve selected filter values in control state after render.

## JSON Response Contract

For JSON mode (`GET /reports/?format=json`):

Top-level object:

- `reports`: array of filtered rows
- `selected_filters`: object with normalized active filter values

Each report row minimum fields:

- `id`
- `site_id`
- `site_name`
- `reporting_month`
- `status`
- `owner_name`
- `last_edited_by_name`
- `validator_name`
- `validation_status`
- `open_url`

`selected_filters` minimum fields:

- `site_query`
- `user_query`
- `start_month`
- `end_month`
- `report_statuses`
- `validation_statuses`

## Error Behavior

- Invalid month range behavior is mode-specific and fixed:
  - HTML page mode (`GET /reports/` without `format=json`): return HTTP 200 with inline validation message and render no report rows.
  - JSON mode (`GET /reports/?format=json`): return HTTP 400 with JSON body containing:
    - `detail`: `Start Month must be earlier than or equal to End Month`
    - `code`: `invalid_month_range`
    - `selected_filters`: normalized filter payload.
- Authorization remains unchanged: unauthenticated users redirect to login; unauthorized visibility is never broadened by filter parameters.

## Compatibility Requirements

- Existing saved-reports metadata contracts (ownership and validation columns) remain intact.
- Existing open-report action (`open_url`) behavior remains unchanged.
