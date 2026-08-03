from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, ReportWriteDelegationEvent, ReportWriteGrant, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportWriteDelegationConflictTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner_conf', email='owner_conf@example.com', password='pw123456')
        self.delegate = User.objects.create_user(username='delegate_conf', email='delegate_conf@example.com', password='pw123456')

        self.team = Team.objects.create(name='Conflict Team', level=1)
        self.site = Site.objects.create(external_id='site-conf-1', name='Conflict Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.delegate, team=self.team)

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def test_last_write_wins_for_grant_revoke_sequence_and_logs_events(self):
        self.client.force_login(self.owner)
        grant_1 = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        revoke = self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        grant_2 = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(grant_1.status_code, 200)
        self.assertEqual(revoke.status_code, 200)
        self.assertEqual(grant_2.status_code, 200)

        active_grant = ReportWriteGrant.objects.filter(
            report=self.report,
            granted_user=self.delegate,
            is_active=True,
        ).first()
        self.assertIsNotNone(active_grant)

        events = ReportWriteDelegationEvent.objects.filter(report=self.report, delegate_user=self.delegate)
        self.assertGreaterEqual(events.count(), 3)
        self.assertEqual(events.first().action, ReportWriteDelegationEvent.ACTION_GRANT)
