# Quickstart: Pen-Test Hardening Validation

## Purpose

Validate that security hardening controls in spec 019 are working end-to-end using Docker-first workflows.

## Prerequisites

- Docker Desktop available
- Repository root: `enerlytix`
- Environment configured from `.env`/deployment variables as appropriate

## Setup

1. Start containers:

```bash
docker compose -f django_app/docker/docker-compose.yml up -d --build
```

2. Run migrations:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

## Validation Scenarios

### Scenario A: Protected endpoint denial semantics

1. Run security-focused tests covering protected routes.
2. Verify unauthenticated requests return 401 and authenticated unauthorized requests return 403.
3. Confirm denied requests produce no side effects.

Reference: [Security Hardening Contract](./contracts/security-hardening-contract.md)

### Scenario B: Credential recovery hardening

1. Execute tests for administrator-triggered account reset flow.
2. Verify no static/predictable password assignment occurs.
3. Verify recovery token is single-use and invalid after 15 minutes.

Reference: [Security Hardening Contract](./contracts/security-hardening-contract.md)

### Scenario C: Invitation password quality enforcement

1. Attempt invitation acceptance with weak password.
2. Confirm account creation is rejected with validation feedback.
3. Repeat with compliant password and confirm success.

Reference: [spec.md](./spec.md) FR-007 and SC-004

### Scenario D: Redirect and error-sanitization checks

1. Exercise redirect paths with external and scheme-relative values.
2. Confirm non-internal targets are rejected.
3. Trigger controlled failure paths and verify user responses do not expose raw exception details.

Reference: [Security Hardening Contract](./contracts/security-hardening-contract.md)

### Scenario E: Forwarded IP trust boundary checks

1. Exercise request logging with trusted and untrusted source paths.
2. Confirm forwarding headers are only used for trusted proxy CIDRs.
3. Confirm untrusted sources use direct remote address.

Reference: [spec.md](./spec.md) FR-010

### Scenario F: Production readiness gate

1. Run deployment security checks in production-like configuration.
2. Confirm missing required controls fail checks.
3. Confirm startup is blocked for production context when required controls are absent.

## Commands

Run deployment security checks:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py check --deploy
```

Run test suite (or scoped security tests):

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests
```

## Expected Outcomes

- All sensitive endpoints enforce contract-aligned access decisions.
- Credential flows satisfy one-time, short-lived recovery requirements.
- Redirect and error response behaviors are hardened.
- Trusted-proxy IP attribution behavior is deterministic and spoof-resistant.
- Deployment-grade security checks and regression tests pass for release readiness.

## Recorded Validation Run

Date: 2026-08-07

- Command:
	- `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_pen_test_hardening_access sitesync.tests.test_pen_test_hardening_credentials sitesync.tests.test_pen_test_hardening_runtime --verbosity 2`
	- Result: `Ran 25 tests ... OK`
- Scenario outcomes:
	- Scenario A: PASS (401/403 semantics verified for baseline routes)
	- Scenario B: PASS (no static reset password assignment; recovery issuance path verified)
	- Scenario C: PASS (weak invitation passwords rejected; strong password accepted)
	- Scenario D: PASS (scheme-relative redirect rejected; failure responses sanitized)
	- Scenario E: PASS (forwarded headers trusted only when source proxy CIDR is trusted)
	- Scenario F: PARTIAL in non-production config (`check --deploy` produced warnings for DEBUG/SSL/cookie/HSTS/secret defaults as expected outside production)
