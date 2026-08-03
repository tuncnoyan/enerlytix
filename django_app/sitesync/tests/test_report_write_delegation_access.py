from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, ReportWriteGrant, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportWriteDelegationAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner_wd', email='owner_wd@example.com', password='pw123456')
        self.delegate = User.objects.create_user(username='delegate_wd', email='delegate_wd@example.com', password='pw123456')
        self.viewer = User.objects.create_user(username='viewer_wd', email='viewer_wd@example.com', password='pw123456')

        self.team = Team.objects.create(name='Delegation Team', level=1)
        self.site = Site.objects.create(external_id='site-wd-1', name='Delegation Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.delegate, team=self.team)
        UserTeamAssignment.objects.create(user=self.viewer, team=self.team)

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def _save_as(self, user, comment='delegated write'):
        self.client.force_login(user)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-07',
                'save_mode': 'draft',
                'comments': '{"overview-table": "%s"}' % comment,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        return response

    def test_owner_grants_delegate_and_revoke_blocks_submit_time_save(self):
        self.client.force_login(self.owner)
        grant_response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(grant_response.status_code, 200)
        self.assertTrue(
            ReportWriteGrant.objects.filter(report=self.report, granted_user=self.delegate, is_active=True).exists()
        )

        delegated_save = self._save_as(self.delegate, comment='active-grant')
        self.assertEqual(delegated_save.status_code, 200)

        self.client.force_login(self.owner)
        revoke_response = self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(revoke_response.status_code, 200)
        denied_save = self._save_as(self.delegate, comment='after-revoke')
        self.assertEqual(denied_save.status_code, 403)

    def test_delegate_becomes_out_of_scope_and_loses_submit_time_write_access(self):
        self.client.force_login(self.owner)
        grant_response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(grant_response.status_code, 200)

        UserTeamAssignment.objects.filter(user=self.delegate, team=self.team).delete()

        denied_save = self._save_as(self.delegate, comment='out-of-scope-delegate')
        self.assertEqual(denied_save.status_code, 403)

    def test_revoked_between_open_and_save_is_denied(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.client.force_login(self.delegate)
        open_response = self.client.get(reverse('sitesync:report'), {'site_id': str(self.site.id), 'end_month': '2026-07'})
        self.client.logout()
        self.assertEqual(open_response.status_code, 200)

        self.client.force_login(self.owner)
        self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        denied_save = self._save_as(self.delegate, comment='revoked-after-open')
        self.assertEqual(denied_save.status_code, 403)
