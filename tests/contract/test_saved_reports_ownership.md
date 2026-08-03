# Contract Test: Saved Reports Ownership Fields

Feature: 010-report-ownership-model
Route: `GET /reports/`

## Required Field Assertions

- [x] Response includes a reports collection for authenticated users with visibility.
- [x] Each row contains `site_name` or equivalent report/site label.
- [x] Each row contains `reporting_month`.
- [x] Each row contains `owner_name`.
- [x] Each row contains `created_at`.
- [x] Each row contains `last_edited_by_name`.
- [x] Each row contains `last_edited_at`.
- [x] Each row contains `status`.
- [x] Each row contains `access_mode` as `owner`, `collaborator`, `admin`, or `read_only`.
- [x] Each row contains `open_url` targeting `/report/?site_id=<id>&end_month=<YYYY-MM>`.

## Empty State Assertions

- [x] Unassigned authenticated users see explicit empty state UI.
- [x] Empty state does not trigger client-side table rendering errors.

## Legacy Fallback Assertions

- [x] Missing historical ownership fields fall back without page failure.
- [x] Rows remain renderable when `created_at` or `last_edited_at` is absent.
