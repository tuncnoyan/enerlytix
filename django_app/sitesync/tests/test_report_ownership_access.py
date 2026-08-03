from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site


User = get_user_model()


class ReportOwnershipAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='pw123456')
        self.other = User.objects.create_user(username='other', email='other@example.com', password='pw123456')
        self.site = Site.objects.create(external_id='site-ownership-1', name='Ownership Site')

    def _save_report(self, user, *, month='2026-07', comments=None):
        self.client.force_login(user)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': month,
                'save_mode': 'draft',
                'comments': comments or '{"overview-table": "alpha"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        return response

    def test_owner_write_and_non_owner_denied(self):
        owner_response = self._save_report(self.owner)
        self.assertEqual(owner_response.status_code, 200)

        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-07')
        self.assertEqual(report.owner_user_id, self.owner.id)
        self.assertEqual(report.versions.count(), 1)

        denied_response = self._save_report(self.other)
        self.assertEqual(denied_response.status_code, 403)

        report.refresh_from_db()
        self.assertEqual(report.owner_user_id, self.owner.id)
        self.assertEqual(report.versions.count(), 1)

    def test_submit_time_permission_check_has_no_partial_write(self):
        owner_response = self._save_report(self.owner, comments='{"overview-table": "first"}')
        self.assertEqual(owner_response.status_code, 200)

        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-07')
        original_version_id = report.current_version_id
        original_count = report.versions.count()

        denied_response = self._save_report(self.other, comments='{"overview-table": "intrusion"}')
        self.assertEqual(denied_response.status_code, 403)

        report.refresh_from_db()
        self.assertEqual(report.current_version_id, original_version_id)
        self.assertEqual(report.versions.count(), original_count)

    def test_read_only_page_disables_save_actions_and_shows_top_label(self):
        owner_response = self._save_report(self.owner)
        self.assertEqual(owner_response.status_code, 200)

        self.client.force_login(self.other)
        response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': str(self.site.id), 'end_month': '2026-07'},
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Read Only')
        self.assertContains(response, 'id="save-draft-button"', html=False)
        self.assertContains(response, 'id="save-final-button"', html=False)
        self.assertContains(response, 'id="save-draft-button" class="button button-primary" type="button" disabled', html=False)
        self.assertContains(response, 'id="save-final-button" class="button button-secondary" type="button" disabled', html=False)
