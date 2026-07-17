"""Tests for available capacity upload and report-time resolution."""

from datetime import datetime, timezone
from io import BytesIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from sitesync.models import (
    AppSettings,
    CapacityReference,
    CapacityUploadRun,
    HalfHourlyConsumption,
    ImportRun,
    Site,
    Supply,
)


class CapacityUploadTests(TestCase):
    def setUp(self):
        AppSettings.objects.create()

    def _build_workbook_bytes(self, rows):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(['Name', 'eSight Meter Code', 'Av Cap (kVA)'])
        for row in rows:
            worksheet.append(row)

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def test_capacity_upload_partial_import_skips_invalid_rows(self):
        payload = self._build_workbook_bytes([
            ['Meter A', 'MTR-001', 95.5],
            ['', 'MTR-002', 50],
            ['Duplicate', 'MTR-001', 100],
            ['Bad Number', 'MTR-003', 'n/a'],
        ])
        upload = SimpleUploadedFile(
            'capacity.xlsx',
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(
            reverse('sitesync:settings_panel'),
            {
                'capacity_upload_submit': '1',
                'capacity_upload_file': upload,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CapacityReference.objects.count(), 1)
        self.assertTrue(CapacityReference.objects.filter(esight_meter_code='MTR-001').exists())

        run = CapacityUploadRun.objects.latest('uploaded_at')
        self.assertEqual(run.status, CapacityUploadRun.STATUS_PARTIAL_SUCCESS)
        self.assertEqual(run.total_rows, 4)
        self.assertEqual(run.accepted_rows, 1)
        self.assertEqual(run.rejected_rows, 3)

    def test_capacity_upload_accepts_blank_or_null_capacity_as_null(self):
        payload = self._build_workbook_bytes([
            ['Meter A', 'MTR-010', None],
            ['Meter B', 'MTR-011', ''],
            ['Meter C', 'MTR-012', 88.25],
        ])
        upload = SimpleUploadedFile(
            'capacity.xlsx',
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(
            reverse('sitesync:settings_panel'),
            {
                'capacity_upload_submit': '1',
                'capacity_upload_file': upload,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CapacityReference.objects.count(), 3)

        self.assertIsNone(CapacityReference.objects.get(esight_meter_code='MTR-010').available_capacity_kva)
        self.assertIsNone(CapacityReference.objects.get(esight_meter_code='MTR-011').available_capacity_kva)
        self.assertEqual(float(CapacityReference.objects.get(esight_meter_code='MTR-012').available_capacity_kva), 88.25)

        run = CapacityUploadRun.objects.latest('uploaded_at')
        self.assertEqual(run.status, CapacityUploadRun.STATUS_SUCCESS)
        self.assertEqual(run.total_rows, 3)
        self.assertEqual(run.accepted_rows, 3)
        self.assertEqual(run.rejected_rows, 0)

    def test_report_data_uses_uploaded_capacity_by_meter_code(self):
        site = Site.objects.create(external_id='site-1', name='Site 1')
        supply_match = Supply.objects.create(
            site=site,
            external_id='supply-1',
            name='Supply 1',
            utility_type='electricity',
            device_id='MTR-001',
        )
        supply_no_match = Supply.objects.create(
            site=site,
            external_id='supply-2',
            name='Supply 2',
            utility_type='electricity',
            device_id='MTR-999',
        )

        import_run = ImportRun.objects.create(
            selected_supply_ids=['supply-1', 'supply-2'],
            reporting_month='2026-06',
            status=ImportRun.STATUS_SUCCESS,
            affected_supply_count=2,
        )

        start = datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 10, 0, 30, tzinfo=timezone.utc)
        HalfHourlyConsumption.objects.create(
            import_run=import_run,
            supply=supply_match,
            canonical_month_key='2026-06',
            source_period_start=start,
            source_period_end=end,
            consumption=10,
        )
        HalfHourlyConsumption.objects.create(
            import_run=import_run,
            supply=supply_no_match,
            canonical_month_key='2026-06',
            source_period_start=start,
            source_period_end=end,
            consumption=8,
        )

        CapacityReference.objects.create(
            name='Meter A',
            esight_meter_code='MTR-001',
            available_capacity_kva=123.4,
            last_imported_at=datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
        )

        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        supplies = {item['external_id']: item for item in data['supplies']}

        self.assertEqual(supplies['supply-1']['load_factor']['available_capacity_kva'], 123.4)
        self.assertIsNone(supplies['supply-2']['load_factor']['available_capacity_kva'])
