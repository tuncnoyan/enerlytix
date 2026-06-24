# API Documentation

## Site list

- `GET /`
- Returns the searchable site dashboard.

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
