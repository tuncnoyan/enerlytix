"""Tests for monthly report draft save and reopen workflow."""

import json
from datetime import datetime, timezone

from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from sitesync.models import AppSettings, CapacityReference, HalfHourlyConsumption, ImportRun, MonthlyReport, MonthlyReportVersion, MonthlyConsumption, Site, Supply
from sitesync.views import report_view


class ReportDraftWorkflowTest(TestCase):
    """Validate draft save and single-report-per-month behavior."""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
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
        response = report_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"endMonth": "2026-05"', response.content.decode('utf-8'))

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
