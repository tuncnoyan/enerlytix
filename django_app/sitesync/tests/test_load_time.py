"""
Performance test for the site list page.
"""

from time import perf_counter

from django.test import RequestFactory, TestCase

from sitesync.models import Site
from sitesync.views import site_list_view


class SiteListLoadTimeTest(TestCase):
    """Performance test for rendering the site list page."""

    def setUp(self):
        self.factory = RequestFactory()
        Site.objects.bulk_create([
            Site(external_id=f'site-{index}', name=f'Site {index}')
            for index in range(1, 201)
        ])

    def test_site_list_renders_under_three_seconds(self):
        request = self.factory.get('/')
        start = perf_counter()
        response = site_list_view(request)
        elapsed = perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0)
