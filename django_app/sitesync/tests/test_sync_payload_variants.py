"""
Integration tests for Etainabl payload key variants.
"""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from sitesync.models import Site, Supply
from sitesync.services import EtainaibleSyncService


class SyncPayloadVariantsTest(TestCase):
    """Ensure sync works with id and key variants from Etainabl payloads."""

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_supports__id_and_assetId_fields(self, mock_get):
        def side_effect(url, params=None, headers=None, timeout=None):
            response = Mock()
            response.status_code = 200

            if '/assets' in url:
                response.json.return_value = {
                    'data': [
                        {'_id': 'site-abc', 'name': 'Variant Site'}
                    ],
                    'total': 1,
                }
                return response

            if '/accounts' in url:
                response.json.return_value = {
                    'data': [
                        {
                            '_id': 'acc-abc',
                            'assetId': 'site-abc',
                            'name': 'Variant Supply',
                            'type': 'electricity',
                            'deviceId': 'device-variant',
                        }
                    ],
                    'total': 1,
                }
                return response

            response.status_code = 404
            response.json.return_value = {}
            return response

        mock_get.side_effect = side_effect

        service = EtainaibleSyncService()
        result = service.sync_all()

        self.assertEqual(result['sites_created'], 1)
        self.assertEqual(result['supplies_created'], 1)
        self.assertEqual(Site.objects.count(), 1)
        self.assertEqual(Supply.objects.count(), 1)
        self.assertEqual(Site.objects.first().external_id, 'site-abc')
        self.assertEqual(Supply.objects.first().external_id, 'acc-abc')
