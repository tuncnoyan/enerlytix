"""
Contract tests for settings endpoints.
"""

from django.test import TestCase
from sitesync.models import AppSettings
from sitesync.serializers import AppSettingsSerializer


class SettingsEndpointContractTest(TestCase):
    """Contract tests for app settings serialization."""

    def setUp(self):
        self.settings = AppSettings.objects.create(
            etainabl_api_url='https://api.example.com/2.0',
            page_size=75,
            api_timeout=45,
        )

    def test_settings_serializer_response_structure(self):
        serializer = AppSettingsSerializer(self.settings)
        data = serializer.data

        required_fields = [
            'id',
            'etainabl_api_url',
            'page_size',
            'api_timeout',
            'created_at',
            'updated_at',
        ]

        for field in required_fields:
            self.assertIn(field, data)

    def test_settings_serializer_field_types(self):
        serializer = AppSettingsSerializer(self.settings)
        data = serializer.data

        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['etainabl_api_url'], str)
        self.assertIsInstance(data['page_size'], int)
        self.assertIsInstance(data['api_timeout'], int)
        self.assertIsInstance(data['created_at'], str)
        self.assertIsInstance(data['updated_at'], str)

    def test_settings_serializer_field_values(self):
        serializer = AppSettingsSerializer(self.settings)
        data = serializer.data

        self.assertEqual(data['etainabl_api_url'], 'https://api.example.com/2.0')
        self.assertEqual(data['page_size'], 75)
        self.assertEqual(data['api_timeout'], 45)

    def test_settings_serializer_readonly_fields(self):
        serializer = AppSettingsSerializer(self.settings)

        self.assertIn('id', serializer.Meta.read_only_fields)
        self.assertIn('created_at', serializer.Meta.read_only_fields)
        self.assertIn('updated_at', serializer.Meta.read_only_fields)
