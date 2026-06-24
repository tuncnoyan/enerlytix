from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from sitesync.services import EtainaibleSyncService
from sitesync.models import Site, Supply


class DeduplicationTest(TestCase):
    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_is_idempotent(self, mock_get):
        # Same mock as integration test
        def side_effect(url, params=None, headers=None, timeout=None):
            mock_resp = Mock()
            if url.endswith('/assets') or '/assets' in url:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    'data': [
                        {'id': 'site-1', 'name': 'Site 1'},
                    ],
                    'total': 1,
                }
                return mock_resp
            if url.endswith('/accounts') or '/accounts' in url:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    'data': [
                        {'id': 'acc-1', 'asset_id': 'site-1', 'name': 'Supply 1', 'type': 'electricity', 'device_id': 'dev1'},
                    ],
                    'total': 1,
                }
                return mock_resp
            mock_resp.status_code = 404
            mock_resp.json.return_value = {}
            return mock_resp

        mock_get.side_effect = side_effect

        service = EtainaibleSyncService()
        results_first = service.sync_all()
        results_second = service.sync_all()

        # First sync should create records
        self.assertEqual(results_first['sites_created'], 1)
        self.assertEqual(results_first['supplies_created'], 1)

        # Second sync should not create new records (idempotent)
        self.assertEqual(results_second['sites_created'], 0)
        self.assertEqual(results_second['supplies_created'], 0)

        # Ensure counts remain 1
        self.assertEqual(Site.objects.count(), 1)
        self.assertEqual(Supply.objects.count(), 1)
