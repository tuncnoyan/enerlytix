# Security Review: Admin Audit Log (T032)

Date: 2026-07-30
Reviewer: Speckit implement agent
Scope: admin-only access and denied-attempt logging paths in django_app/sitesync/views.py

## Reviewed Paths

- admin_panel_required decorator and all panel routes
- admin_audit_logs_view
- admin_audit_logs_export_csv_view
- admin_audit_logs_export_xlsx_view
- denied paths in team/role assignment and team detail mutating endpoints

## Findings

1. Access control enforcement for audit viewer/export
- Status: PASS
- Evidence: viewer/export endpoints are wrapped by admin_panel_required.
- Behavior: non-admin users are redirected to site list and denied attempt is logged.

2. Denied-attempt logging coverage on protected admin panel routes
- Status: PASS
- Evidence: admin_panel_required invokes _log_denied_admin_panel_access before redirect.
- Captured fields: actor (or anonymous), source IP, request path, denied outcome, reason metadata.

3. Denied-attempt logging coverage on privileged mutating APIs
- Status: PASS
- Evidence: user_team_assignment_view and role_assignment_view log ACCESS_DENIED on unauthorized POST/DELETE.
- Evidence: team_detail_view logs denied access and denied update attempts.

4. Export abuse control for large result sets
- Status: PASS
- Evidence: CSV/XLSX exports enforce >50000 threshold with fail-fast 400 and no file generation.

5. Validation boundary behavior
- Status: PASS
- Evidence: invalid viewer filters return HTTP 200 with inline errors; invalid export filters return 400 JSON.

## Residual Risks and Recommendations

1. Header-trusted IP address
- Risk: _get_client_ip trusts X-Forwarded-For directly and can be spoofed if proxy chain is not locked down.
- Recommendation: only trust X-Forwarded-For behind known reverse proxies; otherwise prefer REMOTE_ADDR.

2. High-volume denied-event bursts
- Risk: repeated unauthorized requests can increase audit row volume.
- Recommendation: add rate limiting (middleware or gateway) for panel routes and export endpoints.

3. Sensitive metadata hygiene
- Risk: future code may add secrets into metadata_json inadvertently.
- Recommendation: keep metadata payload strictly operational and non-secret; enforce review checklist item for metadata fields.

## Conclusion

- No blocking security defects identified for Phase 6 scope.
- Current implementation satisfies admin-only gating and denied-attempt audit logging requirements for viewer/export and related privileged paths.
