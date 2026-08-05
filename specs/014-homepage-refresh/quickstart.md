# Quickstart: Homepage Refresh

## Prerequisites

- Run the app from `django_app`.
- Use the repo's existing Django environment and a local SQLite database when PostgreSQL is not available.
- Set `DATABASE_URL=sqlite:///local.db` if the local environment tries to connect to PostgreSQL.

## Start the app

```powershell
cd django_app
$env:DATABASE_URL = 'sqlite:///local.db'
python manage.py runserver 0.0.0.0:8080
```

## Validate the public home page

1. Open `/` as a regular user.
2. Confirm the page emphasizes site search and site selection.
3. Confirm the refresh, usage-import, and create-report controls are not visible on the public page.
4. Select a site and confirm the supply panel still loads.
5. Use the new supply search and inactive-meter toggle to verify inactive supplies are hidden by default and appear only when enabled.

## Validate the admin area

1. Open `/panel/` as an admin user.
2. Confirm the moved refresh and summary controls are present there.
3. Open `/panel/imports/` and confirm the admin data-import selection page loads.
4. Select one or more sites from the left selector and confirm supplies load in the right selector.
5. Use the supply search, Utility Type filter, Include sub meters checkbox, and Include inactive checkbox to verify filtering behavior.
6. Select one or more supplies (across one or multiple selected sites), set reporting month/display type, and click `Load Data`.
7. Confirm the app navigates to `/panel/imports/results/` and loaded records appear in the table.
8. Confirm the results page includes `Back to Data Import` and that it returns to `/panel/imports/` with query context.

## Validate export behavior

1. Load data on the admin import results page (month, type, site + supply selections).
2. Use `Export CSV` and `Export XLSX`.
3. Confirm each export reflects the currently filtered view only.

## Test commands

```powershell
cd django_app
$env:DATABASE_URL = 'sqlite:///local.db'
python -m pytest sitesync/tests
```

If the project is using Django's built-in test runner in your environment, an equivalent targeted check is:

```powershell
cd django_app
$env:DATABASE_URL = 'sqlite:///local.db'
python manage.py test sitesync.tests
```