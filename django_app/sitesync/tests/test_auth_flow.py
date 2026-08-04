from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username='demo_user',
            email='demo@example.com',
            password='StrongPass123!',
        )

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse('sitesync:profile'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_page_shows_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('sitesync:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'demo_user')
        self.assertContains(response, 'demo@example.com')

    def test_profile_page_allows_editing_identity_fields(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('sitesync:profile'),
            {
                'username': 'updated_user',
                'first_name': 'Updated',
                'last_name': 'Name',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated_user')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertContains(response, 'Profile updated successfully.')

    def test_password_reset_page_is_available(self):
        response = self.client.get(reverse('sitesync:password_reset'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Password')

    def test_common_self_signup_routes_are_unavailable(self):
        for path in ['/signup/', '/register/', '/accounts/signup/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
