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
3. Open `/panel/imports/?reporting_month=2026-08&data_type=monthly&supply_ids=<ids>` and confirm the admin import review page loads.
4. Confirm the page layout matches the admin shell and does not include the create-report section.
5. Confirm the Back action returns to `/panel/`.

## Validate export behavior

1. Apply filters on the admin import review page.
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