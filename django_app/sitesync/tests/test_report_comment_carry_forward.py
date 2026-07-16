"""Tests for previous-month final comment carry-forward behavior."""

from django.test import Client, TestCase

from sitesync.models import MonthlyReport, ReportComment, Site
from sitesync.services import create_report_version, get_or_create_monthly_report


class ReportCommentCarryForwardTest(TestCase):
    """Validate copy-forward behavior from previous month final reports."""

    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(
            external_id='site-ext-carry-1',
            name='Carry Forward Site',
            description='Carry-forward demo',
        )

    def _create_previous_month_final_with_comment(self):
        previous_report = get_or_create_monthly_report(self.site, '2026-05')
        previous_final = create_report_version(
            report=previous_report,
            version_kind='final',
            comments={'overview': 'Previous final note'},
            derived_from_version=None,
        )
        return previous_report, previous_final

    def test_new_month_draft_copies_previous_final_comments(self):
        _, previous_final = self._create_previous_month_final_with_comment()

        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-06',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-06')
        self.assertIsNotNone(report.current_version)
        comments = ReportComment.objects.filter(report_version=report.current_version)
        self.assertEqual(comments.count(), 1)
        comment = comments.first()
        self.assertEqual(comment.visual_key, 'overview')
        self.assertEqual(comment.text, 'Previous final note')
        self.assertTrue(comment.is_reference_copy)
        self.assertEqual(comment.source_reporting_month, '2026-05')
        self.assertEqual(comment.source_version_id, previous_final.id)

    def test_new_month_draft_has_no_copied_comments_without_previous_final(self):
        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-06',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-06')
        self.assertEqual(ReportComment.objects.filter(report_version=report.current_version).count(), 0)
