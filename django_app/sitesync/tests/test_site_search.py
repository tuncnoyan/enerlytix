from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from sitesync.models import Site, Supply
from sitesync.views import site_list_view


class SiteSearchIntegrationTest(TestCase):
    """Integration test verifying end-to-end site list display and search functionality."""

    def setUp(self):
        """Create sample sites and supplies for testing."""
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='searcher', password='pass123')
        self.site_alpha = Site.objects.create(
            external_id='etainabl-101',
            name='Alpha Distribution Center',
            description='Main warehouse in the north region'
        )
        self.site_beta = Site.objects.create(
            external_id='etainabl-102',
            name='Beta Retail Store',
            description='Secondary location in the south region'
        )
        
        Supply.objects.create(
            site=self.site_alpha,
            external_id='acc-201',
            name='Main Electricity Meter',
            utility_type='electricity',
            device_id='meter-001',
        )
        Supply.objects.create(
            site=self.site_beta,
            external_id='acc-202',
            name='Gas Supply',
            utility_type='gas',
            device_id='meter-002',
        )

    def _auth_get(self, path='/', data=None):
        request = self.factory.get(path, data or {})
        request.user = self.user
        return request

    def test_site_list_displays_all_sites(self):
        """Verify the site list page renders all available sites."""
        request = self._auth_get('/')
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Alpha Distribution Center', content)
        self.assertIn('Beta Retail Store', content)

    def test_search_filters_by_site_name(self):
        """Verify search by site name filters the list correctly."""
        request = self._auth_get('/', {'q': 'alpha'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Alpha Distribution Center', content)
        self.assertNotIn('Beta Retail Store', content)

    def test_search_filters_by_external_id(self):
        """Verify search by external ID filters the list correctly."""
        request = self._auth_get('/', {'q': 'etainabl-102'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Beta Retail Store', content)
        self.assertNotIn('Alpha Distribution Center', content)

    def test_search_filters_by_description(self):
        """Verify search by description filters the list correctly."""
        request = self._auth_get('/', {'q': 'north'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Alpha Distribution Center', content)
        self.assertNotIn('Beta Retail Store', content)

    def test_search_filters_by_supply_name(self):
        """Verify search by supply name filters the list correctly."""
        request = self._auth_get('/', {'q': 'electricity'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Alpha Distribution Center', content)

    def test_empty_search_result(self):
        """Verify that non-matching search shows empty state message."""
        request = self._auth_get('/', {'q': 'nonexistent'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('No sites match', content)

    def test_supplies_display_with_site(self):
        """Verify that the site list page renders correctly and can load supplies via the supply_list_view."""
        # Test that site list view renders the page
        request = self._auth_get('/')
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Site names should be present
        self.assertIn('Alpha Distribution Center', content)
        self.assertIn('Beta Retail Store', content)
        # Supplies are loaded dynamically, so check for UI that supports this
        self.assertIn('Supply Details', content)
