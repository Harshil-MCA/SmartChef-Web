from django.test import TestCase

from accounts.models import User
from diet_planner.services import DietPlannerService


class DietPlannerServiceTest(TestCase):
    def test_generate_plan(self):
        User.objects.create_user(email="diet@example.com", password="StrongPass123")
        result = DietPlannerService().generate(age=25, weight=70, height=170, daily_budget=300, goal="Weight Loss")
        self.assertIn("breakfast", result)
