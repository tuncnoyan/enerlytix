# Enerlytix Django App

## Setup

- Install the Python dependencies from `requirements.txt`.
- Configure environment variables in `.env`.
- Run migrations from the `django_app/` directory.
- Start the app with `python manage.py runserver`.

## Runtime pages

- Site dashboard at `/`
- Manual refresh endpoint at `/sync/`
- Supply panel endpoint at `/supplies/`
- Settings page at `/settings/`

## Configuration

- Secrets must come from environment variables.
- Production deployments require approval.
- Database transport should use SSL where supported.
