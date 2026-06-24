"""
Edge case tests for site and supply behavior.
"""

from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase, override_settings

from sitesync.models import Site
from sitesync.services import EtainaibleSyncService
from sitesync.views import site_list_view


class EdgeCaseTests(TestCase):
    """Edge case coverage for empty data, timeouts, and malformed responses."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_site_list_view_handles_no_sites(self):
        request = self.factory.get('/')
        response = site_list_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('No sites available', content)

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_retries_api_timeout_and_raises_after_failures(self, mock_get):
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout('timed out')
        service = EtainaibleSyncService()
        service.max_retries = 2
        service.base_backoff = 0

        with self.assertRaises(Timeout):
            service._fetch_from_api('https://api.test/assets')

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_handles_malformed_api_response(self, mock_get):
        malformed = Mock()
        malformed.status_code = 200
        malformed.json.return_value = {'unexpected': 'payload'}
        mock_get.return_value = malformed

        service = EtainaibleSyncService()
        result = service.sync_assets()

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 0)
