from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, ReportWriteGrant, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportCollaboratorGrantTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner2', email='owner2@example.com', password='pw123456')
        self.collaborator = User.objects.create_user(username='collab2', email='collab2@example.com', password='pw123456')
        self.team = Team.objects.create(name='Grant Team', level=1)
        self.site = Site.objects.create(external_id='site-grant-1', name='Grant Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.collaborator, team=self.team)
        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def _save_as(self, user):
        self.client.force_login(user)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-07',
                'save_mode': 'draft',
                'comments': '{"overview-table": "granted"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        return response

    def test_owner_grant_then_revoke_collaborator_write(self):
        self.client.force_login(self.owner)
        grant_response = self.client.post(
            reverse('sitesync:report_grant_write_access', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.collaborator.id)},
        )
        self.client.logout()

        self.assertEqual(grant_response.status_code, 200)
        self.assertTrue(
            ReportWriteGrant.objects.filter(
                report=self.report,
                granted_user=self.collaborator,
                is_active=True,
            ).exists()
        )

        collaborator_save = self._save_as(self.collaborator)
        self.assertEqual(collaborator_save.status_code, 200)

        self.client.force_login(self.owner)
        revoke_response = self.client.post(
            reverse('sitesync:report_revoke_write_access', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.collaborator.id)},
        )
        self.client.logout()

        self.assertEqual(revoke_response.status_code, 200)
        self.assertFalse(
            ReportWriteGrant.objects.filter(
                report=self.report,
                granted_user=self.collaborator,
                is_active=True,
            ).exists()
        )

        collaborator_denied = self._save_as(self.collaborator)
        self.assertEqual(collaborator_denied.status_code, 403)
