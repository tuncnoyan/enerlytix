"""Tests for page-based invoice pagination (replacing the broken skip param)."""

from unittest.mock import patch

from django.test import TestCase

from sitesync.api_client import EtainablApiClient
from sitesync.models import AppSettings, Site, Supply
from sitesync.services import ConsumptionImportService


class InvoicePaginationApiClientTest(TestCase):
    """Validate EtainablApiClient.get_invoices pages through all results."""

    def setUp(self):
        self.client = EtainablApiClient(api_key='test-key', base_url='https://api.test', timeout=5)

    def test_pages_through_multiple_pages_using_total(self):
        page_1 = {'total': 5, 'limit': 2, 'data': [{'id': 1}, {'id': 2}]}
        page_2 = {'total': 5, 'limit': 2, 'data': [{'id': 3}, {'id': 4}]}
        page_3 = {'total': 5, 'limit': 2, 'data': [{'id': 5}]}

        with patch.object(EtainablApiClient, 'get', side_effect=[page_1, page_2, page_3]) as mock_get:
            rows = self.client.get_invoices(account_id='acc-1', limit=2, start_page=1)

        self.assertEqual([row['id'] for row in rows], [1, 2, 3, 4, 5])
        self.assertEqual(mock_get.call_count, 3)
        first_call_params = mock_get.call_args_list[0].kwargs['params']
        self.assertEqual(first_call_params, {'accountId': 'acc-1', 'limit': 2, 'page': 1})
        third_call_params = mock_get.call_args_list[2].kwargs['params']
        self.assertEqual(third_call_params, {'accountId': 'acc-1', 'limit': 2, 'page': 3})

    def test_starts_from_configured_start_page(self):
        page_2 = {'total': 6, 'limit': 2, 'data': [{'id': 3}, {'id': 4}]}
        page_3 = {'total': 6, 'limit': 2, 'data': [{'id': 5}, {'id': 6}]}

        with patch.object(EtainablApiClient, 'get', side_effect=[page_2, page_3]) as mock_get:
            rows = self.client.get_invoices(account_id='acc-1', limit=2, start_page=2)

        self.assertEqual([row['id'] for row in rows], [3, 4, 5, 6])
        first_call_params = mock_get.call_args_list[0].kwargs['params']
        self.assertEqual(first_call_params, {'accountId': 'acc-1', 'limit': 2, 'page': 2})

    def test_stops_on_short_page_when_total_missing(self):
        page_1 = {'data': [{'id': 1}, {'id': 2}]}
        page_2 = {'data': [{'id': 3}]}

        with patch.object(EtainablApiClient, 'get', side_effect=[page_1, page_2]) as mock_get:
            rows = self.client.get_invoices(account_id='acc-1', limit=2, start_page=1)

        self.assertEqual([row['id'] for row in rows], [1, 2, 3])
        self.assertEqual(mock_get.call_count, 2)

    def test_stops_immediately_on_empty_page(self):
        with patch.object(EtainablApiClient, 'get', return_value={'data': []}) as mock_get:
            rows = self.client.get_invoices(account_id='acc-1', limit=100, start_page=1)

        self.assertEqual(rows, [])
        self.assertEqual(mock_get.call_count, 1)


class ConsumptionImportServiceInvoiceSettingsTest(TestCase):
    """Validate invoice pagination settings are read from AppSettings and applied."""

    def setUp(self):
        self.site = Site.objects.create(external_id='site-1', name='Site 1')
        self.supply = Supply.objects.create(
            site=self.site,
            external_id='supply-1',
            name='Supply 1',
            utility_type='electricity',
        )

    def test_uses_configured_invoice_page_limit_and_start_page(self):
        AppSettings.objects.create(invoice_page_limit=250, invoice_start_page=4)

        service = ConsumptionImportService()
        self.assertEqual(service.invoice_page_limit, 250)
        self.assertEqual(service.invoice_start_page, 4)

        with patch.object(service, '_account_id_candidates', return_value=[self.supply.external_id]), \
                patch.object(service.client, 'get_invoices', return_value=[]) as mock_get_invoices:
            service._fetch_invoices_for_supply(supply=self.supply)

        mock_get_invoices.assert_called_once_with(
            account_id=self.supply.external_id,
            limit=250,
            start_page=4,
        )

    def test_defaults_to_100_and_page_1_without_explicit_settings(self):
        AppSettings.objects.create()

        service = ConsumptionImportService()
        self.assertEqual(service.invoice_page_limit, 100)
        self.assertEqual(service.invoice_start_page, 1)
