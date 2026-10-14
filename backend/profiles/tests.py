from django.test import TestCase
from rest_framework.test import APIClient

from accounts.jwt import create_token
from accounts.models import User
from django.conf import settings


class ProfileSignalTest(TestCase):
    def test_profile_created_with_user(self):
        user = User.objects.create_user(email="profile@example.com", password="StrongPass123")
        self.assertTrue(hasattr(user, "profile"))


class ProfileApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="profile-api@example.com", password="StrongPass123")

    def test_profile_update_via_api(self):
        access = create_token(
            user_id=str(self.user.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.patch(
            "/api/profile/me/",
            {"display_name": "Kitchen Lead", "theme_preference": "dark", "unit_preference": "imperial"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["display_name"], "Kitchen Lead")
        self.assertEqual(response.data["theme_preference"], "dark")
        self.assertEqual(response.data["unit_preference"], "imperial")
