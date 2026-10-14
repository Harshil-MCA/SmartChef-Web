from django.test import TestCase

from accounts.models import User
from recipes.models import RecipeRecord
from recipes.services import generate_recipe_record


class RecipeServiceTest(TestCase):
    def test_generate_recipe_record(self):
        user = User.objects.create_user(email="recipe@example.com", password="StrongPass123")
        record = generate_recipe_record(user=user, ingredients=["tomato", "onion"])
        self.assertIsInstance(record, RecipeRecord)
        self.assertEqual(record.user, user)
