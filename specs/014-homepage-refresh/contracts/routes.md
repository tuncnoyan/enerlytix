# Route Contract: Homepage Refresh

## Public Home Page

### `GET /`

- Purpose: Render the public home page for regular users.
- Query parameters: `q` for site search.
- Expected behavior: The page focuses on site selection and supply inspection only; admin-only refresh/import/report actions are not shown.

### `GET /supplies/`

- Purpose: Render the supply panel fragment for the selected site(s).
- Query parameters: `site_ids`, `utility_type`, `meter_type`, `supply_q`, `include_inactive`.
- Expected behavior: Returns the HTML fragment used to render the supply panel, with inactive supplies excluded unless `include_inactive` is truthy.

### `POST /sync/`

- Purpose: Trigger a manual refresh of source data.
- Access: Admin-only in the UI; the existing endpoint remains the execution target.
- Expected behavior: Used from the admin dashboard rather than the public home page.

## Admin Area

### `GET /panel/`

- Purpose: Render the admin dashboard with the moved refresh and summary controls.
- Expected behavior: Exposes the controls that were removed from the public home page.

### `GET /panel/imports/`

- Purpose: Render the admin data-import selection page.
- Query parameters: `reporting_month`, `data_type`, optional `site_ids`, optional `supply_ids`, optional `supply_id` for legacy compatibility.
- Expected behavior: Shows import controls plus admin selectors for choosing sites and then supplies (including multiple sites) before loading data.

### `GET /panel/imports/results/`

- Purpose: Render the dedicated admin import-review results table page.
- Query parameters: `reporting_month`, `data_type`, optional `site_ids`, optional `supply_ids`, optional `supply_id` for legacy compatibility.
- Expected behavior: Renders records table, export actions, and a Back to Data Import action that returns to the selector page.

### `GET /api/import-review-sites/`

- Purpose: Return admin-selectable site options for the import review page.
- Access: Admin-only.
- Expected behavior: Returns site metadata for list rendering and multi-site selection.

### `GET /api/import-review-supplies/`

- Purpose: Return admin-selectable supply options scoped to selected site IDs.
- Query parameters: `site_ids`, optional `q`, optional `utility_type`, optional `include_submeters`, optional `include_inactive`, optional `supply_ids` for legacy deep-link hydration.
- Access: Admin-only.
- Expected behavior: Returns supply metadata (name, external ID, site, utility, meter type, status) used by the selector UI.

### `GET /panel/imports/export.csv`

- Purpose: Export the current filtered admin import view as CSV.
- Query parameters: same as the page route.
- Expected behavior: Returns a CSV file containing only the current filtered view.

### `GET /panel/imports/export.xlsx`

- Purpose: Export the current filtered admin import view as XLSX.
- Query parameters: same as the page route.
- Expected behavior: Returns an XLSX file containing only the current filtered view.

## Legacy Compatibility

### `GET /consumption-display/`

- Purpose: Preserve existing bookmarks and old links.
- Expected behavior: Redirects to the dedicated admin results route while preserving the relevant query string.

## Client-Side Expectations

- The public dashboard and admin import page should share the site-selection and supply-loading behavior where possible.
- The public dashboard should not render the admin-only report creation controls.
- The inactive-meter toggle should default to off.