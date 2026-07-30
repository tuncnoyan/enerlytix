"""Tests for the saved reports browser view."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from sitesync.models import Site
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
