from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from uuid import uuid4

from sitesync.models import MonthlyReport, ReportWriteGrant, Site, Team, UserTeamAssignment


User = get_user_model()


class SavedReportsOwnershipListingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner4', email='owner4@example.com', password='pw123456')
        self.viewer = User.objects.create_user(username='viewer4', email='viewer4@example.com', password='pw123456')
        self.team = Team.objects.create(name='Listing Team', level=1)
        self.site = Site.objects.create(external_id='site-listing-1', name='Listing Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.viewer, team=self.team)

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
        )

    def test_saved_reports_json_includes_ownership_fields_and_access_mode(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('sitesync:saved_reports'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()['reports']
        self.assertEqual(len(payload), 1)

        row = payload[0]
        self.assertIn('owner_name', row)
        self.assertIn('created_at', row)
        self.assertIn('last_edited_by_name', row)
        self.assertIn('last_edited_at', row)
        self.assertIn('access_mode', row)
        self.assertEqual(row['access_mode'], 'owner')

    def test_saved_reports_access_mode_switches_to_collaborator(self):
        ReportWriteGrant.objects.create(report=self.report, granted_user=self.viewer, granted_by=self.owner, is_active=True)

        self.client.force_login(self.viewer)
        response = self.client.get(reverse('sitesync:saved_reports'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        row = response.json()['reports'][0]
        self.assertEqual(row['access_mode'], 'collaborator')

    def test_saved_reports_filters_case_insensitive_site_and_user_contains(self):
        validator = User.objects.create_user(username='ValidationHero', email='validator@example.com', password='pw123456')
        editor = User.objects.create_user(username='EditCaptain', email='editor@example.com', password='pw123456')

        self.report.validator_user = validator
        self.report.last_modified_by_user = editor
        self.report.validation_status = MonthlyReport.VALIDATION_VALIDATED
        self.report.save(update_fields=['validator_user', 'last_modified_by_user', 'validation_status'])

        other_site = Site.objects.create(external_id='site-listing-2', name='North Complex', team=self.team)
        MonthlyReport.objects.create(
            site=other_site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
            validation_status=MonthlyReport.VALIDATION_DRAFT,
        )

        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('sitesync:saved_reports'),
            {
                'format': 'json',
                'site_query': 'listing',
                'user_query': 'hero',
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()['reports']
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['id'], str(self.report.id))

    def test_bulk_delete_atomic_failure_returns_blocking_references(self):
        self.viewer.is_staff = True
        self.viewer.save(update_fields=['is_staff'])
        self.client.force_login(self.viewer)

        blocked_id = str(uuid4())
        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'selected_report_ids': [str(self.report.id), blocked_id],
                'password_confirmation': 'pw123456',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertEqual(payload['code'], 'atomic_delete_blocked')
        self.assertIn(blocked_id, payload['blocked_report_refs'])
        self.assertTrue(MonthlyReport.objects.filter(id=self.report.id).exists())
