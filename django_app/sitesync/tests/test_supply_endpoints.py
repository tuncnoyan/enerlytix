"""
Contract tests for supply endpoints.
Validates the expected JSON response structure and field types.
"""

from django.test import TestCase
from sitesync.models import Site, Supply
from sitesync.serializers import SupplySerializer


class SupplyEndpointContractTest(TestCase):
    """Contract test for supply list endpoint response structure."""

    def setUp(self):
        """Create sample site and supplies for contract validation."""
        self.site = Site.objects.create(
            external_id='site-001',
            name='Test Site'
        )
        self.supply = Supply.objects.create(
            site=self.site,
            external_id='supply-001',
            name='Main Meter',
            utility_type='electricity',
            device_id='device-123',
        )

    def test_supply_serializer_response_structure(self):
        """Verify supply serializer produces correct JSON structure."""
        serializer = SupplySerializer(self.supply)
        data = serializer.data
        
        # Verify required fields exist
        required_fields = [
            'id', 'external_id', 'name', 'utility_type',
            'utility_type_display', 'device_id', 'parent_account_id', 'created_at', 'updated_at'
        ]
        for field in required_fields:
            self.assertIn(field, data)

    def test_supply_serializer_field_types(self):
        """Verify field types in serialized supply data."""
        serializer = SupplySerializer(self.supply)
        data = serializer.data
        
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['external_id'], str)
        self.assertIsInstance(data['name'], str)
        self.assertIsInstance(data['utility_type'], str)
        self.assertIsInstance(data['utility_type_display'], str)
        self.assertIsInstance(data['device_id'], str)
        self.assertIn('parent_account_id', data)

    def test_supply_serializer_field_values(self):
        """Verify serialized field values match model data."""
        serializer = SupplySerializer(self.supply)
        data = serializer.data
        
        self.assertEqual(data['external_id'], 'supply-001')
        self.assertEqual(data['name'], 'Main Meter')
        self.assertEqual(data['utility_type'], 'electricity')
        self.assertEqual(data['utility_type_display'], 'Electricity')
        self.assertEqual(data['device_id'], 'device-123')
        self.assertIsNone(data['parent_account_id'])

    def test_supply_list_contract_multiple_supplies(self):
        """Verify serializer handles multiple supplies correctly."""
        supply2 = Supply.objects.create(
            site=self.site,
            external_id='supply-002',
            name='Gas Meter',
            utility_type='gas',
            device_id='device-456',
        )
        
        supplies = Supply.objects.filter(site=self.site)
        serializer = SupplySerializer(supplies, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        # Supplies are ordered by name, so check by name
        utility_types = {item['name']: item['utility_type'] for item in data}
        self.assertEqual(utility_types['Main Meter'], 'electricity')
        self.assertEqual(utility_types['Gas Meter'], 'gas')

    def test_supply_endpoint_readonly_fields(self):
        """Verify that id and timestamps are read-only in serializer."""
        serializer = SupplySerializer(self.supply)
        
        # Read-only fields should be present in serialization output
        self.assertIn('id', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)
        
        # Verify these fields are not in writable fields
        self.assertIn('id', serializer.Meta.read_only_fields)
        self.assertIn('created_at', serializer.Meta.read_only_fields)
        self.assertIn('updated_at', serializer.Meta.read_only_fields)
