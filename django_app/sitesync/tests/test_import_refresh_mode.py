from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from sitesync.models import (
    HalfHourlyConsumption,
    ImportRun,
    InvoiceCost,
    MonthlyConsumption,
    Site,
    Supply,
)
from sitesync.services import ConsumptionImportService, get_halfhourly_windows, get_invoice_window, get_monthly_window


class ImportRefreshModeTests(TestCase):
    def setUp(self):
        self.reporting_month = '2026-05'
        self.site = Site.objects.create(external_id='site-1', name='Site 1')
        self.supply = Supply.objects.create(
            site=self.site,
            external_id='supply-1',
            name='Supply 1',
            utility_type='electricity',
        )
        self.seed_run = ImportRun.objects.create(
            selected_supply_ids=[self.supply.external_id],
            reporting_month=self.reporting_month,
            status=ImportRun.STATUS_SUCCESS,
            affected_supply_count=1,
        )

        hh_windows = get_halfhourly_windows(self.reporting_month)
        for start, end in hh_windows:
            HalfHourlyConsumption.objects.create(
                import_run=self.seed_run,
                supply=self.supply,
                canonical_month_key=end.strftime('%Y-%m'),
                source_period_start=start,
                source_period_end=start + timedelta(minutes=30),
                consumption=Decimal('1.0'),
            )

        monthly_start, monthly_end = get_monthly_window(self.reporting_month)
        MonthlyConsumption.objects.create(
            import_run=self.seed_run,
            supply=self.supply,
            canonical_month_key=monthly_end.strftime('%Y-%m'),
            source_period_start=monthly_start,
            source_period_end=monthly_start + timedelta(days=30),
            consumption=Decimal('10.0'),
            breakdown={},
            sources=[],
        )

        invoice_start, _ = get_invoice_window(self.reporting_month)
        InvoiceCost.objects.create(
            import_run=self.seed_run,
            supply=self.supply,
            canonical_month_key=invoice_start.strftime('%Y-%m'),
            source_period_start=invoice_start,
            source_period_end=invoice_start + timedelta(days=30),
            cost=Decimal('25.5'),
            invoice_metadata={},
        )

    def test_run_skips_download_when_refresh_disabled_and_cache_exists(self):
        service = ConsumptionImportService()

        with patch.object(service, '_fetch_consumption_for_supply') as consumption_fetch, patch.object(service, '_fetch_invoices_for_supply') as invoice_fetch:
            run = service.run(
                supply_external_ids=[self.supply.external_id],
                reporting_month=self.reporting_month,
                refresh_mode=False,
            )

        consumption_fetch.assert_not_called()
        invoice_fetch.assert_not_called()
        self.assertEqual(run.status, ImportRun.STATUS_SUCCESS)
        self.assertEqual(run.records_failed, 0)
        self.assertEqual(run.records_imported, 0)
        self.assertTrue(run.outcome_details)
        self.assertTrue(all(item.get('status') == 'skipped' for item in run.outcome_details))

    def test_run_forces_download_when_refresh_enabled(self):
        service = ConsumptionImportService()

        with patch.object(service, '_fetch_consumption_for_supply', return_value=({'data': []}, 0, self.supply.external_id)) as consumption_fetch, patch.object(service, '_fetch_invoices_for_supply', return_value=([], 0, self.supply.external_id)) as invoice_fetch:
            run = service.run(
                supply_external_ids=[self.supply.external_id],
                reporting_month=self.reporting_month,
                refresh_mode=True,
            )

        self.assertEqual(consumption_fetch.call_count, 3)
        invoice_fetch.assert_called_once()
        self.assertEqual(run.status, ImportRun.STATUS_SUCCESS)