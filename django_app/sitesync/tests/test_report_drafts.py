"""Tests for monthly report draft save and reopen workflow."""

import json

from django.test import Client, TestCase

from sitesync.models import MonthlyReport, MonthlyReportVersion, Site


class ReportDraftWorkflowTest(TestCase):
    """Validate draft save and single-report-per-month behavior."""

    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(
            external_id='site-ext-1',
            name='Test Site',
            description='Demo site',
        )

    def test_post_report_creates_draft_report_for_site_month(self):
        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
                'comments': json.dumps({'overview': 'Draft note'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyReport.objects.count(), 1)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_status, MonthlyReport.STATUS_DRAFT)
        self.assertIsNotNone(report.current_version)
        self.assertEqual(report.current_version.version_kind, MonthlyReportVersion.KIND_DRAFT)

    def test_post_report_reuses_existing_site_month_identity(self):
        first = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(second.status_code, 200)

        self.assertEqual(MonthlyReport.objects.count(), 1)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.versions.count(), 2)

    def test_get_report_supports_reporting_month_alias_for_end_month(self):
        response = self.client.get(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'reporting_month': '2026-05',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"endMonth": "2026-05"')
