"""
Integration test for sync success rate.
"""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from sitesync.models import Site, Supply
from sitesync.services import EtainaibleSyncService


class SyncSuccessRateTest(TestCase):
    """Verify that the first sync persists at least 95 percent of sample records."""

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_first_sync_persists_at_least_95_percent(self, mock_get):
        assets = [
            {'id': f'site-{index}', 'name': f'Site {index}'}
            for index in range(100)
        ]
        accounts = [
            {
                'id': f'acc-{index}',
                'asset_id': f'site-{index}',
                'name': f'Supply {index}',
                'type': 'electricity' if index % 2 == 0 else 'gas',
                'device_id': f'device-{index}',
            }
            for index in range(100)
        ]

        def side_effect(url, params=None, headers=None, timeout=None):
            response = Mock()
            if url.endswith('/assets') or '/assets' in url:
                response.status_code = 200
                response.json.return_value = {'data': assets, 'total': len(assets)}
                return response
            if url.endswith('/accounts') or '/accounts' in url:
                response.status_code = 200
                response.json.return_value = {'data': accounts, 'total': len(accounts)}
                return response
            response.status_code = 404
            response.json.return_value = {}
            return response

        mock_get.side_effect = side_effect

        service = EtainaibleSyncService()
        results = service.sync_all()

        persisted = Site.objects.count() + Supply.objects.count()
        expected = 200

        self.assertEqual(results['sites_created'], 100)
        self.assertEqual(results['supplies_created'], 100)
        self.assertGreaterEqual(persisted, int(expected * 0.95))
