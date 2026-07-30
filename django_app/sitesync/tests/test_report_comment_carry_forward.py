"""Tests for previous-month final comment carry-forward behavior."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase

from sitesync.models import MonthlyReport, ReportComment, Site
from sitesync.services import create_report_version, get_or_create_monthly_report
from sitesync.views import report_view


class ReportCommentCarryForwardTest(TestCase):
    """Validate copy-forward behavior from previous month final reports."""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='carryuser', password='pass123')
        self.client.force_login(self.user)
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

    def test_opening_new_month_previews_previous_final_comments_before_save(self):
        self._create_previous_month_final_with_comment()

        request = self.factory.get(
            '/report/',
            data={'site_id': str(self.site.id), 'end_month': '2026-06'},
        )
        request.user = self.user
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyReport.objects.filter(site=self.site, reporting_month='2026-06').count(), 0)

        content = response.content.decode('utf-8')
        self.assertIn('Previous final note', content)
        self.assertIn('overview', content)

    def test_saving_edited_reference_comment_is_not_retagged(self):
        self._create_previous_month_final_with_comment()

        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-06',
                'save_mode': 'draft',
                'comments': json.dumps({'overview': 'Edited note for June'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-06')
        comment = ReportComment.objects.get(report_version=report.current_version, visual_key='overview')
        self.assertEqual(comment.text, 'Edited note for June')
        self.assertFalse(comment.is_reference_copy)
