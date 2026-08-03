from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from sitesync.models import (
    MonthlyReport,
    ReportWriteGrant,
    RoleAssignment,
    Site,
    Team,
    UserTeamAssignment,
)
from sitesync.services import approve_owner_unavailability_and_transfer, get_accessible_reports


User = get_user_model()


class ReportScopeConvergenceTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username='scope_viewer', email='scope_viewer@example.com', password='pw123456')
        self.owner = User.objects.create_user(username='scope_owner', email='scope_owner@example.com', password='pw123456')
        self.outsider = User.objects.create_user(username='scope_outsider', email='scope_outsider@example.com', password='pw123456')
        self.team_lead = User.objects.create_user(username='scope_lead', email='scope_lead@example.com', password='pw123456')

        self.team = Team.objects.create(name='Convergence Team', level=1, team_lead=self.team_lead)
        UserTeamAssignment.objects.create(user=self.viewer, team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        RoleAssignment.objects.create(user=self.team_lead, role_name='team_lead')

    def test_null_team_reports_are_not_globally_visible(self):
        scoped_site = Site.objects.create(external_id='scope-site-1', name='Scoped Site', team=self.team)
        null_team_site = Site.objects.create(external_id='scope-site-2', name='Legacy Null Team Site')

        scoped_report = MonthlyReport.objects.create(
            site=scoped_site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )
        unauthorized_null_report = MonthlyReport.objects.create(
            site=null_team_site,
            reporting_month='2026-06',
            owner_user=self.outsider,
            created_by_user=self.outsider,
            last_modified_by_user=self.outsider,
            last_modified_at=timezone.now(),
        )
        authorized_null_report = MonthlyReport.objects.create(
            site=null_team_site,
            reporting_month='2026-05',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )
        ReportWriteGrant.objects.create(
            report=authorized_null_report,
            granted_user=self.viewer,
            granted_by=self.owner,
            is_active=True,
        )

        visible_ids = set(get_accessible_reports(self.viewer).values_list('id', flat=True))
        self.assertIn(scoped_report.id, visible_ids)
        self.assertIn(authorized_null_report.id, visible_ids)
        self.assertNotIn(unauthorized_null_report.id, visible_ids)

    def test_fallback_transfer_requires_site_team_scope(self):
        null_team_site = Site.objects.create(external_id='scope-site-3', name='No Scope Site')
        report = MonthlyReport.objects.create(
            site=null_team_site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

        with self.assertRaises(LookupError):
            approve_owner_unavailability_and_transfer(
                report=report,
                owner_user=self.owner,
                approved_by=self.team_lead,
                reason='Owner unavailable and fallback requested',
            )

        report.refresh_from_db()
        self.assertEqual(report.owner_user_id, self.owner.id)
