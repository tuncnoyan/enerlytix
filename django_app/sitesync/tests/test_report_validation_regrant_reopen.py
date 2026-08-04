"""Tests for validation reopen after superior-chain write regrant."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import (
    assign_report_validator,
    create_report_version,
    get_report_delegation_candidate_users,
    get_or_create_monthly_report,
    grant_report_write_access,
    mark_report_page_validation_state,
)


User = get_user_model()


class ReportValidationRegrantReopenTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='regrant_owner', password='pass123')
        self.supervisor = User.objects.create_user(username='regrant_supervisor', password='pass123')
        self.contributor = User.objects.create_user(username='regrant_contributor', password='pass123')
        self.team = Team.objects.create(name='Regrant Team', level=1, team_lead=self.supervisor)
        self.site = Site.objects.create(external_id='site-regrant-1', name='Regrant Site', team=self.team)
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.supervisor, team=self.team)
        UserTeamAssignment.objects.create(user=self.contributor, team=self.team)

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
        assign_report_validator(report=self.report, validator_user=self.supervisor, assigned_by_user=self.owner)
        mark_report_page_validation_state(report=self.report, page_key='overview-table', is_validated=True, actor_user=self.supervisor)
        mark_report_page_validation_state(report=self.report, page_key='usage-chart', is_validated=True, actor_user=self.supervisor)

        self.client.force_login(self.owner)
        final_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'final',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(final_response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)

    def test_superior_regrant_followed_by_edit_reopens_validation(self):
        self.client.force_login(self.supervisor)
        regrant_response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {
                'target_user_id': str(self.contributor.id),
                'reason': 'Need to fix final report wording',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(regrant_response.status_code, 200)

        self.client.logout()
        self.client.force_login(self.contributor)
        edit_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha revised', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(edit_response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertEqual(self.report.validation_reopened_at is not None, True)
        self.assertFalse(self.report.page_validation_states.get(page_key='overview-table').is_validated)
        self.assertTrue(self.report.page_validation_states.get(page_key='usage-chart').is_validated)

    def test_owner_cannot_edit_final_without_superior_regrant(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Owner tries edit', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_owner_can_edit_final_after_superior_regrant(self):
        self.client.force_login(self.supervisor)
        regrant_response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {
                'target_user_id': str(self.owner.id),
                'reason': 'Owner must correct final content',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(regrant_response.status_code, 200)

        self.client.force_login(self.owner)
        edit_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Owner revised', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(edit_response.status_code, 200)

    def test_owner_granted_contributor_cannot_edit_final_until_superior_regrant(self):
        grant_report_write_access(report=self.report, granted_user=self.contributor, granted_by=self.owner)

        self.client.force_login(self.contributor)
        denied_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Contributor tries edit', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(denied_response.status_code, 403)

        self.client.force_login(self.supervisor)
        regrant_response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {
                'target_user_id': str(self.contributor.id),
                'reason': 'Contributor needs to fix final content',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(regrant_response.status_code, 200)

        self.client.force_login(self.contributor)
        allowed_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Contributor revised', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(allowed_response.status_code, 200)

        self.client.force_login(self.supervisor)
        self.client.post(
            reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'}),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.client.force_login(self.contributor)
        final_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'final',
                'comments': json.dumps({'overview-table': 'Contributor revised', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(final_response.status_code, 200)

        self.client.force_login(self.contributor)
        post_final_denied_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Attempt after final', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.assertEqual(post_final_denied_response.status_code, 403)

    def test_owner_cannot_use_validation_regrant_route(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {
                'target_user_id': str(self.contributor.id),
                'reason': 'Owner should not reopen final write access',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)
        self.report.refresh_from_db()
        self.assertEqual(self.report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)

    def test_superior_candidate_list_includes_owner_for_final_validated_report(self):
        candidates = get_report_delegation_candidate_users(self.report, self.supervisor)
        candidate_ids = {item['id'] for item in candidates}
        self.assertIn(str(self.owner.id), candidate_ids)
