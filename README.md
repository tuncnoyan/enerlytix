# Enerlytix

Enerlytix is a Django web application for monitoring utility usage and costs across electricity, gas, and water supplies. It provides dashboard-driven data sync, usage and invoice imports, report visuals, and operational settings in a single app.

## What the application does

- Synchronizes sites and supplies from Etainabl.
- Imports half-hourly, monthly, and invoice data for selected supplies.
- Displays usage and invoice records for a selected reporting month.
- Generates utility report visuals per site and month.
- Supports runtime settings and import retention cleanup.

## Application structure

Top-level repository layout:

- django_app/: Django project and Sitesync application source.
- deployment/: deployment and security process documentation.
- docs/: API and security documentation.
- sample_app/: API request examples and sample payloads.
- specs/: feature specifications, plans, tasks, and contracts.
- tests/: additional project-level test folders.
- .env.example: environment variable template.

Key Django modules:

- django_app/manage.py: Django management entry point.
- django_app/config/settings.py: runtime settings and environment variable loading.
- django_app/config/urls.py: root URL routing.
- django_app/sitesync/models.py: core domain models for sites, supplies, and consumption/import data.
- django_app/sitesync/views.py: dashboard views and API endpoints.
- django_app/sitesync/services.py: sync/import and data processing services.
- django_app/sitesync/templates/sitesync/: dashboard, report, settings, and display templates.
- django_app/static/sitesync/js/: client-side behavior for dashboard, report, and data display.
- django_app/docker/: Dockerfile and Compose configuration for containerized development.

## Prerequisites

- Docker Desktop (required for all development and test workflows).
- Docker Compose v2 (required).

## Development setup (Docker-only)

All development and tests must run in the containerized Docker environment.

1. Create a local environment file from .env.example.
2. Start the Docker stack.
3. Run database migrations in the web container.

Example commands (PowerShell):

- Copy-Item .env.example .env
- docker compose -f django_app/docker/docker-compose.yml up -d --build
- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate

App URL:

- http://localhost:8080/

## Railway deployment

Enerlytix is ready for Railway with a production-style Django entrypoint and static file serving.

Required environment variables:

- SECRET_KEY
- DEBUG=False
- ALLOWED_HOSTS=your-domain.com
- DATABASE_URL=postgresql://...
- PORT=8080
- RAILWAY_PUBLIC_DOMAIN=your-app.up.railway.app
- SECURE_SSL_REDIRECT=True
- SESSION_COOKIE_SECURE=True
- CSRF_COOKIE_SECURE=True

Recommended startup command:

- `cd django_app && gunicorn --bind 0.0.0.0:$PORT config.wsgi:application`

## Docker setup

From the repository root:

- Copy-Item .env.example .env
- docker compose -f django_app/docker/docker-compose.yml up --build

Services:

- web: Django app on port 8080.
- db: PostgreSQL service used by the web container via DATABASE_URL.

To stop:

- docker compose -f django_app/docker/docker-compose.yml down

### Private image via GHCR

This repository can publish a private container image to GitHub Container Registry (GHCR).

Workflow file:

- .github/workflows/publish-ghcr-private.yml

What it does:

- builds from `django_app/docker/Dockerfile`
- publishes to `ghcr.io/<owner>/enerlytix`
- pushes tags for `latest` (default branch), branch names, tags, and commit SHA

One-time setup:

1. Ensure repository Actions are enabled.
2. Ensure package visibility remains private (GitHub Packages settings).
3. If your org restricts package publishing, allow GitHub Actions to publish packages.

Manual local login/pull commands (PowerShell):

- echo <GH_PAT_WITH_READ_PACKAGES> | docker login ghcr.io -u <github-username> --password-stdin
- docker pull ghcr.io/<owner>/enerlytix:latest
- docker run --rm -p 8080:8080 --env-file .env ghcr.io/<owner>/enerlytix:latest

Manual local build/push commands (PowerShell):

- docker build -f django_app/docker/Dockerfile -t ghcr.io/<owner>/enerlytix:manual .
- echo <GH_PAT_WITH_WRITE_PACKAGES> | docker login ghcr.io -u <github-username> --password-stdin
- docker push ghcr.io/<owner>/enerlytix:manual

## Configuration

Configuration is environment-variable driven. The app loads values from .env via python-dotenv.

### Core Django settings

- DEBUG: enables debug mode.
- SECRET_KEY: Django secret key.
- ALLOWED_HOSTS: comma-separated hostnames.
- DJANGO_SETTINGS_MODULE: defaults to config.settings in container workflows.

### Database

- DATABASE_URL:
	- if omitted, local SQLite is used at django_app/db.sqlite3.
	- if postgresql URL is provided, PostgreSQL is used.
- DATABASE_SSLMODE: PostgreSQL sslmode override.

### Etainabl integration

- ETAINABL_API_KEY: required API key.
- ETAINABL_API_URL: base API URL (default https://api.etainabl.com/2.0).
- ETAINABL_ACCOUNT_ID: root account id.
- API_TIMEOUT: request timeout seconds.

### Pagination and import behavior

- PAGE_SIZE: API pagination size for DRF list responses.
- CONSUMPTION_RETENTION_MONTHS: retention period for imported consumption and invoice data.
- CONSUMPTION_IMPORT_RETRY_COUNT: retries for transient import failures.
- CONSUMPTION_IMPORT_RETRY_BACKOFF_SECONDS: retry delay.
- CONSUMPTION_HALFHOURLY_MONTHS: months fetched for half-hourly imports.
- CONSUMPTION_MONTHLY_MONTHS: months fetched for monthly imports.
- CONSUMPTION_INVOICE_MONTHS: months fetched for invoice imports.

### Security toggles

- SECURE_SSL_REDIRECT
- SESSION_COOKIE_SECURE
- CSRF_COOKIE_SECURE
- SECURE_HSTS_SECONDS
- SECURE_HSTS_INCLUDE_SUBDOMAINS
- SECURE_HSTS_PRELOAD

For local development, start with .env.example values and harden for production.

## Usage

### Main pages

- /: Site and supply dashboard.
- /consumption-display/: usage and invoice display page.
- /report/: report visuals page.
- /settings/: runtime settings panel.
- /login/: login page template (available if authenticated flows are enabled).

### Dashboard flow

1. Open dashboard.
2. Sync sites and supplies with Refresh data.
3. Select site(s) and supply filters.
4. Import usage data with Load Data.
5. Create report with Create Report for a selected site and month.

### API endpoints

- POST /api/consumption-import/: trigger import for selected supply ids and reporting month.
- GET /api/consumption-display/: return display records by reporting month and data type.
- GET /api/report-data/: return aggregated report payload for site and month.
- GET /api/import-runs/<uuid>/: retrieve import run details.

### Data cleanup command

Run periodic retention cleanup in Docker:

- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py cleanup_expired_consumption

This removes expired HalfHourlyConsumption, MonthlyConsumption, and InvoiceCost records based on retention configuration.

## Testing and checks

Run checks and tests in Docker only:

- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py check
- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test

### Docker-only verification for report ownership implementation

For feature work under report ownership model, run verification in Docker only:

- docker compose -f django_app/docker/docker-compose.yml up -d --build
- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
- docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests

Optional pytest workflow (if configured in your environment):

- pytest

## Operational notes

- Keep secrets out of source control and use environment variables.
- Use PostgreSQL with TLS settings for production.
- Follow deployment approval and security checklists in deployment/.
- See docs/API.md and docs/SECRET_MANAGEMENT.md for integration and secret handling guidance.
