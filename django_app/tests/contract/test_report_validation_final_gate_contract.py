"""Contract checks for final-save validation gating."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report, mark_report_page_validation_state


User = get_user_model()


class ReportValidationFinalGateContractTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='final_contract_owner', password='pass123')
        self.validator = User.objects.create_user(username='final_contract_validator', password='pass123')
        self.team = Team.objects.create(name='Final Contract Team', level=1)
        self.site = Site.objects.create(external_id='site-contract-final-1', name='Final Contract Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)
        self.report = get_or_create_monthly_report(self.site, '2026-11', actor_user=self.owner)
        create_report_version(report=self.report, version_kind='draft', comments={'overview-table': 'Alpha', 'usage-chart': 'Beta'}, derived_from_version=None, actor_user=self.owner)
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)

    def test_final_save_blocks_with_clear_payload(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-11',
                'save_mode': 'final',
                'comments': '{"overview-table": "Alpha", "usage-chart": "Beta"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertFalse(payload['can_save_final'])
        self.assertIn('detail', payload)

    def test_final_save_payload_succeeds_after_validation(self):
        mark_report_page_validation_state(report=self.report, page_key='overview-table', is_validated=True, actor_user=self.validator)
        mark_report_page_validation_state(report=self.report, page_key='usage-chart', is_validated=True, actor_user=self.validator)
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-11',
                'save_mode': 'final',
                'comments': '{"overview-table": "Alpha", "usage-chart": "Beta"}',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], MonthlyReport.STATUS_FINAL)
