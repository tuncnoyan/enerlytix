# Phase 0 Research: Pen-Test Hardening and Readiness

## Decision 1: Protect sensitive API and admin mutation surfaces with strict authn/authz

- Decision: Treat import execution, report/consumption data APIs, settings mutation, capacity upload, and manual sync as protected surfaces requiring authentication and role-constrained authorization.
- Rationale: These surfaces can mutate operational state, trigger expensive upstream integrations, or expose sensitive usage data.
- Alternatives considered:
  - Keep mixed public/private endpoints and rely on obscurity: rejected due to direct exposure risk.
  - Authenticate only mutating endpoints but leave read endpoints open: rejected due to data disclosure findings.

## Decision 2: Normalize denied-access semantics to 401/403

- Decision: Return 401 for unauthenticated requests and 403 for authenticated-but-unauthorized requests for protected resources.
- Rationale: Improves testability, aligns with clarified spec behavior, and supports deterministic security validation.
- Alternatives considered:
  - Always return 403: rejected because it obscures authentication state and weakens diagnostics.
  - Redirect for APIs: rejected because machine clients need explicit status codes.

## Decision 3: Replace static reset credential flow with one-time recovery tokens

- Decision: Eliminate predictable reset passwords and require a single-use recovery token valid for 15 minutes.
- Rationale: Prevents deterministic account takeover paths while preserving recoverability.
- Alternatives considered:
  - Keep static temporary password with forced change: rejected as guessable/shared secret pattern.
  - Long-lived recovery token: rejected due to replay window expansion.

## Decision 4: Enforce password quality on invitation activation

- Decision: Apply password strength validation during invitation acceptance before account creation finalization.
- Rationale: Closes weak-password admission path introduced by custom account creation flow.
- Alternatives considered:
  - Defer validation until first login: rejected because weak passwords would still enter system.
  - Only minimum length check: rejected as insufficient against common weak-password attacks.

## Decision 5: Enforce internal-only redirect targets

- Decision: Accept only validated internal redirect targets and reject scheme-relative/external destinations.
- Rationale: Mitigates open redirect abuse for phishing and session confusion.
- Alternatives considered:
  - Prefix check with leading slash only: rejected because `//host` bypass remains.
  - Remove all user-driven redirection: rejected due to UX regression in valid return flows.

## Decision 6: Remove internal exception detail leakage from user responses

- Decision: Return sanitized user-facing error payloads while preserving detailed diagnostic data in server logs/audit events.
- Rationale: Reduces attacker reconnaissance while retaining observability.
- Alternatives considered:
  - Return raw exception text for troubleshooting convenience: rejected due to information disclosure risk.
  - Suppress all logging to avoid leakage: rejected because it harms operational diagnosis.

## Decision 7: Trust forwarding headers only from configured proxy CIDR allowlist

- Decision: Use forwarding headers only when request source matches configured trusted proxy CIDRs; otherwise use direct remote address.
- Rationale: Preserves audit-log integrity and prevents spoofed client IP attribution.
- Alternatives considered:
  - Trust all forwarding headers: rejected as spoofable.
  - Never trust forwarding headers: rejected because legitimate proxy deployments need true client IP capture.

## Decision 8: Enforce fail-closed production security checks at CI/release and startup

- Decision: Fail CI/release checks and block production startup when required security controls (secret handling, HTTPS/cookie protections) are missing.
- Rationale: Prevents insecure configuration drift from reaching runtime.
- Alternatives considered:
  - Warn-only approach: rejected because it permits insecure deployment.
  - CI-only enforcement: rejected because direct runtime deployments could bypass CI.

## Decision 9: Keep Docker-first validation and regression gating

- Decision: Use Docker Compose web container as authoritative environment for checks/tests and include explicit security regression coverage for this feature.
- Rationale: Aligns with constitution requirements and existing project workflow.
- Alternatives considered:
  - Local host-only ad hoc checks: rejected due to environment drift risk.
  - Partial manual verification without automated tests: rejected due to regression risk.

## Implementation Evidence (2026-08-07)

### Automated security regression execution

- Command executed:
  - `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_pen_test_hardening_access sitesync.tests.test_pen_test_hardening_credentials sitesync.tests.test_pen_test_hardening_runtime --verbosity 2`
- Result:
  - `Ran 25 tests ... OK`
- Full app regression command executed:
  - `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests --verbosity 1`
- Full app regression result:
  - `Ran 281 tests ... OK`

### SC-001 Sensitive Endpoint Baseline coverage mapping

- `POST /api/consumption-import/`:
  - unauthenticated denied (`401`) in `test_consumption_import_requires_authentication`
  - non-admin denied (`403`) in `test_consumption_import_requires_admin`
- `GET /api/consumption-display/`:
  - unauthenticated denied (`401`) in `test_consumption_display_requires_authentication`
- `GET /api/report-data/`:
  - unauthenticated denied (`401`) in `test_report_data_requires_authentication`
- `GET /api/import-runs/{import_run_id}/`:
  - unauthenticated denied (`401`) in `test_import_run_detail_requires_authentication`
- `POST /sync/`:
  - unauthenticated denied (`401`) in `test_manual_sync_requires_authentication`
  - non-admin denied (`403`) in `test_manual_sync_requires_admin`
- `POST /settings/` mutation path:
  - unauthenticated denied (`401`) in `test_settings_post_requires_authentication`
  - non-admin denied (`403`) in `test_settings_post_requires_admin`
- `GET /settings/capacity-upload/results.xlsx`:
  - unauthenticated denied (`401`) in `test_capacity_results_export_requires_authentication`
  - non-admin denied (`403`) in `test_capacity_results_export_requires_admin`

Coverage result: 8/8 baseline endpoints verified for denied unauthenticated access; admin-scoped subset verified for authenticated non-admin denial.

### Deploy security check evidence

- Command executed:
  - `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py check --deploy`
- Result summary (non-production configuration):
  - Reported warnings for `DEBUG=True`, insecure/default `SECRET_KEY`, `SECURE_SSL_REDIRECT=False`, `SESSION_COOKIE_SECURE=False`, `CSRF_COOKIE_SECURE=False`, and `SECURE_HSTS_SECONDS` unset.
  - This confirms detection path for FR-011 controls is active and fail conditions are visible in runtime verification.
