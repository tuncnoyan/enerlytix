from django.test import TestCase
from django.db import IntegrityError
from sitesync.models import Site, Supply


class ModelsTest(TestCase):
    def test_site_and_supply_creation_and_uniqueness(self):
        s1 = Site.objects.create(external_id='s1', name='Site 1')
        self.assertEqual(Site.objects.count(), 1)

        sp1 = Supply.objects.create(site=s1, external_id='sup1', name='Supply 1', utility_type='electricity')
        self.assertEqual(Supply.objects.count(), 1)

        with self.assertRaises(IntegrityError):
            Site.objects.create(external_id='s1', name='Duplicate Site')
