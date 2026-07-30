"""
Integration tests for supply list display.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from sitesync.models import Site, Supply
from sitesync.views import supply_list_view


class SupplyListViewIntegrationTest(TestCase):
    """Integration tests for supply list view."""

    def setUp(self):
        """Create sample data for integration testing."""
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='supplyuser', password='pass123')
        
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

    def _auth_get(self, path='/', data=None):
        request = self.factory.get(path, data or {})
        request.user = self.user
        return request

    def test_supply_list_view_returns_200(self):
        """Verify supply list view returns successful response."""
        request = self._auth_get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        
        self.assertEqual(response.status_code, 200)

    def test_supply_list_displays_all_supplies_for_site(self):
        """Verify all supplies for a site are displayed."""
        request = self._auth_get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('Main Electricity Meter', content)
        self.assertIn('Primary Gas Meter', content)
        self.assertIn('Water Supply', content)

    def test_supply_list_filters_by_site_correctly(self):
        """Verify supplies are filtered by site ID."""
        request = self._auth_get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        # Site1 supplies should be present
        self.assertIn('Main Electricity Meter', content)
        # Site2 supplies should not be present
        self.assertNotIn('Secondary Electricity', content)

    def test_supply_list_displays_utility_types(self):
        """Verify utility types are displayed for each supply."""
        request = self._auth_get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('Electricity', content)
        self.assertIn('Gas', content)
        self.assertIn('Water', content)

    def test_supply_list_displays_device_ids(self):
        """Verify device IDs are displayed."""
        request = self._auth_get('/', {'site_id': self.site1.id})
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
        
        request = self._auth_get('/', {'site_id': site_empty.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')
        
        self.assertIn('No supplies', content)

    def test_supply_list_missing_site_id_parameter(self):
        """Verify view handles missing site_id parameter gracefully."""
        request = self._auth_get('/')
        response = supply_list_view(request)
        
        self.assertEqual(response.status_code, 200)

    def test_supply_list_with_invalid_site_id(self):
        """Verify view handles invalid site ID gracefully."""
        request = self._auth_get('/', {'site_id': 99999})
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

        request = self._auth_get('/', {'site_id': self.site1.id})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Main (Fiscal)', content)
        self.assertIn('Submeter', content)
        self.assertIn('Level 1 Lighting Submeter', content)

    def test_supply_list_filters_by_utility_type(self):
        """Verify utility type filter only shows matching supplies."""
        request = self._auth_get('/', {'site_id': self.site1.id, 'utility_type': 'gas'})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Primary Gas Meter', content)
        self.assertNotIn('Main Electricity Meter', content)
        self.assertNotIn('Water Supply', content)
        self.assertIn('Site: <strong>Main Distribution Center</strong>', content)
        self.assertIn('Utility: <strong>Gas</strong>', content)
        self.assertIn('Meter Type: <strong>All</strong>', content)

    def test_supply_list_filters_by_meter_type_sub_and_updates_counts(self):
        """Verify submeter filter applies and reports filtered fiscal/sub counts."""
        Supply.objects.create(
            site=self.site1,
            external_id='supply-elec-sub-002',
            name='Ground Floor Lighting Submeter',
            utility_type='electricity',
            device_id='meter-elec-sub-002',
            parent_account_id='supply-elec-001',
        )

        request = self._auth_get('/', {'site_id': self.site1.id, 'meter_type': 'sub'})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Ground Floor Lighting Submeter', content)
        self.assertIn('data-fiscal-count="0"', content)
        self.assertIn('data-submeter-count="1"', content)
        self.assertIn('Meter Type: <strong>Submeter</strong>', content)
        self.assertNotIn('Main (Fiscal)', content)

    def test_supply_list_combines_supplies_from_multiple_selected_sites(self):
        """Verify site_ids includes supplies across all selected sites."""
        request = self._auth_get('/', {'site_ids': f'{self.site1.id},{self.site2.id}'})
        response = supply_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Main Electricity Meter', content)
        self.assertIn('Secondary Electricity', content)
        self.assertIn('Site: <strong>2 sites selected</strong>', content)
        self.assertIn('data-site-count="2"', content)
