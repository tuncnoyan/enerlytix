"""Tests for report validation comment persistence."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, ReportValidationComment, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, mark_report_page_validation_state, get_or_create_monthly_report


User = get_user_model()


class ReportValidationCommentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='comment_owner', password='pass123')
        self.validator = User.objects.create_user(username='comment_validator', password='pass123')
        self.team = Team.objects.create(name='Comment Team', level=1)
        self.site = Site.objects.create(external_id='site-comment-1', name='Comment Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)

        self.report = get_or_create_monthly_report(self.site, '2026-07', actor_user=self.owner)
        create_report_version(
            report=self.report,
            version_kind='draft',
            comments={
                'overview-table': 'Alpha',
                'usage-chart': 'Beta',
            },
            derived_from_version=None,
            actor_user=self.owner,
        )
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)
        mark_report_page_validation_state(report=self.report, page_key='overview-table', is_validated=True, actor_user=self.validator)
        mark_report_page_validation_state(report=self.report, page_key='usage-chart', is_validated=True, actor_user=self.validator)

    def test_validation_comments_persist_without_clearing_validated_pages(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-07',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
                'validation_comments': json.dumps({
                    'overview-table': 'Please check the totals again.',
                    'usage-chart': 'Looks consistent.',
                }),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)
        self.assertEqual(ReportValidationComment.objects.filter(report=self.report).count(), 2)
        self.assertEqual(
            ReportValidationComment.objects.get(report=self.report, page_key='overview-table', authored_by_user=self.owner).comment_text,
            'Please check the totals again.',
        )
        self.assertTrue(self.report.page_validation_states.get(page_key='overview-table').is_validated)
        self.assertTrue(self.report.page_validation_states.get(page_key='usage-chart').is_validated)

    def test_assigned_validator_can_save_draft_with_validation_comments(self):
        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-07',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
                'validation_comments': json.dumps({
                    'overview-table': 'Validator note.',
                }),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['access_mode'], 'validator')
        self.assertEqual(
            ReportValidationComment.objects.get(report=self.report, page_key='overview-table', authored_by_user=self.validator).comment_text,
            'Validator note.',
        )
