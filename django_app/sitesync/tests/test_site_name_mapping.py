"""
Tests for Etainabl asset name mapping.
"""

from django.test import TestCase

from sitesync.services import EtainaibleSyncService


class SiteNameMappingTest(TestCase):
    """Verify site name mapping uses Etainabl siteName field."""

    def test_upsert_site_uses_siteName_when_name_missing(self):
        service = EtainaibleSyncService.__new__(EtainaibleSyncService)

        created = service._upsert_site({
            '_id': 'site-001',
            'siteName': '17 Pavilion Rd Knightsbridge',
            'address': {
                'streetAddress': '17 Pavilion Rd Knightsbridge',
                'region': 'London',
                'postCode': 'SW1X 0HD',
            },
        })

        self.assertTrue(created)

        from sitesync.models import Site

        site = Site.objects.get(external_id='site-001')
        self.assertEqual(site.name, '17 Pavilion Rd Knightsbridge')
        self.assertIn('London', site.description)
