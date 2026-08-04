from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user_model.objects.create_user(
            username='reset_user',
            email='reset@example.com',
            password='StrongPass123!',
        )

    def test_password_reset_submits_email_and_shows_confirmation(self):
        response = self.client.post(
            reverse('sitesync:password_reset'),
            {'email': 'reset@example.com'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'If an account exists')
