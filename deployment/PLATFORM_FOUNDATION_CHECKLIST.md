# Deployment Checklist: Platform Foundation (T094)

**Feature**: Platform Foundation (Authentication, Teams, Admin Panel, Report Access)  
**Version**: 1.0  
**Prerequisite**: All phases (1-7) complete, all tests passing  
**Last Updated**: 2026-07-29

---

## Pre-Deployment: Test Validation

### Automated Tests
- [ ] Run full test suite in Docker and confirm all 110 tests pass:
  ```bash
  powershell .specify/scripts/powershell/test-integration.ps1 -Verbosity 0
  ```
  **Expected output**: `Ran 110 tests OK`

- [ ] Capture test results for deployment record:
  ```bash
  docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test --verbosity 2 2>&1 | Out-File tests/test_results_$(Get-Date -Format "yyyy-MM-dd").txt
  ```

### Integration Test Coverage
Verify each phase has passing tests:
- [ ] Phase 1 (Auth): `tests.integration.test_auth_flow` ✓
- [ ] Phase 2 (Invitations): `tests.integration.test_invitations` ✓
- [ ] Phase 3 (User Admin): `tests.integration.test_user_admin` ✓
- [ ] Phase 4 (Teams): `tests.integration.test_team_hierarchy_full` ✓
- [ ] Phase 5 (Admin Panel): `tests.integration.test_admin_panel_full` ✓
- [ ] Phase 6 (Report Access): `tests.integration.test_report_access_team` ✓
- [ ] Phase 7 (E2E): `tests.integration.test_load_hierarchy` ✓
- [ ] Validation workflow: `sitesync.tests.test_report_validation_end_to_end` ✓

---

## Pre-Deployment: Manual Validation

### User Stories Sign-Off
Complete manual validation per [MANUAL_VALIDATION.md](../specs/008-platform-foundation/MANUAL_VALIDATION.md):
- [ ] US1 Authentication and Account Management: PASS
- [ ] US2 Invitation-Based Onboarding: PASS
- [ ] US3 User Administration and Roles: PASS
- [ ] US4 Team Hierarchy and Multi-Team Assignment: PASS
- [ ] US5 Consolidated Admin Panel: PASS
- [ ] US6 Report Access Scoping: PASS

**Manual Validation Sign-Off**:  
Validated by: _________________ Date: _______ Result: ☐ PASS / ☐ FAIL

---

## Pre-Deployment: Database Verification

### Migration Status
- [ ] All migrations applied in staging:
  ```bash
  docker compose exec -T web python manage.py showmigrations sitesync
  ```
  Expected: All migrations marked [X]

- [ ] No pending migrations exist:
  ```bash
  docker compose exec -T web python manage.py migrate --check
  ```
  Expected: `No migrations to apply`

### Schema Verification
- [ ] Team model exists with hierarchy FK
- [ ] UserTeamAssignment model with unique constraint
- [ ] RoleAssignment model with role choices
- [ ] Invitation model with 7-day expiry logic

### Database Backup
- [ ] Create full PostgreSQL backup before migration:
  ```bash
  docker compose exec postgres pg_dump -U postgres django_app > backup_$(Get-Date -Format "yyyy-MM-dd")_pre_platform_foundation.sql
  ```

---

## Pre-Deployment: Security Checklist

### Authentication
- [ ] `DEBUG = False` in production settings
- [ ] `SECRET_KEY` is unique and from environment variable (not hardcoded)
- [ ] `ALLOWED_HOSTS` contains only production domain names
- [ ] Session cookie set to `Secure` (HTTPS only)
- [ ] Session cookie set to `HttpOnly`
- [ ] CSRF cookie secure flag enabled

### Access Control
- [ ] All admin panel views protected by `@admin_panel_required` decorator
- [ ] All team management views require login
- [ ] Role assignment views require admin check
- [ ] No anonymous access to user/team/role management endpoints
- [ ] 403 responses for unauthorized requests (not 500 or 200)
- [ ] Pen-test sensitive endpoint baseline enforced:
  - [ ] `POST /api/consumption-import/` returns 401 when unauthenticated and 403 for non-admin
  - [ ] `GET /api/consumption-display/` returns 401 when unauthenticated
  - [ ] `GET /api/report-data/` returns 401 when unauthenticated
  - [ ] `GET /api/import-runs/{import_run_id}/` returns 401 when unauthenticated
  - [ ] `POST /sync/` returns 401 when unauthenticated and 403 for non-admin
  - [ ] `POST /settings/` mutation paths return 401 when unauthenticated and 403 for non-admin
  - [ ] `GET /settings/capacity-upload/results.xlsx` returns 401 when unauthenticated and 403 for non-admin

### Data Protection
- [ ] No passwords or tokens in server logs
- [ ] No sensitive data in admin panel HTML source
- [ ] Database connections using SSL (PostgreSQL SSL mode)
- [ ] Invitation tokens are URL-safe random strings (not sequential IDs)

### Input Validation
- [ ] All forms using Django's CSRF middleware
- [ ] Email validation in InvitationForm
- [ ] File upload validation in CapacityUploadForm (xlsx only)
- [ ] Team name length limits enforced (max 255 chars)
- [ ] Role name choices limited to valid values (admin/manager/team_lead/user)

---

## Pre-Deployment: Configuration

### Environment Variables
- [ ] Verify production .env or environment settings contain:
  ```
  SECRET_KEY=<production-secret-key>
  DATABASE_URL=<production-db-url>
  DEBUG=False
  ALLOWED_HOSTS=<your-domain.com>
  EMAIL_HOST=<smtp-host>
  EMAIL_PORT=587
  EMAIL_HOST_USER=<email-user>
  EMAIL_HOST_PASSWORD=<email-password>
  ```

### Static Files
- [ ] Run collectstatic:
  ```bash
  docker compose exec -T web python manage.py collectstatic --noinput
  ```
- [ ] Verify static files served correctly (CSS, JS, images load)
- [ ] Admin panel CSS (`panel.css`) loads correctly

### Media Files
- [ ] Media storage configured for production (S3 or similar)
- [ ] Upload directories have correct permissions

---

## Deployment Steps

### Step 1: Pre-Deployment Backup
```bash
# 1. Create DB backup
docker compose exec postgres pg_dump -U postgres django_app > backup_pre_deploy.sql

# 2. Tag current version in git
git tag -a v1.0.0-pre-platform-foundation -m "Backup before Platform Foundation deployment"
git push origin v1.0.0-pre-platform-foundation
```

### Step 2: Deploy Application
```bash
# 1. Pull latest code
git pull origin main

# 2. Build Docker image
docker compose build web

# 3. Apply migrations (this is reversible up to this point)
docker compose exec -T web python manage.py migrate

# 4. Collect static files
docker compose exec -T web python manage.py collectstatic --noinput

# 5. Restart web service
docker compose restart web
```

### Step 3: Post-Deployment Verification
```bash
# 1. Verify application is running
curl http://localhost:8000/ -I  # Should return 302 or 200

# 2. Verify login works
# Open browser: http://localhost:8000/login/
# Login with admin credentials

# 3. Run smoke test
docker compose exec -T web python manage.py test tests.integration.test_auth_flow --verbosity 2

# 4. Verify admin panel
# Open browser: http://localhost:8000/admin-panel/
```

### Step 4: Admin User Setup
```bash
# 1. Create admin user (if not exists)
docker compose exec -T web python manage.py createsuperuser

# 2. Verify Django admin still works (if needed)
# Open browser: http://localhost:8000/django-admin/
```

---

## Post-Deployment: Validation

### Smoke Tests (5 minutes)
- [ ] Application accessible: `http://your-domain.com/`
- [ ] Login page loads
- [ ] Admin can login
- [ ] Admin panel accessible: `/admin-panel/`
- [ ] Teams section loads
- [ ] Users section loads
- [ ] Roles section loads

### Functional Tests (15 minutes)
- [ ] Create a new team via admin panel
- [ ] Invite a test user via user admin
- [ ] Accept invitation (from new browser session)
- [ ] Assign test user to team
- [ ] Verify test user can see team reports
- [ ] Verify test user sees empty state before assignment
- [ ] Verify non-admin cannot access admin panel

### Performance Checks (5 minutes)
- [ ] Admin panel dashboard loads in < 2 seconds
- [ ] Team hierarchy view loads in < 2 seconds
- [ ] User list (100+ users) loads in < 1 second
- [ ] Report access filtering completes in < 500ms

---

## Rollback Plan

### Quick Rollback (if needed within 1 hour)
```bash
# 1. Revert migrations
docker compose exec -T web python manage.py migrate sitesync 0013  # Reverts team/role tables

# 2. Redeploy previous version
git checkout v1.0.0-pre-platform-foundation
docker compose build web
docker compose restart web

# 3. Verify rollback
curl http://localhost:8000/login/  # Should work
```

### Full Rollback (if database integrity compromised)
```bash
# 1. Stop application
docker compose stop web

# 2. Restore database backup
docker compose exec postgres psql -U postgres -c "DROP DATABASE django_app"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE django_app"
docker compose exec postgres psql -U postgres django_app < backup_pre_deploy.sql

# 3. Deploy previous version
git checkout v1.0.0-pre-platform-foundation
docker compose build web
docker compose start web

# 4. Verify restoration
docker compose exec -T web python manage.py test tests.integration.test_auth_flow
```

---

## Post-Deployment Monitoring (First 24 Hours)

### Monitor These Logs
```bash
# Application logs
docker compose logs -f web | Select-String "ERROR|WARNING"

# Access logs
docker compose logs -f nginx | Select-String "4[0-9][0-9]|5[0-9][0-9]"
```

### Alert Thresholds
- [ ] Error rate > 1%: Investigate immediately
- [ ] Response time > 5 seconds: Performance investigation
- [ ] Login failures > 20/minute: Possible brute-force attack
- [ ] 403 errors > 50/minute: Possible unauthorized access attempts

---

## Documentation Sign-Off

Verify all Phase 7 documentation is complete and accessible:
- [ ] [data-model.md](../specs/008-platform-foundation/data-model.md): Schema finalized
- [ ] [ADMIN_GUIDE.md](../specs/008-platform-foundation/ADMIN_GUIDE.md): Admin guide complete
- [ ] [quickstart.md](../specs/008-platform-foundation/quickstart.md): Quick start scenarios documented
- [ ] [MANUAL_VALIDATION.md](../specs/008-platform-foundation/MANUAL_VALIDATION.md): Manual validation checklist ready
- [ ] [contracts/team-management.md](../specs/008-platform-foundation/contracts/team-management.md): API docs complete
- [ ] This deployment checklist: Complete

---

## Deployment Approval

**Pre-Deployment Checklist Review**:
- [ ] All tests passing (110/110)
- [ ] Manual validation sign-off
- [ ] Security checklist reviewed
- [ ] Database backup taken
- [ ] Rollback plan documented

**Deployment Approved By**: _________________  
**Approval Date**: _________________  
**Deployment Date**: _________________  
**Deployed By**: _________________  
**Release Tag**: `v1.0.0-platform-foundation`

**Deployment Result**: ☐ SUCCESS  ☐ PARTIAL  ☐ FAILURE (rollback executed)

**Post-Deployment Notes**:
____________________________________________________________________________
____________________________________________________________________________
