from django.conf import settings
from rest_framework.test import APIClient
from django.test import TestCase

from accounts.jwt import create_token
from accounts.models import User
from history.models import HistoryEntry


class HistoryIsolationTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123")
        self.user_b = User.objects.create_user(email="b@example.com", password="StrongPass123")
        HistoryEntry.objects.create(user=self.user_a, entry_type="recipe", title="User A Recipe")
        HistoryEntry.objects.create(user=self.user_b, entry_type="recipe", title="User B Recipe")

    def test_history_scoped_to_user(self):
        self.assertEqual(HistoryEntry.objects.filter(user=self.user_a).count(), 1)
        self.assertEqual(HistoryEntry.objects.filter(user=self.user_b).count(), 1)


class HistoryApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(email="api-a@example.com", password="StrongPass123")
        self.user_b = User.objects.create_user(email="api-b@example.com", password="StrongPass123")
        HistoryEntry.objects.create(user=self.user_a, entry_type="recipe", title="A Recipe")
        HistoryEntry.objects.create(user=self.user_b, entry_type="recipe", title="B Recipe")

    def test_history_isolation_via_api(self):
        access = create_token(
            user_id=str(self.user_a.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get("/api/history/")
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("A Recipe", titles)
        self.assertNotIn("B Recipe", titles)
