# Security Hardening Contract

## 1. Protected Surface Contract

All routes categorized as sensitive MUST conform to this access contract.

| Contract Field | Required Value |
|---|---|
| Authentication required | Yes |
| Unauthenticated denial status | 401 |
| Authenticated but unauthorized denial status | 403 |
| Side effects on denied request | None |
| Audit event on denied privileged action | Required |

Sensitive routes include, at minimum:
- Import trigger operations
- Report/consumption data APIs
- Import-run detail retrieval
- Runtime settings mutation
- Capacity upload and export of sensitive operational outcomes
- Manual synchronization trigger

Baseline routes and expected denials:
- `POST /api/consumption-import/`: 401 unauthenticated, 403 authenticated non-admin
- `GET /api/consumption-display/`: 401 unauthenticated
- `GET /api/report-data/`: 401 unauthenticated
- `GET /api/import-runs/{import_run_id}/`: 401 unauthenticated
- `POST /sync/`: 401 unauthenticated, 403 authenticated non-admin
- `POST /settings/` mutation paths: 401 unauthenticated, 403 authenticated non-admin
- `GET /settings/capacity-upload/results.xlsx`: 401 unauthenticated, 403 authenticated non-admin

## 2. Credential Recovery Contract

| Contract Field | Required Value |
|---|---|
| Predictable/static reset password allowed | No |
| Recovery token single use | Yes |
| Recovery token validity | 15 minutes |
| Replay attempt behavior | Rejected |
| Expired token behavior | Rejected with safe error response |

## 3. Invitation Acceptance Password Contract

| Contract Field | Required Value |
|---|---|
| Password strength validation at acceptance | Required |
| Weak-password creation allowed | No |
| Validation failure response | User-actionable, non-sensitive |

## 4. Redirect Safety Contract

| Contract Field | Required Value |
|---|---|
| External redirect targets | Rejected |
| Scheme-relative targets (`//host`) | Rejected |
| Internal validated paths | Allowed |

## 5. Error Exposure Contract

| Contract Field | Required Value |
|---|---|
| Raw exception details in user responses | Forbidden |
| User-facing error response | Sanitized |
| Detailed diagnostics | Server logs/audit context only |

## 6. Forwarded IP Trust Contract

| Contract Field | Required Value |
|---|---|
| Trust forwarded headers from any source | No |
| Trust condition | Source matches configured proxy CIDR allowlist |
| Non-trusted source behavior | Use direct remote address |

## 7. Production Security Gate Contract

| Contract Field | Required Value |
|---|---|
| CI/release enforcement | Fail build/release if required controls missing |
| Production startup enforcement | Block startup if required controls missing |
| Required controls scope | Secure secret handling + secure transport/cookie settings |

## 8. Verification Contract

Readiness verification MUST include:
- Deployment security check execution in production-like mode
- Automated regression tests for access control, credential flow safety, redirect validation, and error sanitization
- Evidence that all sensitive endpoints enforce 401/403 semantics correctly
