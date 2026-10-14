from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from ingredients.services import IngredientModelError
from nutrition.services import NutritionService
from nutrition.image_processing import weight_from_ocr_text


class NutritionServiceTest(TestCase):
    def test_nutrition_service_initializes(self):
        service = NutritionService()
        self.assertIsInstance(service.batch_lookup([]), list)

    def test_local_dataset_scales_potato_by_actual_weight(self):
        result = NutritionService().scale_nutrition("Potato", 120)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "potato")
        self.assertEqual(result["grams"], 120)
        self.assertEqual(result["calories"], 196.8)

    def test_scale_ocr_ignores_capacity_and_resolution(self):
        self.assertEqual(weight_from_ocr_text("Max. 5000g\nd=1g\n120 g"), 120)

    def test_scale_ocr_accepts_display_without_unit(self):
        self.assertEqual(weight_from_ocr_text("50"), 50)

    def test_scale_ocr_reconstructs_digit_fragments(self):
        self.assertEqual(weight_from_ocr_text("1 2 0 g"), 120)

    def test_tomato_uses_a_tomato_record_not_a_fuzzy_dish_match(self):
        result = NutritionService().scale_nutrition("tomato", 50)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "tomato cooked")
        self.assertEqual(result["grams"], 50)
        self.assertEqual(result["calories"], 11.0)
        self.assertEqual(result["protein"], 0.6)


class NutritionScanTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user(email="nutrition@example.com", password="StrongPass123"))

    def test_scale_ocr_result_survives_an_unavailable_ingredient_model(self):
        """Local OCR must still work when the ingredient model cannot load."""
        from PIL import Image

        buffer = BytesIO()
        Image.new("RGB", (20, 20), "white").save(buffer, format="JPEG")
        upload = SimpleUploadedFile("scan.jpg", buffer.getvalue(), content_type="image/jpeg")
        with patch("nutrition.views.IngredientDetectionService.detect", side_effect=IngredientModelError("model unavailable")), patch(
            "nutrition.views.read_scale_weight", return_value=120
        ), patch("nutrition.views.GeminiService.recognize_ingredients_from_image", return_value=None):
            response = self.client.post("/api/nutrition/scan/", {"image": upload}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["ingredient"])
        self.assertEqual(response.data["weight_grams"], 120)
        self.assertTrue(response.data["weight_detected"])
