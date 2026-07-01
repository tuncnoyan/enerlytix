from decimal import Decimal

from django.test import TestCase

from sitesync.models import ImportRun, Site, Supply
from sitesync.services import upsert_invoice_record


class InvoiceMappingTests(TestCase):
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
            reporting_month='2006-11',
            status=ImportRun.STATUS_IN_PROGRESS,
            affected_supply_count=1,
        )

    def test_upsert_invoice_record_uses_values_dates_and_net_total_cost(self):
        row = {
            '_id': 'invoice-1',
            'values': {
                'invoiceNumber': '0007',
                'startDate': '2006-08-18T00:00:00.000Z',
                'endDate': '2006-11-20T00:00:00.000Z',
                'netTotalCost': 357.9,
            },
        }

        invoice, created = upsert_invoice_record(self.import_run, self.supply, row)

        self.assertTrue(created)
        self.assertEqual(invoice.source_period_start.isoformat(), '2006-08-18T00:00:00+00:00')
        self.assertEqual(invoice.source_period_end.isoformat(), '2006-11-20T00:00:00+00:00')
        self.assertEqual(invoice.cost, Decimal('357.9'))
        self.assertEqual(invoice.invoice_metadata.get('invoiceNumber'), '0007')

    def test_upsert_invoice_record_prefers_net_total_cost_when_other_cost_fields_exist(self):
        row = {
            'startDate': '2026-01-01T00:00:00.000Z',
            'endDate': '2026-02-01T00:00:00.000Z',
            'cost': 999,
            'amount': 888,
            'values': {
                'netTotalCost': 123.45,
            },
        }

        invoice, _ = upsert_invoice_record(self.import_run, self.supply, row)

        self.assertEqual(invoice.cost, Decimal('123.45'))
