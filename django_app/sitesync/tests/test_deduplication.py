from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from sitesync.services import EtainaibleSyncService
from sitesync.models import Site, Supply


class DeduplicationTest(TestCase):
    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_is_idempotent(self, mock_get):
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
                        {'id': 'acc-1', 'asset_id': 'site-1', 'name': 'Supply 1', 'type': 'electricity', 'device_id': 'dev1', 'status': 'inactive'},
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

        self.assertEqual(results_first['sites_created'], 1)
        self.assertEqual(results_first['supplies_created'], 1)
        self.assertEqual(results_second['sites_created'], 0)
        self.assertEqual(results_second['supplies_created'], 0)
        self.assertEqual(Site.objects.count(), 1)
        self.assertEqual(Supply.objects.count(), 1)
        self.assertEqual(Supply.objects.get(external_id='acc-1').status, 'inactive')

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_reconciles_deleted_sites_and_supplies(self, mock_get):
        call_state = {'run': 0}

        def side_effect(url, params=None, headers=None, timeout=None):
            if params and params.get('page') == 1 and url.endswith('/assets'):
                call_state['run'] += 1

            mock_resp = Mock()
            if url.endswith('/assets') or '/assets' in url:
                if call_state['run'] == 1:
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {
                        'data': [
                            {'id': 'site-1', 'name': 'Site 1'},
                        ],
                        'total': 1,
                    }
                else:
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {
                        'data': [
                            {'id': 'site-1', 'name': 'Site 1'},
                        ],
                        'total': 1,
                    }
                return mock_resp

            if url.endswith('/accounts') or '/accounts' in url:
                if call_state['run'] == 1:
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {
                        'data': [
                            {'id': 'acc-1', 'asset_id': 'site-1', 'name': 'Supply 1', 'type': 'electricity', 'device_id': 'dev1'},
                            {'id': 'acc-2', 'asset_id': 'site-1', 'name': 'Supply 2', 'type': 'gas', 'device_id': 'dev2'},
                        ],
                        'total': 2,
                    }
                else:
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

        self.assertEqual(results_first['sites_created'], 1)
        self.assertEqual(results_first['supplies_created'], 2)
        self.assertEqual(results_first['sites_deleted'], 0)
        self.assertEqual(results_first['supplies_deleted'], 0)

        self.assertEqual(results_second['sites_deleted'], 0)
        self.assertEqual(results_second['supplies_deleted'], 1)
        self.assertEqual(Site.objects.count(), 1)
        self.assertEqual(Supply.objects.count(), 1)
        self.assertTrue(Site.objects.filter(external_id='site-1').exists())
        self.assertTrue(Supply.objects.filter(external_id='acc-1').exists())
        self.assertFalse(Supply.objects.filter(external_id='acc-2').exists())
