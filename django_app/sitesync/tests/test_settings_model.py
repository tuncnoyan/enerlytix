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
        self.assertEqual(float(settings.electricity_benchmark_intensity), 0.0)
        self.assertEqual(float(settings.gas_benchmark_intensity), 0.0)
        self.assertEqual(float(settings.water_benchmark_intensity), 0.0)

    def test_app_settings_save_and_reload(self):
        settings = AppSettings.objects.create(
            etainabl_api_url='https://api.example.com/2.0',
            page_size=100,
            api_timeout=60,
            electricity_benchmark_intensity=85.5,
            gas_benchmark_intensity=55.25,
            water_benchmark_intensity=1.75,
        )

        settings.page_size = 125
        settings.api_timeout = 90
        settings.electricity_benchmark_intensity = 92.125
        settings.gas_benchmark_intensity = 61.5
        settings.water_benchmark_intensity = 2.125
        settings.save()
        settings.refresh_from_db()

        self.assertEqual(settings.etainabl_api_url, 'https://api.example.com/2.0')
        self.assertEqual(settings.page_size, 125)
        self.assertEqual(settings.api_timeout, 90)
        self.assertEqual(float(settings.electricity_benchmark_intensity), 92.125)
        self.assertEqual(float(settings.gas_benchmark_intensity), 61.5)
        self.assertEqual(float(settings.water_benchmark_intensity), 2.125)

    def test_app_settings_string_representation(self):
        settings = AppSettings.objects.create()

        self.assertEqual(str(settings), 'Application Settings')
