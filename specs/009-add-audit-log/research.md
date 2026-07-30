# Research: Admin Audit Log

## Summary

Implement audit logging as a Django-native capability within the existing `sitesync` app and expose investigation/export operations through admin-only panel routes. The implementation remains inside the current Docker Compose runtime, and all automated validation is executed inside the web container.

## Decisions

### Decision 1: Capture audit events at service/view action boundaries for authenticated mutating flows

**Decision**: Record an audit entry whenever an authenticated mutating action succeeds, and also for denied/failed security-relevant attempts.

**Rationale**: This directly satisfies FR-001 and FR-001a while avoiding implicit logging gaps from relying only on one technical layer.

**Alternatives considered**:
- Middleware-only logging: broad but may miss domain context and entity identifiers.
- Model-signal-only logging: captures persistence changes but misses denied/failed access attempts.

### Decision 2: Use normalized action type codes plus human-readable messages

**Decision**: Store both a normalized action type code (for stable filtering/reporting) and a human-readable message (for investigator readability).

**Rationale**: Matches clarified requirement and keeps filtering robust over time.

**Alternatives considered**:
- Free-text-only activity logging: inconsistent filter behavior and analytics.
- Code-only logging without message text: poor investigation usability.

### Decision 3: Store timestamps in UTC and localize display only

**Decision**: Persist event timestamps in UTC and allow localized rendering in UI/export context.

**Rationale**: Ensures unambiguous chronology across environments and containers.

**Alternatives considered**:
- Server-local storage time: ambiguous during environment/timezone changes.
- Per-user local storage: hard to compare across users and sessions.

### Decision 4: Enforce admin-only viewer and export access at route level

**Decision**: Gate audit viewer and export endpoints with the same admin privilege checks used by admin panel routes.

**Rationale**: Aligns with FR-005 and FR-014 and constitution Principle III (log privacy and approved viewers).

**Alternatives considered**:
- Manager-level access in v1: expands sensitive access surface without explicit requirement.
- Read-only API token access: out of scope for this phase.

### Decision 5: Reuse current Docker Compose runtime and execute tests in container

**Decision**: Run migrations/tests via `docker compose -f django_app/docker/docker-compose.yml exec -T web ...` and keep validation inside the containerized stack.

**Rationale**: Matches user direction and constitution Principle V (containerized maintainability).

**Alternatives considered**:
- Local host interpreter tests: risks divergence from container runtime.
- Separate test harness container: unnecessary overhead for this scope.

### Decision 6: Implement export contracts for CSV and XLSX using active filters

**Decision**: Export endpoints must apply the exact active filter set and produce either CSV or XLSX files with equivalent row sets.

**Rationale**: Directly satisfies FR-010 through FR-012 and keeps compliance evidence consistent.

**Alternatives considered**:
- Asynchronous queued export for v1: more resilient for very large files but adds complexity not required now.
- CSV-only export: does not satisfy requirement for XLSX.

## Resolved Clarification Mapping

- Audit scope: all authenticated mutating actions across app.
- Failure/denial coverage: included for security-relevant attempts.
- Action representation: normalized code + message text.
- Retention: organizational policy with minimum 1 year.
- Time standard: UTC storage.

## Implementation Notes for Planning

- Introduce an audit log entity with immutable event payload fields needed for long-term readability even after target entities are deleted.
- Add filtered admin panel listing and export routes under panel namespace.
- Add integration and authorization tests that run in Docker web container only.
