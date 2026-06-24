# Enerlytix

Enerlytix is a Django-based web app for analysing electricity, gas, and water usage data.

## Local development

1. Create a Python environment and install dependencies from `requirements.txt`.
2. Set environment variables in `.env`.
3. Run migrations from `django_app/`.
4. Start the app with `python manage.py runserver`.

## Docker

The app also supports Docker Compose from `django_app/docker/`.

## Main pages

- Site list dashboard
- Supply details panel
- Settings page for runtime configuration

## Security notes

- Secrets must come from environment variables.
- Production deployments require approval.
- Database connections should use encrypted transport where supported.
