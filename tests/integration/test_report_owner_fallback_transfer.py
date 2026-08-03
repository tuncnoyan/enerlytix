from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import (
    MonthlyReport,
    ReportOwnershipTransferEvent,
    ReportWriteGrant,
    RoleAssignment,
    Site,
    Team,
    UserTeamAssignment,
)


User = get_user_model()


class ReportOwnerFallbackTransferTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner3', email='owner3@example.com', password='pw123456')
        self.approver = User.objects.create_user(username='approver3', email='approver3@example.com', password='pw123456')
        self.manager = User.objects.create_user(username='manager3', email='manager3@example.com', password='pw123456')
        self.scoped_admin = User.objects.create_user(username='admin3', email='admin3@example.com', password='pw123456')

        self.team = Team.objects.create(name='Scope Team', level=1, team_lead=self.approver, manager=self.manager)
        self.site = Site.objects.create(external_id='site-fallback-1', name='Fallback Site', team=self.team)
        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.approver, team=self.team)
        UserTeamAssignment.objects.create(user=self.manager, team=self.team)
        UserTeamAssignment.objects.create(user=self.scoped_admin, team=self.team)

        RoleAssignment.objects.create(user=self.approver, role_name='team_lead')
        RoleAssignment.objects.create(user=self.manager, role_name='manager')
        RoleAssignment.objects.create(user=self.scoped_admin, role_name='admin')

    def test_fallback_transfer_keeps_previous_owner_as_collaborator(self):
        self.client.force_login(self.approver)
        response = self.client.post(
            reverse('sitesync:report_approve_unavailable_owner', kwargs={'report_id': self.report.id}),
            {
                'owner_user_id': str(self.owner.id),
                'reason': 'Owner is unavailable for the month-end handover',
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)

        self.report.refresh_from_db()
        self.assertEqual(self.report.owner_user_id, self.approver.id)
        self.assertTrue(
            ReportWriteGrant.objects.filter(
                report=self.report,
                granted_user=self.owner,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            ReportOwnershipTransferEvent.objects.filter(
                report=self.report,
                from_owner=self.owner,
                to_owner=self.approver,
                transfer_mode=ReportOwnershipTransferEvent.MODE_AUTO_FALLBACK,
            ).exists()
        )

    def test_cross_scope_admin_is_rejected_from_fallback_candidates(self):
        self.team.team_lead = self.owner
        self.team.manager = None
        self.team.save(update_fields=['team_lead', 'manager'])
        self.scoped_admin.is_active = False
        self.scoped_admin.save(update_fields=['is_active'])

        other_team = Team.objects.create(name='Other Scope Team', level=1)
        out_of_scope_admin = User.objects.create_user(
            username='other_admin3',
            email='other_admin3@example.com',
            password='pw123456',
        )
        UserTeamAssignment.objects.create(user=out_of_scope_admin, team=other_team)
        RoleAssignment.objects.create(user=out_of_scope_admin, role_name='admin')

        self.client.force_login(self.approver)
        response = self.client.post(
            reverse('sitesync:report_approve_unavailable_owner', kwargs={'report_id': self.report.id}),
            {
                'owner_user_id': str(self.owner.id),
                'reason': 'Fallback should reject out-of-scope admin',
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 400)
        self.report.refresh_from_db()
        self.assertEqual(self.report.owner_user_id, self.owner.id)
