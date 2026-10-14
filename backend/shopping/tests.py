from django.conf import settings
from rest_framework.test import APIClient
from django.test import TestCase

from accounts.jwt import create_token
from accounts.models import User
from shopping.models import ShoppingItem


class ShoppingIsolationTest(TestCase):
    def test_user_specific_items(self):
        user = User.objects.create_user(email="shop@example.com", password="StrongPass123")
        ShoppingItem.objects.create(user=user, name="Tomato")
        self.assertEqual(ShoppingItem.objects.filter(user=user).count(), 1)


class ShoppingApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(email="shop-a@example.com", password="StrongPass123")
        self.user_b = User.objects.create_user(email="shop-b@example.com", password="StrongPass123")
        ShoppingItem.objects.create(user=self.user_a, name="Tomato")
        ShoppingItem.objects.create(user=self.user_b, name="Onion")

    def test_shopping_isolation_via_api(self):
        access = create_token(
            user_id=str(self.user_a.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get("/api/shopping-items/")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data["results"]]
        self.assertIn("Tomato", names)
        self.assertNotIn("Onion", names)

    def test_create_update_and_delete_item(self):
        access = create_token(
            user_id=str(self.user_a.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        create_response = self.client.post(
            "/api/shopping-items/",
            {"name": "Milk", "quantity": "2", "category": "Dairy", "notes": "Low fat"},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        item_id = create_response.data["id"]

        update_response = self.client.patch(
            f"/api/shopping-items/{item_id}/",
            {"is_purchased": True, "is_favorite": True},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(update_response.data["is_purchased"])
        self.assertTrue(update_response.data["is_favorite"])

        delete_response = self.client.delete(f"/api/shopping-items/{item_id}/")
        self.assertEqual(delete_response.status_code, 204)

    def test_cannot_modify_other_users_item(self):
        access = create_token(
            user_id=str(self.user_a.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        other_item_id = ShoppingItem.objects.get(user=self.user_b).pk
        response = self.client.patch(
            f"/api/shopping-items/{other_item_id}/",
            {"name": "Tampered"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
