from django.conf import settings
from rest_framework.test import APIClient
from django.test import TestCase
from unittest.mock import patch

from accounts.jwt import create_token
from accounts.models import User


class UserModelTest(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="chef@example.com", password="StrongPass123")
        self.assertEqual(user.email, "chef@example.com")
        self.assertTrue(user.check_password("StrongPass123"))


class AuthApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_login_and_me(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {"email": "new@example.com", "password": "StrongPass123", "display_name": "New Chef"},
            format="json",
        )
        self.assertEqual(register_response.status_code, 201)
        self.assertIn("access", register_response.data)
        register_refresh = register_response.data["refresh"]

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "new@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 409)
        self.assertEqual(
            login_response.data["detail"],
            "Your account is already active on another device. Please log out first.",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}"
        )
        logout_response = self.client.post(
            "/api/auth/logout/", {"refresh": register_refresh}, format="json"
        )
        self.assertEqual(logout_response.status_code, 200)
        self.client.credentials()

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "new@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        access = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data["user"]["email"], "new@example.com")

    def test_invalid_login(self):
        user = User.objects.create_user(email="invalid@example.com", password="StrongPass123")
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_refresh_token_returns_new_pair(self):
        user = User.objects.create_user(email="refresh@example.com", password="StrongPass123")
        refresh = create_token(
            user_id=str(user.pk),
            token_type="refresh",
            expires_in=settings.TOKEN_REFRESH_LIFETIME,
        )
        response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    @patch("accounts.views.verify_id_token")
    def test_firebase_exchange_links_existing_user_and_enforces_single_session(self, verify):
        user = User.objects.create_user(email="firebase@example.com", password="legacy")
        verify.return_value = {
            "firebase_uid": "firebase-uid-1",
            "email": "firebase@example.com",
            "display_name": "Firebase Chef",
            "photo_url": "",
        }
        payload = {"id_token": "test-id-token", "platform": "flutter"}
        first = self.client.post("/api/auth/firebase/", payload, format="json")
        self.assertEqual(first.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.firebase_uid, "firebase-uid-1")
        self.assertEqual(User.objects.filter(email="firebase@example.com").count(), 1)

        second = self.client.post("/api/auth/firebase/", payload, format="json")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(
            second.data["detail"],
            "Your account is already active on another device. Please log out first.",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first.data['access']}")
        logout = self.client.post(
            "/api/auth/logout/", {"refresh": first.data["refresh"]}, format="json"
        )
        self.assertEqual(logout.status_code, 200)
        self.client.credentials()

        after_logout = self.client.post("/api/auth/firebase/", payload, format="json")
        self.assertEqual(after_logout.status_code, 200)
