from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, RoleAssignment, Site, Team, UserTeamAssignment
from sitesync.services import get_accessible_reports


User = get_user_model()


class SavedReportsTeamContextTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='team_owner', password='pass123456')
        self.team_lead = User.objects.create_user(username='team_lead_user', password='pass123456')
        self.unassigned = User.objects.create_user(username='no_team_user', password='pass123456')

        self.team = Team.objects.create(name='Team One', level=1, team_lead=self.team_lead)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)

        self.site = Site.objects.create(external_id='team-site-1', name='Team Scoped Site', team=self.team)
        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-08',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def test_team_lead_without_membership_row_still_has_team_context(self):
        self.client.force_login(self.team_lead)
        response = self.client.get(reverse('sitesync:saved_reports'))
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "You haven't been assigned to a team yet")

        visible_ids = set(get_accessible_reports(self.team_lead).values_list('id', flat=True))
        self.assertIn(self.report.id, visible_ids)

    def test_request_team_assignment_page_renders_for_unassigned_user(self):
        self.client.force_login(self.unassigned)
        response = self.client.get(reverse('sitesync:request_team_assignment'))
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request Team Assignment')

    def test_request_team_assignment_redirects_for_team_lead_context(self):
        self.client.force_login(self.team_lead)
        response = self.client.get(reverse('sitesync:request_team_assignment'))
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('sitesync:saved_reports'), response.url)

    def test_team_lead_sees_null_team_reports_created_by_team_members(self):
        member_two = User.objects.create_user(username='team_member_two', password='pass123456')
        UserTeamAssignment.objects.create(user=member_two, team=self.team)

        null_team_site = Site.objects.create(external_id='team-site-legacy', name='Legacy Site')
        report_one = MonthlyReport.objects.create(
            site=null_team_site,
            reporting_month='2026-06',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_FINAL,
        )
        report_two = MonthlyReport.objects.create(
            site=null_team_site,
            reporting_month='2026-07',
            owner_user=member_two,
            created_by_user=member_two,
            last_modified_by_user=member_two,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_FINAL,
        )

        visible_ids = set(get_accessible_reports(self.team_lead).values_list('id', flat=True))
        self.assertIn(report_one.id, visible_ids)
        self.assertIn(report_two.id, visible_ids)

    def test_role_assigned_manager_sees_subteam_member_null_team_reports(self):
        top_manager = User.objects.create_user(username='top_manager_user', password='pass123456')
        member_user = User.objects.create_user(username='sub_member_user', password='pass123456')

        top_team = Team.objects.create(name='Top Team', level=1)
        child_team = Team.objects.create(name='Child Team', level=2, parent_team=top_team)

        UserTeamAssignment.objects.create(user=top_manager, team=top_team)
        UserTeamAssignment.objects.create(user=member_user, team=child_team)
        RoleAssignment.objects.create(user=top_manager, role_name='manager')

        legacy_site = Site.objects.create(external_id='legacy-mgr-site', name='Legacy Manager Site')
        subteam_report = MonthlyReport.objects.create(
            site=legacy_site,
            reporting_month='2026-08',
            owner_user=member_user,
            created_by_user=member_user,
            last_modified_by_user=member_user,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_FINAL,
        )

        visible_ids = set(get_accessible_reports(top_manager).values_list('id', flat=True))
        self.assertIn(subteam_report.id, visible_ids)

    def test_saved_reports_combined_criteria_returns_expected_row(self):
        validator = User.objects.create_user(username='combo_validator', password='pass123456')
        self.report.current_status = MonthlyReport.STATUS_FINAL
        self.report.validation_status = MonthlyReport.VALIDATION_VALIDATED
        self.report.validator_user = validator
        self.report.save(update_fields=['current_status', 'validation_status', 'validator_user'])

        non_matching_site = Site.objects.create(external_id='team-site-2', name='Other Plant', team=self.team)
        MonthlyReport.objects.create(
            site=non_matching_site,
            reporting_month='2026-04',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
            validation_status=MonthlyReport.VALIDATION_DRAFT,
        )

        self.client.force_login(self.team_lead)
        response = self.client.get(
            reverse('sitesync:saved_reports'),
            {
                'format': 'json',
                'site_query': 'scoped',
                'user_query': 'validator',
                'start_month': '2026-08',
                'end_month': '2026-08',
                'report_status': ['final'],
                'validation_status': ['validated'],
                'report_status_applied': '1',
                'validation_status_applied': '1',
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        reports = response.json()['reports']
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]['id'], str(self.report.id))

    def test_saved_reports_all_status_options_unticked_returns_zero_rows(self):
        self.client.force_login(self.team_lead)
        response = self.client.get(
            reverse('sitesync:saved_reports'),
            {
                'format': 'json',
                'report_status_applied': '1',
                'validation_status_applied': '1',
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['reports'], [])
        self.assertEqual(payload['selected_filters']['report_statuses'], [])
        self.assertEqual(payload['selected_filters']['validation_statuses'], [])

    def test_saved_reports_sort_reporting_month_defaults_to_newest_first(self):
        second_site = Site.objects.create(external_id='team-site-3', name='Team Scoped Site B', team=self.team)
        MonthlyReport.objects.create(
            site=second_site,
            reporting_month='2026-05',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
            validation_status=MonthlyReport.VALIDATION_DRAFT,
        )

        self.client.force_login(self.team_lead)
        response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json', 'sort_field': 'reporting_month'})
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['sort']['field'], 'reporting_month')
        months = [row['reporting_month'] for row in payload['reports']]
        self.assertEqual(months, sorted(months, reverse=True))

    def test_saved_reports_sort_site_name_defaults_to_ascending(self):
        second_site = Site.objects.create(external_id='team-site-4', name='Aardvark Site', team=self.team)
        MonthlyReport.objects.create(
            site=second_site,
            reporting_month='2026-08',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
            validation_status=MonthlyReport.VALIDATION_DRAFT,
        )

        self.client.force_login(self.team_lead)
        response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json', 'sort_field': 'site_name'})
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['sort']['field'], 'site_name')
        site_names = [row['site_name'] for row in payload['reports']]
        self.assertEqual(site_names, sorted(site_names))
