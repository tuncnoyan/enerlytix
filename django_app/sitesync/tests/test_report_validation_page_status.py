"""Tests for report page validation status behavior."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, ReportPageValidationState, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report


User = get_user_model()


class ReportValidationPageStatusTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='page_owner', password='pass123')
        self.validator = User.objects.create_user(username='page_validator', password='pass123')
        self.other_user = User.objects.create_user(username='page_other', password='pass123')
        self.team = Team.objects.create(name='Page Validation Team', level=1)
        self.site = Site.objects.create(external_id='site-page-validation-1', name='Page Validation Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)
        UserTeamAssignment.objects.create(user=self.other_user, team=self.team)

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

    def test_assigned_validator_can_mark_pages_and_complete_validation(self):
        self.client.force_login(self.validator)

        first = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        second = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'usage-chart'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)
        self.assertEqual(self.report.validated_by_user_id, self.validator.id)
        self.assertIsNotNone(self.report.validated_at)
        states = ReportPageValidationState.objects.filter(report=self.report)
        self.assertEqual(states.filter(is_validated=True).count(), 2)

    def test_non_validator_cannot_mark_pages(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(ReportPageValidationState.objects.filter(report=self.report, is_validated=True).count(), 0)

    def test_business_content_edit_resets_validated_page(self):
        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.owner)
        save_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-07',
                'save_mode': 'draft',
                'comments': '{"overview-table": "Alpha changed", "usage-chart": "Beta"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(save_response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(ReportPageValidationState.objects.filter(report=self.report, page_key='overview-table', is_validated=True).count(), 0)
        self.assertEqual(ReportPageValidationState.objects.filter(report=self.report, page_key='usage-chart', is_validated=True).count(), 0)

    def test_validator_can_mark_page_when_report_has_no_comment_keys(self):
        empty_report = get_or_create_monthly_report(self.site, '2026-08', actor_user=self.owner)
        assign_report_validator(report=empty_report, validator_user=self.validator, assigned_by_user=self.owner)

        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': empty_report.id, 'page_key': '120001016371'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        empty_report.refresh_from_db()
        self.assertEqual(empty_report.page_validation_states.filter(page_key='120001016371', is_validated=True).count(), 1)

    def test_one_checked_page_does_not_mark_all_known_pages_validated(self):
        empty_report = get_or_create_monthly_report(self.site, '2026-09', actor_user=self.owner)
        assign_report_validator(report=empty_report, validator_user=self.validator, assigned_by_user=self.owner)

        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': empty_report.id, 'page_key': 'page-a'}),
            {
                'is_validated': 'true',
                'known_page_keys': '["page-a", "page-b"]',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['validation_summary']['validated_page_count'], 1)
        self.assertEqual(payload['validation_summary']['total_page_count'], 2)
        self.assertEqual(payload['validation_summary']['validation_status'], MonthlyReport.VALIDATION_AWAITING)
        empty_report.refresh_from_db()
        self.assertEqual(empty_report.page_validation_states.filter(is_validated=True).count(), 1)
