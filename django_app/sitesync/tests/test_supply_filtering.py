"""
Unit tests for supply filtering by site.
"""

from django.test import TestCase
from sitesync.models import Site, Supply


class SupplyFilteringTest(TestCase):
    """Unit tests for supply filtering logic."""

    def setUp(self):
        """Create multiple sites and supplies for filtering tests."""
        self.site1 = Site.objects.create(
            external_id='site-1',
            name='Site Alpha'
        )
        self.site2 = Site.objects.create(
            external_id='site-2',
            name='Site Beta'
        )
        
        # Create supplies for site1
        self.supply1_1 = Supply.objects.create(
            site=self.site1,
            external_id='supply-1-1',
            name='Electricity Meter',
            utility_type='electricity',
        )
        self.supply1_2 = Supply.objects.create(
            site=self.site1,
            external_id='supply-1-2',
            name='Gas Meter',
            utility_type='gas',
        )
        
        # Create supplies for site2
        self.supply2_1 = Supply.objects.create(
            site=self.site2,
            external_id='supply-2-1',
            name='Water Meter',
            utility_type='water',
        )

    def test_filter_supplies_by_site(self):
        """Verify supplies can be filtered by site."""
        site1_supplies = Supply.objects.filter(site=self.site1)
        
        self.assertEqual(site1_supplies.count(), 2)
        self.assertIn(self.supply1_1, site1_supplies)
        self.assertIn(self.supply1_2, site1_supplies)
        self.assertNotIn(self.supply2_1, site1_supplies)

    def test_filter_supplies_by_site_returns_empty(self):
        """Verify filtering returns empty when site has no supplies."""
        site3 = Site.objects.create(external_id='site-3', name='Site Gamma')
        supplies = Supply.objects.filter(site=site3)
        
        self.assertEqual(supplies.count(), 0)

    def test_supplies_ordered_by_name(self):
        """Verify supplies are correctly ordered by name."""
        site1_supplies = Supply.objects.filter(site=self.site1).order_by('name')
        
        self.assertEqual(site1_supplies[0].name, 'Electricity Meter')
        self.assertEqual(site1_supplies[1].name, 'Gas Meter')

    def test_supplies_ordered_by_utility_type(self):
        """Verify supplies can be ordered by utility type."""
        all_supplies = Supply.objects.all().order_by('utility_type')
        
        self.assertEqual(all_supplies[0].utility_type, 'electricity')
        self.assertEqual(all_supplies[1].utility_type, 'gas')
        self.assertEqual(all_supplies[2].utility_type, 'water')

    def test_multiple_supplies_same_site_different_types(self):
        """Verify site can have multiple supplies of different utility types."""
        site1_supplies = Supply.objects.filter(site=self.site1)
        utility_types = [s.utility_type for s in site1_supplies]
        
        self.assertIn('electricity', utility_types)
        self.assertIn('gas', utility_types)
        self.assertEqual(len(utility_types), 2)

    def test_supply_count_per_site(self):
        """Verify supply count calculation per site."""
        site1_count = Supply.objects.filter(site=self.site1).count()
        site2_count = Supply.objects.filter(site=self.site2).count()
        
        self.assertEqual(site1_count, 2)
        self.assertEqual(site2_count, 1)

    def test_filter_by_site_id(self):
        """Verify filtering by site ID (common query pattern)."""
        supplies = Supply.objects.filter(site_id=self.site1.id)
        
        self.assertEqual(supplies.count(), 2)
        for supply in supplies:
            self.assertEqual(supply.site_id, self.site1.id)

    def test_filter_by_utility_type_within_site(self):
        """Verify filtering by utility type within a site."""
        electricity_supplies = Supply.objects.filter(
            site=self.site1,
            utility_type='electricity'
        )
        
        self.assertEqual(electricity_supplies.count(), 1)
        self.assertEqual(electricity_supplies[0].name, 'Electricity Meter')
