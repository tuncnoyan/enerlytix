from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportWriteDelegationVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner_vis', email='owner_vis@example.com', password='pw123456')
        self.delegate = User.objects.create_user(username='delegate_vis', email='delegate_vis@example.com', password='pw123456')
        self.reader = User.objects.create_user(username='reader_vis', email='reader_vis@example.com', password='pw123456')

        self.team = Team.objects.create(name='Visibility Team', level=1)
        self.site = Site.objects.create(external_id='site-vis-1', name='Visibility Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.delegate, team=self.team)
        UserTeamAssignment.objects.create(user=self.reader, team=self.team)

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def test_read_access_user_can_view_active_delegations(self):
        self.client.force_login(self.owner)
        grant_response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(grant_response.status_code, 200)

        self.client.force_login(self.reader)
        response = self.client.get(reverse('sitesync:report_delegations', kwargs={'report_id': self.report.id}))
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()['delegations']
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['delegate_user'], self.delegate.username)
        self.assertEqual(payload[0]['granted_by_user'], self.owner.username)

    def test_revoked_delegate_not_returned_in_active_list(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.client.force_login(self.reader)
        response = self.client.get(reverse('sitesync:report_delegations', kwargs={'report_id': self.report.id}))
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()['delegations']
        self.assertEqual(payload, [])
