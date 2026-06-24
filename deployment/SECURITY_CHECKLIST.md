# Security Hardening Checklist

Before release, verify the following:

- Secrets are sourced from environment variables or approved secret storage.
- No secrets appear in logs, templates, or source control.
- HTTPS redirect is enabled in production.
- Session and CSRF cookies are marked secure in production.
- Database transport uses SSL where supported.
- Admin account changes have been approved.
- Deployment approval has been recorded.
