# Implementation Plan: Etainabl Site & Supply Sync

**Branch**: `001-etainabl-site-supply-sync` | **Date**: 2026-06-23 | **Spec**: `specs/001-etainabl-site-supply-sync/spec.md`

**Input**: Feature specification from `specs/001-etainabl-site-supply-sync/spec.md`

## Summary

Implement a containerised Django web application that performs an initial sync of Etainabl assets and accounts, persists site and supply records in a SQL database, and displays a searchable site list with the selected site's supply details.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.x, Django REST Framework (for internal API support), requests, psycopg2-binary, Docker, Docker Compose

**Storage**: PostgreSQL in a container

**Testing**: pytest, pytest-django, Django test runner

**Target Platform**: Docker container environment (Docker Desktop on Windows or Windows Containers); app must be buildable and runnable without elevated system privileges

**Project Type**: Web application with backend database and frontend rendering via Django templates

**Performance Goals**: Load primary site list within 3 seconds for up to 100 sites in initial deployment

**Constraints**: No user management in this initial version; app must run containerised and not require admin privileges for normal operation; data sync should support idempotent updates.

**Scale/Scope**: Initial version supports up to 100 sites and associated supplies for interactive browsing.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Containerized architecture must align with constitution principle V. ✅ **ALIGNED**: Docker + Docker Compose is primary deployment model.
- No admin-privilege requirements for normal operations aligns with principle II. ✅ **ALIGNED**: All tasks assume standard user execution.
- Data persistence and secure handling of API credentials aligns with principle III. ⚠️ **PARTIAL**: See Governance section below.
- Windows-native support aligns with principle I. ⚠️ **NEEDS VALIDATION**: Docker Compose must be tested on Windows (Docker Desktop or Windows Containers).
- Production deployment approvals align with principle IV. ⚠️ **OUT OF SCOPE for MVP**: Approval workflow to be documented in governance; implementation tasks in Phase 6.

## Governance & Approval Workflow

### Production Deployment Approval (Constitution Principle IV)

All production deployments MUST follow this approval workflow:

1. **Pre-Deployment Review**:
   - Code review: All changes reviewed against constitution principles and security requirements.
   - Automated checks: Unit tests, integration tests, and security scanning pass.
   - Migration validation: Database migrations reviewed for backward compatibility.

2. **Approval Gate**:
   - A designated approver (defined in project governance) reviews the deployment candidate.
   - Approver confirms security checklist: encryption enabled, secrets managed, no hardcoded credentials.
   - Approver documents approval in commit message or deployment log.

3. **Post-Deployment Validation**:
   - Automated smoke tests verify app health and API connectivity.
   - Error logs monitored for anomalies during initial run.

### Encryption & Secret Management (Constitution Principle III)

All sensitive data (API credentials, database connection strings) MUST:
- Be sourced from environment variables at runtime, never from version control.
- Support optional database encryption at rest (PostgreSQL pgcrypto or OS-level encryption).
- Use TLS/HTTPS for all external API calls and database connections.
- Be rotated periodically per organizational security policy.

## Project Structure

### Documentation (this feature)

```text
specs/001-etainabl-site-supply-sync/
├── plan.md
├── data-model.md
├── quickstart.md
├── contracts/
└── spec.md
```

### Source Code (repository root)

```text
django_app/
├── manage.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── sitesync/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── services.py
│   └── templates/
│       └── sitesync/
│           └── site_supply_list.html
└── requirements.txt

tests/
├── unit/
└── integration/
```

**Structure Decision**: Use a single Django project rooted in `django_app/` to host the backend, database models, sync services, and simple template-based UI. This avoids splitting frontend/backend while still enabling containerised deployment.

## Phase 0: Research

1. Confirm the Etainabl endpoints and authentication model using the sample `download_ref.py` and `download_data.py` logic.
2. Identify the exact response fields for asset and account records needed for `external_id`, site name, utility type, and device ID.
3. Determine the simplest container configuration that works under Windows without admin privileges (Docker Desktop or Windows container support for Django/PostgreSQL).
4. Validate secure handling of API keys via environment variables or mounted config files.

## Phase 1: Design & Contracts

1. Define Django models for `Site` and `Supply` in `django_app/sitesync/models.py`.
2. Create a sync service in `django_app/sitesync/services.py` that:
   - downloads assets and accounts from Etainabl
   - deduplicates by `external_id`
   - upserts database records
3. Define internal API contract expectations in `specs/001-etainabl-site-supply-sync/contracts/`.
4. Design the UI template for:
   - searchable site list
   - adjacent supply list with name, utility type, and device ID
5. Document quickstart validation commands in `specs/001-etainabl-site-supply-sync/quickstart.md`.

## Phase 2: Implementation Plan Output

### Key Implementation Milestones

- Setup Django project, PostgreSQL container, and Docker Compose.
- Implement `Site` and `Supply` models with unique `external_id` fields.
- Add sync service and helper to call Etainabl, parse JSON responses, and persist site/supply records.
- Implement a page that displays the searchable site list and selected site supplies.
- Add a manual refresh button and automatic initial sync hook.

### Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Agent Context

- This plan is written for a Django-based containerised web app that excludes user management in the initial release.
- The app will focus on Etainabl site and supply sync, database persistence, and a searchable display UI.

---

### Artifacts Generated

- `specs/001-etainabl-site-supply-sync/data-model.md`
- `specs/001-etainabl-site-supply-sync/quickstart.md`
- `specs/001-etainabl-site-supply-sync/contracts/README.md`

### Next Step

Run `/speckit.tasks` to generate the concrete implementation task list from this plan and the feature spec.
