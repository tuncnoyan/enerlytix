"""Tests for monthly report draft save and reopen workflow."""

import json
from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from sitesync.models import AppSettings, CapacityReference, HalfHourlyConsumption, ImportRun, MonthlyReport, MonthlyReportVersion, MonthlyConsumption, Site, Supply, Team, UserTeamAssignment
from sitesync.services import assign_report_validator
from sitesync.views import _report_editor_context, report_view


class ReportDraftWorkflowTest(TestCase):
    """Validate draft save and single-report-per-month behavior."""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='reportuser', password='pass123')
        self.client.force_login(self.user)
        self.site = Site.objects.create(
            external_id='site-ext-1',
            name='Test Site',
            description='Demo site',
            floor_area=100,
            floor_area_unit='sqm',
        )
        AppSettings.objects.create(
            electricity_benchmark_intensity=120,
            gas_benchmark_intensity=90,
            water_benchmark_intensity=1.8,
        )

    def test_post_report_creates_draft_report_for_site_month(self):
        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
                'comments': json.dumps({'overview': 'Draft note'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyReport.objects.count(), 1)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_status, MonthlyReport.STATUS_DRAFT)
        self.assertIsNotNone(report.current_version)
        self.assertEqual(report.current_version.version_kind, MonthlyReportVersion.KIND_DRAFT)

    def test_post_report_reuses_existing_site_month_identity(self):
        first = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(second.status_code, 200)

        self.assertEqual(MonthlyReport.objects.count(), 1)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.versions.count(), 2)

    def test_get_report_supports_reporting_month_alias_for_end_month(self):
        request = self.factory.get(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'reporting_month': '2026-05',
            },
        )
        request.user = self.user
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"endMonth": "2026-05"', response.content.decode('utf-8'))

    def test_post_report_persists_selected_supply_ids_on_version(self):
        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
                'supply_ids': 'supply-a,supply-b',
                'comments': json.dumps({'overview': 'Draft note'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_version.selected_supply_ids, ['supply-a', 'supply-b'])

    def test_get_report_reuses_saved_supply_ids_when_query_is_missing(self):
        self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
                'supply_ids': 'supply-a,supply-b',
                'comments': json.dumps({'overview': 'Draft note'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        context = _report_editor_context(
            str(self.site.id),
            '2026-05',
            '',
            '',
            user=self.user,
        )
        self.assertEqual(context['supply_ids'], 'supply-a,supply-b')
        self.assertEqual(context['report_context']['supplyIds'], 'supply-a,supply-b')

    def test_post_report_pins_default_supply_ids_when_none_selected(self):
        """Regression test: saving a report without an explicit supply selection must
        pin the site's current fiscal supplies on the version, rather than persisting
        an empty list. Otherwise, supplies added to the site later would silently
        appear (with no data) when the saved report is reopened."""
        Supply.objects.create(
            site=self.site,
            external_id='supply-existing',
            name='Existing Meter',
            utility_type='electricity',
        )

        response = self.client.post(
            '/report/',
            data={
                'site_id': str(self.site.id),
                'end_month': '2026-05',
                'save_mode': 'draft',
                'comments': json.dumps({'overview': 'Draft note'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        report = MonthlyReport.objects.get(site=self.site, reporting_month='2026-05')
        self.assertEqual(report.current_version.selected_supply_ids, ['supply-existing'])

        # A new supply is added to the site after the report was saved.
        Supply.objects.create(
            site=self.site,
            external_id='supply-added-later',
            name='Later Meter',
            utility_type='gas',
        )

        context = _report_editor_context(
            str(self.site.id),
            '2026-05',
            '',
            '',
            user=self.user,
        )
        self.assertEqual(context['supply_ids'], 'supply-existing')

    def test_get_report_renders_validator_assignment_control_for_owner(self):
        team = Team.objects.create(name='Validator Control Team', level=1)
        owner = get_user_model().objects.create_user(username='validator_owner', password='pass123')
        candidate = get_user_model().objects.create_user(username='validator_candidate', password='pass123')
        UserTeamAssignment.objects.create(user=owner, team=team)
        UserTeamAssignment.objects.create(user=candidate, team=team)
        site = Site.objects.create(
            external_id='site-validator-control-1',
            name='Validator Control Site',
            team=team,
        )
        MonthlyReport.objects.create(
            site=site,
            reporting_month='2026-05',
            owner_user=owner,
            created_by_user=owner,
            last_modified_by_user=owner,
        )

        request = self.factory.get(
            '/report/',
            data={
                'site_id': str(site.id),
                'end_month': '2026-05',
            },
        )
        request.user = owner
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn('Assign validator', body)
        self.assertIn('validation-validator-select', body)
        self.assertLess(body.index('Validation Summary'), body.index('Cover Page Editor'))

    def test_get_report_shows_validator_candidates_when_site_team_is_missing(self):
        team = Team.objects.create(name='Owner Fallback Team', level=1)
        owner = get_user_model().objects.create_user(username='validator_owner_fallback', password='pass123')
        candidate = get_user_model().objects.create_user(username='validator_candidate_fallback', password='pass123')
        UserTeamAssignment.objects.create(user=owner, team=team)
        UserTeamAssignment.objects.create(user=candidate, team=team)

        site = Site.objects.create(
            external_id='site-validator-fallback-1',
            name='Validator Fallback Site',
            team=None,
        )
        MonthlyReport.objects.create(
            site=site,
            reporting_month='2026-04',
            owner_user=owner,
            created_by_user=owner,
            last_modified_by_user=owner,
        )

        request = self.factory.get(
            '/report/',
            data={
                'site_id': str(site.id),
                'end_month': '2026-04',
            },
        )
        request.user = owner
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn('validator_candidate_fallback', body)

    def test_get_report_renders_when_validator_is_assigned(self):
        team = Team.objects.create(name='Validator Assigned Team', level=1)
        owner = get_user_model().objects.create_user(username='validator_owner_assigned', password='pass123')
        candidate = get_user_model().objects.create_user(username='validator_candidate_assigned', password='pass123')
        UserTeamAssignment.objects.create(user=owner, team=team)
        UserTeamAssignment.objects.create(user=candidate, team=team)
        site = Site.objects.create(
            external_id='site-validator-assigned-1',
            name='Validator Assigned Site',
            team=team,
        )
        report = MonthlyReport.objects.create(
            site=site,
            reporting_month='2026-04',
            owner_user=owner,
            created_by_user=owner,
            last_modified_by_user=owner,
        )
        assign_report_validator(report=report, validator_user=candidate, assigned_by_user=owner)

        request = self.factory.get(
            '/report/',
            data={
                'site_id': str(site.id),
                'end_month': '2026-04',
            },
        )
        request.user = owner
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('validator_candidate_assigned', response.content.decode('utf-8'))

    def test_report_data_uses_latest_capacity_reference_value(self):
        supply = Supply.objects.create(
            site=self.site,
            external_id='supply-ext-1',
            name='Main Meter',
            utility_type='electricity',
            device_id='MTR-777',
        )
        import_run = ImportRun.objects.create(
            selected_supply_ids=['supply-ext-1'],
            reporting_month='2026-05',
            status=ImportRun.STATUS_SUCCESS,
            affected_supply_count=1,
        )
        start = datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc)
        HalfHourlyConsumption.objects.create(
            import_run=import_run,
            supply=supply,
            canonical_month_key='2026-05',
            source_period_start=start,
            source_period_end=datetime(2026, 5, 10, 0, 30, tzinfo=timezone.utc),
            consumption=12,
        )
        CapacityReference.objects.create(
            name='Current Name',
            esight_meter_code='MTR-777',
            available_capacity_kva=155.5,
            last_imported_at=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
        )

        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-05'},
        )

        self.assertEqual(response.status_code, 200)
        supplies = {item['external_id']: item for item in response.json()['supplies']}
        self.assertEqual(supplies['supply-ext-1']['available_capacity_kva'], 155.5)
        self.assertEqual(supplies['supply-ext-1']['load_factor']['available_capacity_kva'], 155.5)

    def test_report_data_computes_electricity_benchmark_from_settings_and_floor_area(self):
        supply = Supply.objects.create(
            site=self.site,
            external_id='supply-bench-elec',
            name='Benchmark Meter',
            utility_type='electricity',
            device_id='MTR-BENCH-E',
        )
        MonthlyConsumption.objects.create(
            import_run=ImportRun.objects.create(
                selected_supply_ids=['supply-bench-elec'],
                reporting_month='2026-05',
                status=ImportRun.STATUS_SUCCESS,
                affected_supply_count=1,
            ),
            supply=supply,
            canonical_month_key='2026-05',
            source_period_start=datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc),
            source_period_end=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            consumption=1000,
        )

        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-05'},
        )

        self.assertEqual(response.status_code, 200)
        supplies = {item['external_id']: item for item in response.json()['supplies']}
        benchmark_values = supplies['supply-bench-elec']['monthly']['benchmark_kwh']
        self.assertTrue(all(value == 1000.0 for value in benchmark_values))

    def test_report_data_computes_water_benchmark_from_settings_and_floor_area(self):
        supply = Supply.objects.create(
            site=self.site,
            external_id='supply-bench-water',
            name='Water Meter',
            utility_type='water',
            device_id='MTR-BENCH-W',
        )
        MonthlyConsumption.objects.create(
            import_run=ImportRun.objects.create(
                selected_supply_ids=['supply-bench-water'],
                reporting_month='2026-05',
                status=ImportRun.STATUS_SUCCESS,
                affected_supply_count=1,
            ),
            supply=supply,
            canonical_month_key='2026-05',
            source_period_start=datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc),
            source_period_end=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            consumption=8,
        )

        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-05'},
        )

        self.assertEqual(response.status_code, 200)
        supplies = {item['external_id']: item for item in response.json()['supplies']}
        benchmark_values = supplies['supply-bench-water']['monthly']['benchmark_m3']
        self.assertTrue(all(value == 15.0 for value in benchmark_values))
