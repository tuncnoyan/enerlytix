"""Tests for report validation metadata exposure in saved reports."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import create_report_version, get_or_create_monthly_report


User = get_user_model()


class ReportValidationMetadataTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='validation_meta_user', password='pass123')
        self.team = Team.objects.create(name='Validation Meta Team', level=1)
        self.site = Site.objects.create(external_id='site-validation-meta-1', name='Validation Meta Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.user, team=self.team)
        self.client.force_login(self.user)

    def test_saved_reports_json_exposes_validation_metadata_defaults(self):
        report = get_or_create_monthly_report(self.site, '2026-07', actor_user=self.user)
        create_report_version(
            report=report,
            version_kind='draft',
            comments={'overview-table': 'Alpha'},
            derived_from_version=None,
            actor_user=self.user,
        )

        response = self.client.get(reverse('sitesync:saved_reports'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        payload = response.json()['reports']
        self.assertEqual(len(payload), 1)
        row = payload[0]
        self.assertEqual(row['validation_status'], MonthlyReport.VALIDATION_DRAFT)
        self.assertIsNone(row['validator_name'])
        self.assertIsNone(row['validated_by_name'])
        self.assertIsNone(row['validation_date'])
        self.assertFalse(row['can_save_final'])
