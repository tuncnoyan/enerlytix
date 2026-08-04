"""Contract checks for report validator assignment."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportValidationAssignmentContractTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='contract_owner', password='pass123')
        self.validator = User.objects.create_user(username='contract_validator', password='pass123')
        self.outsider = User.objects.create_user(username='contract_outsider', password='pass123')
        self.team = Team.objects.create(name='Contract Team', level=1)
        self.site = Site.objects.create(external_id='site-contract-assign-1', name='Contract Assign Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)
        self.report = MonthlyReport.objects.create(site=self.site, reporting_month='2026-11', owner_user=self.owner, created_by_user=self.owner, last_modified_by_user=self.owner)

    def test_assignment_returns_validation_summary(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertIn('validation_summary', payload)
        self.assertEqual(payload['validation_summary']['validation_status'], MonthlyReport.VALIDATION_AWAITING)

    def test_assignment_rejects_ineligible_validator(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.outsider.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.json())
