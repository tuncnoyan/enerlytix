"""Tests for the saved reports browser view."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, ReportWriteGrant, Site, Team, UserTeamAssignment
from sitesync.services import create_report_version, get_or_create_monthly_report


class SavedReportsViewTest(TestCase):
    """Validate saved reports list and open links."""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='savedreportsadmin',
            password='pass123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)
        self.site = Site.objects.create(
            external_id='site-ext-saved-1',
            name='Saved Reports Site',
            description='Saved reports demo site',
        )

    def _create_report(self, month, kind='draft'):
        report = get_or_create_monthly_report(self.site, month)
        create_report_version(
            report=report,
            version_kind=kind,
            comments={'overview': f'{month} note'},
            derived_from_version=None,
        )
        return report

    def test_saved_reports_page_renders_rows(self):
        self._create_report('2026-05', kind='final')
        self._create_report('2026-06', kind='draft')

        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Saved Reports')
        self.assertContains(response, '2026-05')
        self.assertContains(response, '2026-06')
        self.assertContains(response, 'final')
        self.assertContains(response, 'draft')

    def test_saved_reports_json_includes_open_url(self):
        self._create_report('2026-05', kind='final')

        response = self.client.get('/reports/?format=json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('reports', payload)
        self.assertEqual(len(payload['reports']), 1)
        row = payload['reports'][0]
        self.assertEqual(row['reporting_month'], '2026-05')
        self.assertIn('site_id=', row['open_url'])
        self.assertIn('end_month=2026-05', row['open_url'])


class SavedReportsDelegationModeConsistencyTest(TestCase):
    """Validate listing-to-editor access mode consistency for delegated users."""

    def setUp(self):
        self.client = Client()
        self.owner = get_user_model().objects.create_user(
            username='saved_owner',
            password='pass123',
        )
        self.delegate = get_user_model().objects.create_user(
            username='saved_delegate',
            password='pass123',
        )
        self.team = Team.objects.create(name='Saved Reports Team', level=1)
        self.site = Site.objects.create(
            external_id='site-ext-saved-delegation',
            name='Saved Delegation Site',
            description='Saved reports delegation demo site',
            team=self.team,
        )
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

    def test_listing_and_editor_show_collaborator_mode_for_active_delegate(self):
        ReportWriteGrant.objects.create(
            report=self.report,
            granted_user=self.delegate,
            granted_by=self.owner,
            is_active=True,
        )

        self.client.force_login(self.delegate)
        list_response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json'})
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()['reports']
        self.assertEqual(list_payload[0]['access_mode'], 'collaborator')

        editor_response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': str(self.site.id), 'end_month': self.report.reporting_month},
        )
        self.client.logout()

        self.assertEqual(editor_response.status_code, 200)
        self.assertEqual(editor_response.context['report_access_mode'], 'collaborator')

    def test_listing_and_editor_switch_to_read_only_after_revoke(self):
        grant = ReportWriteGrant.objects.create(
            report=self.report,
            granted_user=self.delegate,
            granted_by=self.owner,
            is_active=True,
        )
        grant.is_active = False
        grant.revoked_by = self.owner
        grant.revoked_at = timezone.now()
        grant.save(update_fields=['is_active', 'revoked_by', 'revoked_at'])

        self.client.force_login(self.delegate)
        list_response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json'})
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()['reports']
        self.assertEqual(list_payload[0]['access_mode'], 'read_only')

        editor_response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': str(self.site.id), 'end_month': self.report.reporting_month},
        )
        self.client.logout()

        self.assertEqual(editor_response.status_code, 200)
        self.assertEqual(editor_response.context['report_access_mode'], 'read_only')
