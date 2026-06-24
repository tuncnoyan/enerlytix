"""
Unit tests for app settings persistence.
"""

from django.test import TestCase
from sitesync.models import AppSettings


class SettingsModelTest(TestCase):
    """Unit tests for AppSettings save and load behavior."""

    def test_app_settings_defaults(self):
        settings = AppSettings.objects.create()

        self.assertEqual(settings.etainabl_api_url, 'https://api.etainabl.com/2.0')
        self.assertEqual(settings.page_size, 50)
        self.assertEqual(settings.api_timeout, 30)

    def test_app_settings_save_and_reload(self):
        settings = AppSettings.objects.create(
            etainabl_api_url='https://api.example.com/2.0',
            page_size=100,
            api_timeout=60,
        )

        settings.page_size = 125
        settings.api_timeout = 90
        settings.save()
        settings.refresh_from_db()

        self.assertEqual(settings.etainabl_api_url, 'https://api.example.com/2.0')
        self.assertEqual(settings.page_size, 125)
        self.assertEqual(settings.api_timeout, 90)

    def test_app_settings_string_representation(self):
        settings = AppSettings.objects.create()

        self.assertEqual(str(settings), 'Application Settings')
