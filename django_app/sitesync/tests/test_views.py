from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch
from sitesync.models import Site, Supply
from sitesync.views import site_list_view


class SiteListViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='viewer', password='pass123')
        self.site1 = Site.objects.create(external_id='site-1', name='Alpha Site', description='First location')
        self.site2 = Site.objects.create(external_id='site-2', name='Beta Site', description='Second location')
        Supply.objects.create(
            site=self.site1,
            external_id='supply-1',
            name='Main Meter',
            utility_type='electricity',
            device_id='dev-1',
        )

    def _auth_get(self, path='/', data=None):
        request = self.factory.get(path, data or {})
        request.user = self.user
        return request

    def test_site_list_view_renders_sites(self):
        request = self._auth_get('/')
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
        request = self._auth_get('/', {'q': 'alpha'})
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

        request = self._auth_get('/')
        response = site_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Available Sites', content)
        self.assertIn('Supply Details', content)
        self.assertIn('Selected Sites: 0', content)
        self.assertNotIn('Fiscal Meters', content)
        self.assertNotIn('Submeters', content)

    def test_site_list_view_renders_selection_controls(self):
        request = self._auth_get('/')
        response = site_list_view(request)
        content = response.content.decode('utf-8')

        self.assertIn('Select all', content)
        self.assertIn('Deselect all', content)
        self.assertIn('Selected Sites: 0', content)
        self.assertIn('site-selector', content)
        self.assertIn('data-fiscal-total=', content)
        self.assertIn('data-submeter-total=', content)
        self.assertIn('Create Report', content)
        self.assertIn('report-end-month', content)
        self.assertIn('report-refresh-mode', content)
        self.assertIn('Refresh data before opening report', content)

    @patch('sitesync.views.render')
    def test_site_list_view_sorts_names_ascending(self, mock_render):
        mock_render.return_value = Mock(status_code=200)
        Site.objects.create(external_id='site-3', name='aardvark house', description='Third location')
        request = self._auth_get('/')
        response = site_list_view(request)

        self.assertEqual(response.status_code, 200)
        rendered_context = mock_render.call_args.args[2]
        rendered_names = [site.name for site in rendered_context['sites']]
        self.assertEqual(rendered_names, ['aardvark house', 'Alpha Site', 'Beta Site'])
