"""Tests for the report final-save validation gate."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report


User = get_user_model()


class ReportValidationFinalGateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='final_owner', password='pass123')
        self.validator = User.objects.create_user(username='final_validator', password='pass123')
        self.team = Team.objects.create(name='Final Gate Team', level=1)
        self.site = Site.objects.create(external_id='site-final-gate-1', name='Final Gate Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)

        self.report = get_or_create_monthly_report(self.site, '2026-08', actor_user=self.owner)
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

    def test_final_save_is_blocked_until_all_pages_are_validated(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'final',
                'comments': '{"overview-table": "Alpha", "usage-chart": "Beta"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertFalse(payload['can_save_final'])
        self.assertEqual(payload['validation_status'], MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(payload['validated_page_count'], 0)
        self.assertEqual(payload['total_page_count'], 2)

    def test_final_save_succeeds_after_full_validation(self):
        self.client.force_login(self.validator)
        self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'usage-chart'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'final',
                'comments': '{"overview-table": "Alpha", "usage-chart": "Beta"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], MonthlyReport.STATUS_FINAL)
        self.report.refresh_from_db()
        self.assertEqual(self.report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)

    def test_final_save_is_blocked_when_status_validated_but_no_pages_exist(self):
        empty_report = get_or_create_monthly_report(self.site, '2026-09', actor_user=self.owner)
        create_report_version(
            report=empty_report,
            version_kind='draft',
            comments={},
            derived_from_version=None,
            actor_user=self.owner,
        )
        assign_report_validator(report=empty_report, validator_user=self.validator, assigned_by_user=self.owner)
        empty_report.validation_status = MonthlyReport.VALIDATION_VALIDATED
        empty_report.validated_by_user = self.validator
        empty_report.save(update_fields=['validation_status', 'validated_by_user'])

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-09',
                'save_mode': 'final',
                'comments': '{}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertFalse(payload['can_save_final'])
        self.assertEqual(payload['total_page_count'], 0)
