# Data Model: Pen-Test Hardening and Readiness

## Overview

This feature is primarily behavioral hardening with minimal schema change pressure. The model impact is focused on security policy/state semantics and test evidence rather than introducing broad new business entities.

## Entities

### 1. SecurityPolicyProfile

- Purpose: Captures effective security expectations enforced by runtime and release gates.
- Fields:
  - mode (development, test, production)
  - require_secure_secret_key (boolean)
  - require_https_redirect (boolean)
  - require_secure_session_cookie (boolean)
  - require_secure_csrf_cookie (boolean)
  - require_hsts (boolean)
  - trusted_proxy_cidrs (list of CIDR strings)
- Relationships:
  - Referenced by readiness checks and request IP attribution policy.
- Validation rules:
  - Production profile requires all secure flags enabled.
  - trusted_proxy_cidrs must contain valid CIDR notation when present.

### 2. EndpointAccessRule

- Purpose: Defines required access level for sensitive routes and actions.
- Fields:
  - route_identifier
  - action_type (read, mutate, trigger)
  - authentication_required (boolean)
  - allowed_roles (set of role codes)
  - denied_status_unauthenticated (fixed 401)
  - denied_status_unauthorized (fixed 403)
- Relationships:
  - Applied to web/API route handlers.
  - Audited via security-relevant log events.
- Validation rules:
  - All sensitive routes must have authentication_required=true.
  - allowed_roles cannot be empty for privileged mutation/trigger actions.

### 3. CredentialRecoveryTokenPolicy

- Purpose: Governs administrator-triggered recovery behavior replacing static resets.
- Fields:
  - token_single_use (boolean, required true)
  - token_ttl_minutes (integer, fixed 15)
  - replay_protection_enabled (boolean)
  - invalidation_on_use (boolean)
- Relationships:
  - Used by account recovery flow and acceptance criteria.
- Validation rules:
  - token_ttl_minutes must equal 15 for this feature scope.
  - token_single_use and invalidation_on_use must be true.

### 4. InvitationCredentialValidationRule

- Purpose: Ensures invitation acceptance uses strong password validation.
- Fields:
  - validator_profile_name
  - minimum_strength_enforced (boolean)
  - weak_password_rejection_enabled (boolean)
- Relationships:
  - Applied during invitation acceptance before user account creation finalization.
- Validation rules:
  - Weak-password inputs are rejected with actionable feedback.

### 5. ReadinessEvidenceRecord

- Purpose: Represents repeatable proof that security controls are enforced.
- Fields:
  - check_name
  - execution_context (ci, release, startup, integration-test)
  - status (pass, fail)
  - executed_at
  - summary
- Relationships:
  - Aggregates output from deployment checks and regression tests.
- Validation rules:
  - Production readiness requires no unresolved critical failures.

## State Transitions

### Access decision state

- unauthenticated request -> denied_401
- authenticated but out-of-role request -> denied_403
- authenticated and authorized request -> allowed

### Credential recovery state

- issued -> pending_use
- pending_use -> consumed (single successful use)
- pending_use -> expired (after 15 minutes)
- consumed/expired -> invalid (non-reusable)

### Readiness gate state

- pre-check -> evaluating
- evaluating -> pass (all required controls present)
- evaluating -> fail (one or more required controls missing)
- fail at production startup context -> startup_blocked
