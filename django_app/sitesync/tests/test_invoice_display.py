from decimal import Decimal

from django.test import TestCase

from sitesync.models import ImportRun, InvoiceCost, Site, Supply
from sitesync.services import get_consumption_display_records


class InvoiceDisplayRecordsTests(TestCase):
    def setUp(self):
        self.site = Site.objects.create(external_id='site-1', name='Site 1')
        self.supply = Supply.objects.create(
            site=self.site,
            external_id='supply-1',
            name='Supply 1',
            utility_type='electricity',
        )
        self.import_run = ImportRun.objects.create(
            selected_supply_ids=[self.supply.external_id],
            reporting_month='2026-05',
            status=ImportRun.STATUS_IN_PROGRESS,
            affected_supply_count=1,
        )

    def test_invoice_display_falls_back_to_existing_history_when_window_has_no_rows(self):
        InvoiceCost.objects.create(
            import_run=self.import_run,
            supply=self.supply,
            canonical_month_key='2020-08',
            source_period_start='2020-07-02T00:00:00Z',
            source_period_end='2020-08-01T00:00:00Z',
            cost=Decimal('125.06'),
        )

        rows = get_consumption_display_records(
            reporting_month='2026-05',
            data_type='invoice',
            supply_external_ids=[self.supply.external_id],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(str(rows[0]['value']), '125.060000')

    def test_invoice_display_prefers_selected_window_when_rows_exist(self):
        InvoiceCost.objects.create(
            import_run=self.import_run,
            supply=self.supply,
            canonical_month_key='2020-08',
            source_period_start='2020-07-02T00:00:00Z',
            source_period_end='2020-08-01T00:00:00Z',
            cost=Decimal('125.06'),
        )
        InvoiceCost.objects.create(
            import_run=self.import_run,
            supply=self.supply,
            canonical_month_key='2026-05',
            source_period_start='2026-05-01T00:00:00Z',
            source_period_end='2026-05-31T23:59:59Z',
            cost=Decimal('321.11'),
        )

        rows = get_consumption_display_records(
            reporting_month='2026-05',
            data_type='invoice',
            supply_external_ids=[self.supply.external_id],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(str(rows[0]['value']), '321.110000')
        self.assertEqual(rows[0]['canonical_month_key'], '2026-05')
