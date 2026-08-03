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

## Report ownership governance controls

- Ownership transfer and collaborator grant endpoints must remain authenticated and role-gated.
- Owner unavailability fallback requires explicit team-lead approval and reason capture.
- Fallback ownership resolution must remain deterministic in this order:
	1. Team lead
	2. Manager
	3. Scoped admin
- Fallback candidates must be active and within report scope via site-team linkage.
- Previous owner must retain collaborator write access after fallback transfer unless explicitly revoked.

## Ownership audit expectations

- The following actions must emit auditable events:
	- Grant collaborator write access
	- Revoke collaborator write access
	- Manual ownership transfer
	- Team-lead unavailability approval and resulting fallback transfer
- Audit metadata must never include secret material while still capturing actor, report, and target user identifiers.
