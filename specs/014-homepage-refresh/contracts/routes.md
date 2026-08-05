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

- Purpose: Render the admin import review page for usage and invoice data.
- Query parameters: `reporting_month`, `data_type`, `supply_ids`, `supply_id`.
- Expected behavior: Shows the current filtered import view in the admin area with no create-report section.

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
- Expected behavior: Redirects to the new admin import review route while preserving the relevant query string.

## Client-Side Expectations

- The public dashboard and admin import page should share the site-selection and supply-loading behavior where possible.
- The public dashboard should not render the admin-only report creation controls.
- The inactive-meter toggle should default to off.