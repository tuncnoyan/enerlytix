from django.test import TestCase, RequestFactory
from sitesync.models import Site, Supply
from sitesync.views import site_list_view


class SiteListViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site1 = Site.objects.create(external_id='site-1', name='Alpha Site', description='First location')
        self.site2 = Site.objects.create(external_id='site-2', name='Beta Site', description='Second location')
        Supply.objects.create(
            site=self.site1,
            external_id='supply-1',
            name='Main Meter',
            utility_type='electricity',
            device_id='dev-1',
        )

    def test_site_list_view_renders_sites(self):
        request = self.factory.get('/')
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Check for site names in the left column (site list items)
        self.assertIn('Alpha Site', content)
        self.assertIn('Beta Site', content)
        # Check for UI elements that are in the initial render
        self.assertIn('Site & Supply Dashboard', content)
        self.assertIn('Available Sites', content)

    def test_site_list_view_filters_by_query(self):
        request = self.factory.get('/', {'q': 'alpha'})
        response = site_list_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Alpha Site', content)
        self.assertNotIn('Beta Site', content)

    def test_site_list_view_renders_statistics(self):
        Supply.objects.create(
            site=self.site1,
            external_id='supply-2',
            name='Lighting Submeter',
            utility_type='electricity',
            parent_account_id='supply-1',
        )

        request = self.factory.get('/')
        response = site_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Available Sites', content)
        self.assertIn('Fiscal Meters', content)
        self.assertIn('Submeters', content)
        self.assertIn('>2<', content)
        self.assertIn('>1<', content)

    def test_site_list_view_renders_selection_controls(self):
        request = self.factory.get('/')
        response = site_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Select all', content)
        self.assertIn('Deselect all', content)
        self.assertIn('Selected Sites: 0', content)
        self.assertIn('site-selector', content)
        self.assertIn('data-fiscal-total=', content)
        self.assertIn('data-submeter-total=', content)
        self.assertIn('Refresh data', content)
