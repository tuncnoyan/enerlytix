# Secret Management

## Rules

- Keep API keys, database passwords, and Django secrets out of version control.
- Load secrets from environment variables or approved secret stores.
- Do not print secrets in application logs.
- Use encrypted database transport where the deployment platform supports it.

## Supported deployment approaches

- Docker environment variables
- Kubernetes secrets
- Azure App Service configuration
- Docker Secrets

## Environment variables

- `SECRET_KEY`
- `ETAINABL_API_KEY`
- `ETAINABL_API_URL`
- `DATABASE_URL`
- `DATABASE_SSLMODE`
- `ALLOWED_HOSTS`

## Audit log data handling

- Audit metadata must never include API keys, passwords, tokens, or full secret payloads.
- Audit viewer and export endpoints are admin-only; do not expose these routes through unauthenticated proxies.
- Exported audit files should be treated as sensitive operational evidence and stored in restricted-access locations.
- If exports are shared externally, apply least-privilege file access controls and retention policies.
- Source IP extraction should only trust forwarding headers from known proxy infrastructure.
