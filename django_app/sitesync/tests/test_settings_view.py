"""
Integration tests for the settings page.
"""

from django.test import RequestFactory, TestCase
from sitesync.models import AppSettings
from sitesync.views import settings_panel_view


class SettingsViewIntegrationTest(TestCase):
    """Integration tests for the settings panel view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.settings = AppSettings.objects.create(
            etainabl_api_url='https://api.etainabl.com/2.0',
            page_size=50,
            api_timeout=30,
        )

    def test_settings_page_renders_current_values(self):
        request = self.factory.get('/settings/')
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Settings', content)
        self.assertIn('https://api.etainabl.com/2.0', content)
        self.assertIn('50', content)
        self.assertIn('30', content)

    def test_settings_page_persists_valid_post(self):
        request = self.factory.post('/settings/', data={
            'etainabl_api_url': 'https://api.updated.example.com/2.0',
            'page_size': 75,
            'api_timeout': 45,
        })
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.etainabl_api_url, 'https://api.updated.example.com/2.0')
        self.assertEqual(self.settings.page_size, 75)
        self.assertEqual(self.settings.api_timeout, 45)

    def test_settings_page_rejects_invalid_post(self):
        request = self.factory.post('/settings/', data={
            'etainabl_api_url': 'not-a-url',
            'page_size': -1,
            'api_timeout': 0,
        })
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Enter a valid URL', content)
