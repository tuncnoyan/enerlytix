# Security Hardening Checklist

Before release, verify the following:

- Secrets are sourced from environment variables or approved secret storage.
- No secrets appear in logs, templates, or source control.
- HTTPS redirect is enabled in production.
- Session and CSRF cookies are marked secure in production.
- Database transport uses SSL where supported.
- Admin account changes have been approved.
- Deployment approval has been recorded.

## Pen-Test Hardening Controls

- Sensitive endpoints return 401 for unauthenticated requests.
- Admin-only actions return 403 for authenticated non-admin users.
- Password reset flows issue one-time recovery tokens; no static reset password is assigned.
- Invitation acceptance rejects weak passwords using Django validators.
- Manual sync redirect targets accept only internal paths and reject external/scheme-relative targets.
- Error responses are sanitized and do not leak exception details.
- Client IP attribution trusts forwarding headers only when source matches `TRUSTED_PROXY_CIDRS`.

## Production Startup Gate

- Production startup blocks when required controls are missing:
	- `SECRET_KEY` is default/insecure.
	- `DEBUG=True`.
	- `SECURE_SSL_REDIRECT=False`.
	- `SESSION_COOKIE_SECURE=False`.
	- `CSRF_COOKIE_SECURE=False`.
	- `SECURE_HSTS_SECONDS<=0`.
- Run deploy checks in production-like configuration:
	- `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py check --deploy`
