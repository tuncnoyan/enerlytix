"""Tests for monthly report finalisation and replacement-final workflow."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, MonthlyReportVersion, Site, Team, UserTeamAssignment
from sitesync.services import (
    assign_report_validator,
    create_report_version,
    get_or_create_monthly_report,
    mark_report_page_validation_state,
)


class ReportFinalisationWorkflowTest(TestCase):
    """Validate final save and warning-before-revision behavior."""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='finaluser', password='pass123')
        self.validator = get_user_model().objects.create_user(username='finalvalidator', password='pass123')
        self.manager = get_user_model().objects.create_user(username='finalmanager', password='pass123')
        self.client.force_login(self.user)
        self.team = Team.objects.create(name='Finalisation Team', level=1, manager=self.manager)
        self.site = Site.objects.create(
            external_id='site-ext-final-1',
            name='Final Test Site',
            description='Finalization demo site',
            team=self.team,
        )
        UserTeamAssignment.objects.create(user=self.user, team=self.team)
        UserTeamAssignment.objects.create(user=self.validator, team=self.team)
        UserTeamAssignment.objects.create(user=self.manager, team=self.team)

        # Seed a validated draft so final-save tests exercise finalisation behavior,
        # not validation-gate denial behavior.
        self.report = get_or_create_monthly_report(self.site, '2026-05', actor_user=self.user)
        create_report_version(
            report=self.report,
            version_kind='draft',
            comments={
                'overview-table': 'Alpha',
                'usage-chart': 'Beta',
            },
            derived_from_version=None,
            actor_user=self.user,
        )
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.user)
        mark_report_page_validation_state(
            report=self.report,
            page_key='overview-table',
            is_validated=True,
            actor_user=self.validator,
        )
        mark_report_page_validation_state(
            report=self.report,
            page_key='usage-chart',
            is_validated=True,
            actor_user=self.validator,
        )

    def test_can_save_report_as_final(self):
        response = self._save_final()

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertIsNotNone(report.current_final_version)
        self.assertEqual(report.current_final_version.version_kind, MonthlyReportVersion.KIND_FINAL)

    def test_editing_existing_final_requires_warning_confirmation(self):
        self._save_final()
        regrant = self._regrant_owner_write_access()
        self.assertEqual(regrant.status_code, 200)

        warning = self._save_final()

        self.assertEqual(warning.status_code, 409)
        self.assertEqual(MonthlyReportVersion.objects.count(), 2)

    def test_confirmed_final_edit_creates_replacement_final_version(self):
        self._save_final()
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        original_final = report.current_final_version

        regrant = self._regrant_owner_write_access()
        self.assertEqual(regrant.status_code, 200)

        confirmed = self._save_final(confirm_final_edit=True)

        self.assertEqual(confirmed.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertIsNotNone(report.current_final_version)
        self.assertNotEqual(report.current_final_version.id, original_final.id)
        self.assertEqual(report.current_final_version.version_kind, MonthlyReportVersion.KIND_REPLACEMENT_FINAL)
        self.assertEqual(MonthlyReportVersion.objects.filter(report=report).count(), 3)

    def _save_final(self, *, confirm_final_edit=False):
        return self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'final',
                'confirm_final_edit': 'true' if confirm_final_edit else 'false',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def _regrant_owner_write_access(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {
                'target_user_id': str(self.user.id),
                'reason': 'Allow replacement final after governance warning',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()
        self.client.force_login(self.user)
        return response
