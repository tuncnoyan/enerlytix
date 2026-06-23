# Quickstart: Etainabl Site & Supply Sync

## Prerequisites

- Docker installed and running on the development machine.
- A valid Etainabl API key with permission to fetch assets and accounts.
- The sample configuration values from `sample_app/supply_list.xlsx` available for local configuration.

## Setup

1. Copy or mount the Etainabl API configuration into the app environment.
   - Example: set `ETAINABL_API_KEY` and `ETAINABL_API_URL` in `.env`.
2. Build the container image:

```bash
docker build -t enerlytix-webapp .
```

3. Run the application container with the database container.

```bash
docker compose up -d
```

4. Apply database migrations.

```bash
docker compose exec web python manage.py migrate
```

## Validation Scenarios

### Scenario 1: Initial sync and site list display

1. Start the application and wait for it to complete the initial Etainabl sync.
2. Open the web UI in a browser.
3. Confirm the site list loads and renders site names in the left pane.
4. Search for a known site name and verify the list filters correctly.

### Scenario 2: Site selection and supply display

1. Select a site from the searchable site list.
2. Confirm the supply list appears adjacent to the site list.
3. Verify each supply row includes `name`, `utility_type`, and `device_id`.

### Expected Outcomes

- The web app starts and performs a background sync of sites and supplies.
- The site list is searchable and displays current site names.
- Supply details appear immediately beside the site list when a site is selected.

## Notes

- No user management is required for this initial version.
- The app should be containerized and runnable without requiring admin privileges on the host OS.
