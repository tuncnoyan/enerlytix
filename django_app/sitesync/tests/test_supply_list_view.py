"""
Integration tests for supply list display.
"""

from django.test import TestCase, RequestFactory
from sitesync.models import Site, Supply
from sitesync.views import supply_list_view


class SupplyListViewIntegrationTest(TestCase):
    """Integration tests for supply list view."""

    def setUp(self):
        """Create sample data for integration testing."""
        self.factory = RequestFactory()
        
        self.site1 = Site.objects.create(
            external_id='site-001',
            name='Main Distribution Center',
            description='Primary location'
        )
        self.site2 = Site.objects.create(
            external_id='site-002',
            name='Secondary Location'
        )
        
        # Create supplies for site1
        self.supply1_elec = Supply.objects.create(
            site=self.site1,
            external_id='supply-elec-001',
            name='Main Electricity Meter',
            utility_type='electricity',
            device_id='meter-elec-001',
        )
        self.supply1_gas = Supply.objects.create(
            site=self.site1,
            external_id='supply-gas-001',
            name='Primary Gas Meter',
            utility_type='gas',
            device_id='meter-gas-001',
        )
        self.supply1_water = Supply.objects.create(
            site=self.site1,
            external_id='supply-water-001',
            name='Water Supply',
            utility_type='water',
            device_id='meter-water-001',
        )
        
        # Create supply for site2
        self.supply2_elec = Supply.objects.create(
            site=self.site2,
            external_id='supply-elec-002',
            name='Secondary Electricity',
            utility_type='electricity',
            device_id='meter-elec-002',
        )

    def test_supply_list_view_returns_200(self):
        """Verify supply list view returns successful response."""
        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        
        self.assertEqual(response.status_code, 200)

    def test_supply_list_displays_all_supplies_for_site(self):
        """Verify all supplies for a site are displayed."""
        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('Main Electricity Meter', content)
        self.assertIn('Primary Gas Meter', content)
        self.assertIn('Water Supply', content)

    def test_supply_list_filters_by_site_correctly(self):
        """Verify supplies are filtered by site ID."""
        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        # Site1 supplies should be present
        self.assertIn('Main Electricity Meter', content)
        # Site2 supplies should not be present
        self.assertNotIn('Secondary Electricity', content)

    def test_supply_list_displays_utility_types(self):
        """Verify utility types are displayed for each supply."""
        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('Electricity', content)
        self.assertIn('Gas', content)
        self.assertIn('Water', content)

    def test_supply_list_displays_device_ids(self):
        """Verify device IDs are displayed."""
        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('meter-elec-001', content)
        self.assertIn('meter-gas-001', content)
        self.assertIn('meter-water-001', content)

    def test_supply_list_empty_for_site_without_supplies(self):
        """Verify empty state when site has no supplies."""
        site_empty = Site.objects.create(
            external_id='site-empty',
            name='Empty Site'
        )
        
        request = self.factory.get('/', {'site_id': site_empty.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('No supplies', content)

    def test_supply_list_missing_site_id_parameter(self):
        """Verify view handles missing site_id parameter gracefully."""
        request = self.factory.get('/')
        response = supply_list_view(request)
        
        self.assertEqual(response.status_code, 200)

    def test_supply_list_with_invalid_site_id(self):
        """Verify view handles invalid site ID gracefully."""
        request = self.factory.get('/', {'site_id': 99999})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('No supplies', content)

    def test_supply_list_groups_submeters_under_fiscal_meter(self):
        """Verify fiscal meters are shown with nested submeters."""
        Supply.objects.create(
            site=self.site1,
            external_id='supply-elec-sub-001',
            name='Level 1 Lighting Submeter',
            utility_type='electricity',
            device_id='meter-elec-sub-001',
            parent_account_id='supply-elec-001',
        )

        request = self.factory.get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Main (Fiscal)', content)
        self.assertIn('Submeter', content)
        self.assertIn('Level 1 Lighting Submeter', content)
