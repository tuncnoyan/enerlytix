from django.test import TestCase
from django.db import IntegrityError
from sitesync.models import Site, Supply


class ModelsTest(TestCase):
    def test_site_and_supply_creation_and_uniqueness(self):
        # Create a site
        s1 = Site.objects.create(external_id='s1', name='Site 1')
        self.assertEqual(Site.objects.count(), 1)

        # Create a supply
        sp1 = Supply.objects.create(site=s1, external_id='sup1', name='Supply 1', utility_type='electricity')
        self.assertEqual(Supply.objects.count(), 1)

        # Attempt to create another site with same external_id -> should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Site.objects.create(external_id='s1', name='Duplicate Site')
