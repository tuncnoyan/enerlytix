"""Tests for validation reset rules."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, ReportPageValidationState, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report, mark_report_page_validation_state


User = get_user_model()


class ReportValidationResetRulesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='reset_owner', password='pass123')
        self.validator = User.objects.create_user(username='reset_validator', password='pass123')
        self.reassigned_validator = User.objects.create_user(username='reset_validator_two', password='pass123')
        self.team = Team.objects.create(name='Reset Team', level=1)
        self.site = Site.objects.create(external_id='site-reset-1', name='Reset Site', team=self.team)
        for user in [self.owner, self.validator, self.reassigned_validator]:
            UserTeamAssignment.objects.create(user=user, team=self.team)

        self.report = get_or_create_monthly_report(self.site, '2026-10', actor_user=self.owner)
        create_report_version(
            report=self.report,
            version_kind='draft',
            comments={'overview-table': 'Alpha', 'usage-chart': 'Beta'},
            derived_from_version=None,
            actor_user=self.owner,
        )
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)
        mark_report_page_validation_state(report=self.report, page_key='overview-table', is_validated=True, actor_user=self.validator)
        mark_report_page_validation_state(report=self.report, page_key='usage-chart', is_validated=True, actor_user=self.validator)

    def test_validation_comment_only_save_does_not_clear_page_validation(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-10',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
                'validation_comments': json.dumps({'overview-table': 'Comment edit only'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)
        self.assertTrue(ReportPageValidationState.objects.get(report=self.report, page_key='overview-table').is_validated)
        self.assertTrue(ReportPageValidationState.objects.get(report=self.report, page_key='usage-chart').is_validated)

    def test_validator_reassignment_resets_all_pages(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.reassigned_validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(ReportPageValidationState.objects.filter(report=self.report, is_validated=True).count(), 0)
        self.assertEqual(self.report.validator_user_id, self.reassigned_validator.id)
