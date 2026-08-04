"""Tests for report validator assignment behavior."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, MonthlyReportVersion, Site, Team, UserTeamAssignment
from sitesync.services import get_report_validation_candidate_users


User = get_user_model()


class ReportValidationAssignmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='validation_owner', password='pass123')
        self.validator = User.objects.create_user(username='validation_validator', password='pass123')
        self.outsider = User.objects.create_user(username='validation_outsider', password='pass123')
        self.team = Team.objects.create(name='Validation Team', level=1)
        self.site = Site.objects.create(external_id='site-validation-assign-1', name='Validation Assign Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
        )

    def test_owner_can_assign_validator_and_status_transitions_to_awaiting_validation(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(self.report.validator_user_id, self.validator.id)
        self.assertEqual(self.report.validator_assigned_by_user_id, self.owner.id)
        payload = response.json()['validation_summary']
        self.assertEqual(payload['validation_status'], MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(payload['validator_user_name'], self.validator.username)
        self.assertFalse(payload['can_finalize'])

    def test_owner_cannot_assign_outsider_validator(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.outsider.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 400)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_DRAFT)
        self.assertIsNone(self.report.validator_user_id)

    def test_non_authorized_user_cannot_assign_validator(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_DRAFT)

    def test_assignment_writes_initial_report_version_agnostic_state(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyReportVersion.objects.filter(report=self.report).count(), 0)

    def test_team_lead_candidate_scope_matches_expected_validator_pool(self):
        manager = User.objects.create_user(username='testmanager01', password='pass123')
        lead_one = User.objects.create_user(username='testlead01', password='pass123')
        lead_two = User.objects.create_user(username='testlead02', password='pass123')
        user_one = User.objects.create_user(username='testuser01', password='pass123')
        user_two = User.objects.create_user(username='testuser02', password='pass123')
        user_three = User.objects.create_user(username='testuser03', password='pass123')
        user_four = User.objects.create_user(username='testuser04', password='pass123')

        root_team = Team.objects.create(name='Root Team', level=1, manager=manager)
        lead_one_team = Team.objects.create(
            name='Lead One Team',
            level=2,
            parent_team=root_team,
            team_lead=lead_one,
            manager=manager,
        )
        lead_two_team = Team.objects.create(
            name='Lead Two Team',
            level=2,
            parent_team=root_team,
            team_lead=lead_two,
            manager=manager,
        )

        UserTeamAssignment.objects.create(user=lead_one, team=root_team)
        UserTeamAssignment.objects.create(user=lead_two, team=root_team)
        UserTeamAssignment.objects.create(user=user_one, team=lead_one_team)
        UserTeamAssignment.objects.create(user=user_two, team=lead_one_team)
        UserTeamAssignment.objects.create(user=user_three, team=lead_two_team)
        UserTeamAssignment.objects.create(user=user_four, team=lead_two_team)

        scoped_report = MonthlyReport.objects.create(
            site=Site.objects.create(external_id='site-validator-scope-1', name='Validator Scope Site', team=None),
            reporting_month='2026-08',
            owner_user=user_four,
            created_by_user=user_four,
            last_modified_by_user=user_four,
        )

        candidates = get_report_validation_candidate_users(scoped_report, actor_user=lead_one)
        candidate_usernames = {item['username'] for item in candidates}

        self.assertIn('testuser01', candidate_usernames)
        self.assertIn('testuser02', candidate_usernames)
        self.assertIn('testlead02', candidate_usernames)
        self.assertIn('testmanager01', candidate_usernames)
        self.assertNotIn('testuser03', candidate_usernames)
        self.assertNotIn('testuser04', candidate_usernames)
