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
