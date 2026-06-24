"""
Tests for the manual sync refresh endpoint.
"""

import json
from unittest.mock import patch

from django.test import RequestFactory, TestCase

from sitesync.views import manual_sync_view


class ManualSyncViewTest(TestCase):
    """Tests for the manual sync trigger view."""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('sitesync.views.EtainaibleSyncService')
    def test_manual_sync_redirects_on_success(self, mock_service_class):
        mock_service = mock_service_class.return_value
        mock_service.sync_all.return_value = {
            'sites_created': 1,
            'sites_updated': 0,
            'supplies_created': 1,
            'supplies_updated': 0,
        }

        request = self.factory.post('/sync/')
        response = manual_sync_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/?sync=success', response.url)
        mock_service.sync_all.assert_called_once()

    @patch('sitesync.views.EtainaibleSyncService')
    def test_manual_sync_returns_json_error_on_failure(self, mock_service_class):
        mock_service = mock_service_class.return_value
        mock_service.sync_all.side_effect = RuntimeError('boom')

        request = self.factory.post('/sync/')
        response = manual_sync_view(request)

        self.assertEqual(response.status_code, 500)
        payload = json.loads(response.content.decode('utf-8'))
        self.assertEqual(payload['error']['message'], 'Unable to complete sync')
        self.assertIn('boom', payload['error']['details'])
