# Data Model: Homepage Refresh

## Existing Persisted Entities

### Site

- Purpose: Represents a site that can be searched, selected, and counted on the dashboard.
- Key fields used by this feature: `id`, `name`, `external_id`, `description`.
- Relationships: One `Site` has many `Supply` records.
- Feature usage: The public home page lists sites, applies the site search filter, and drives the supply panel.

### Supply

- Purpose: Represents a utility meter or supply attached to a site.
- Key fields used by this feature: `id`, `site_id`, `name`, `external_id`, `utility_type`, `parent_account_id`, `device_id`, `status`.
- Relationships: Many `Supply` records belong to one `Site`; a fiscal supply can have related submeter supplies via `parent_account_id`.
- Feature usage: The supply list filters by utility type, meter type, and the new supply search plus inactive-meter toggle.

### ImportRun, HalfHourlyConsumption, MonthlyConsumption, InvoiceCost

- Purpose: Store imported usage and invoice data for admin review and export.
- Key fields used by this feature: reporting month, supply identifiers, period start/end, quantity/value, run metadata, and import status.
- Relationships: Import runs collect imported records for a reporting month and selected supplies.
- Feature usage: The admin review page displays the imported data set and exports the current filtered view.

## Derived View Models

### DashboardFilterState

- Fields: `site_query`, `selected_site_ids`, `utility_type`, `meter_type`, `supply_query`, `include_inactive`.
- Purpose: Represents the current dashboard filters without persisting them.
- Validation rules: `include_inactive` defaults to `false`; `selected_site_ids` must be numeric when passed to the supply endpoint.

### AdminImportReviewQuery

- Fields: `reporting_month`, `data_type`, `supply_ids`, `supply_id`.
- Purpose: Captures the current view state for the import review page and its exports.
- Validation rules: `reporting_month` is required for loading import data; exported rows must match the active query.

### ExportSelection

- Fields: current filters from `AdminImportReviewQuery` plus output format (`csv` or `xlsx`).
- Purpose: Describes exactly which rows should be exported.
- Validation rules: Export output must match the current filtered view only, not a broader unfiltered dataset.

## State Transitions

- Home page flow: initial render -> site search/filter -> site selection -> supply list load -> supply search and inactive toggle -> optional export/navigation into admin area.
- Admin import review flow: admin page render -> import query load -> current filtered view displayed -> export CSV/XLSX -> back to admin dashboard.

## Data Changes

- No schema changes are expected.
- This feature is expected to reuse existing models and add only view/query state plus template and route changes.