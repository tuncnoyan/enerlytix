"""
Tests for Etainabl pagination behavior.
"""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from sitesync.models import Site, Supply
from sitesync.services import EtainaibleSyncService


class SyncPaginationTest(TestCase):
    """Ensure sync traverses multiple pages and links supplies by assetId."""

    @override_settings(ETAINABL_API_KEY='testkey', ETAINABL_API_URL='https://api.test')
    @patch('sitesync.services.requests.get')
    def test_sync_fetches_multiple_pages_and_links_supplies(self, mock_get):
        total_assets = 60
        total_accounts = 75

        assets = [
            {'_id': f'site-{i}', 'siteName': f'Site {i}'}
            for i in range(total_assets)
        ]
        accounts = [
            {
                '_id': f'acc-{i}',
                'assetId': f'site-{i % total_assets}',
                'name': f'Account {i}',
                'type': 'electricity',
                'deviceId': f'device-{i}',
            }
            for i in range(total_accounts)
        ]

        def page_slice(items, page, limit):
            start = (page - 1) * limit
            end = start + limit
            return items[start:end], start

        def side_effect(url, params=None, headers=None, timeout=None):
            page = int((params or {}).get('page', 1))
            limit = int((params or {}).get('limit', 50))

            response = Mock()
            response.status_code = 200

            if '/assets' in url:
                page_items, skip = page_slice(assets, page, limit)
                response.json.return_value = {
                    'data': page_items,
                    'total': total_assets,
                    'limit': limit,
                    'skip': skip,
                }
                return response

            if '/accounts' in url:
                page_items, skip = page_slice(accounts, page, limit)
                response.json.return_value = {
                    'data': page_items,
                    'total': total_accounts,
                    'limit': limit,
                    'skip': skip,
                }
                return response

            response.status_code = 404
            response.json.return_value = {}
            return response

        mock_get.side_effect = side_effect

        service = EtainaibleSyncService()
        results = service.sync_all()

        self.assertEqual(results['sites_created'], total_assets)
        self.assertEqual(results['supplies_created'], total_accounts)
        self.assertEqual(Site.objects.count(), total_assets)
        self.assertEqual(Supply.objects.count(), total_accounts)
