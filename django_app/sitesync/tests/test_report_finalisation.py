"""Tests for monthly report finalisation and replacement-final workflow."""

from django.test import Client, TestCase

from sitesync.models import MonthlyReport, MonthlyReportVersion, Site


class ReportFinalisationWorkflowTest(TestCase):
    """Validate final save and warning-before-revision behavior."""

    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(
            external_id='site-ext-final-1',
            name='Final Test Site',
            description='Finalization demo site',
        )

    def test_can_save_report_as_final(self):
        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertIsNotNone(report.current_final_version)
        self.assertEqual(report.current_final_version.version_kind, MonthlyReportVersion.KIND_FINAL)

    def test_editing_existing_final_requires_warning_confirmation(self):
        self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        warning = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(warning.status_code, 409)
        self.assertEqual(MonthlyReportVersion.objects.count(), 1)

    def test_confirmed_final_edit_creates_replacement_final_version(self):
        self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        original_final = report.current_final_version

        confirmed = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
                'confirm_final_edit': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(confirmed.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertIsNotNone(report.current_final_version)
        self.assertNotEqual(report.current_final_version.id, original_final.id)
        self.assertEqual(report.current_final_version.version_kind, MonthlyReportVersion.KIND_REPLACEMENT_FINAL)
        self.assertEqual(MonthlyReportVersion.objects.filter(report=report).count(), 2)
