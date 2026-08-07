"""Contract checks for page validation marking."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report


User = get_user_model()


class ReportValidationPageMarkContractTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='page_contract_owner', password='pass123')
        self.validator = User.objects.create_user(username='page_contract_validator', password='pass123')
        self.outsider = User.objects.create_user(username='page_contract_outsider', password='pass123')
        self.team = Team.objects.create(name='Page Contract Team', level=1)
        self.site = Site.objects.create(external_id='site-contract-page-1', name='Page Contract Site', team=self.team)
        for user in [self.owner, self.validator, self.outsider]:
            UserTeamAssignment.objects.create(user=user, team=self.team)
        self.report = get_or_create_monthly_report(self.site, '2026-11', actor_user=self.owner)
        create_report_version(report=self.report, version_kind='draft', comments={'overview-table': 'Alpha'}, derived_from_version=None, actor_user=self.owner)
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)

    def test_page_mark_returns_page_and_summary(self):
        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['page_key'], 'overview-table')
        self.assertIn('validation_summary', payload)
        self.assertEqual(payload['validation_summary']['validated_page_count'], 1)

    def test_page_mark_rejects_unknown_page(self):
        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'unknown-page'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.json())

    def test_non_validator_is_denied(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('detail', response.json())

    def test_legacy_overview_key_accepts_overview_table_toggle(self):
        legacy_report = get_or_create_monthly_report(self.site, '2026-12', actor_user=self.owner)
        create_report_version(
            report=legacy_report,
            version_kind='draft',
            comments={'overview': 'Legacy overview text'},
            derived_from_version=None,
            actor_user=self.owner,
        )
        assign_report_validator(report=legacy_report, validator_user=self.validator, assigned_by_user=self.owner)

        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': legacy_report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['page_key'], 'overview')
