from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from sitesync.services import EtainaibleSyncService
from sitesync.models import Site, Supply


class EtainablSyncIntegrationTest(TestCase):
    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_full_sync_creates_sites_and_supplies(self, mock_get):
        def side_effect(url, params=None, headers=None, timeout=None):
            mock_resp = Mock()
            if url.endswith('/assets') or '/assets' in url:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    'data': [
                        {'id': 'site-1', 'name': 'Site 1', 'description': 'Desc1'},
                        {'id': 'site-2', 'name': 'Site 2', 'description': 'Desc2'},
                    ],
                    'total': 2,
                }
                return mock_resp
            if url.endswith('/accounts') or '/accounts' in url:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    'data': [
                        {'id': 'acc-1', 'asset_id': 'site-1', 'name': 'Supply 1', 'type': 'electricity', 'device_id': 'dev1'},
                        {'id': 'acc-2', 'asset_id': 'site-2', 'name': 'Supply 2', 'type': 'gas', 'device_id': 'dev2'},
                    ],
                    'total': 2,
                }
                return mock_resp
            mock_resp.status_code = 404
            mock_resp.json.return_value = {}
            return mock_resp

        mock_get.side_effect = side_effect

        service = EtainaibleSyncService()
        results = service.sync_all()

        self.assertEqual(results['sites_created'], 2)
        self.assertEqual(results['supplies_created'], 2)
        self.assertEqual(Site.objects.count(), 2)
        self.assertEqual(Supply.objects.count(), 2)
