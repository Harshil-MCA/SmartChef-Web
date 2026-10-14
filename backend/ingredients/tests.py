import os
from tempfile import NamedTemporaryFile

from PIL import Image
from django.test import TestCase

from ingredients.services import IngredientDetectionService


class IngredientDetectionServiceTest(TestCase):
    def test_detection_returns_result(self):
        image = Image.new("RGB", (32, 32), color=(240, 60, 50))
        temp_file = NamedTemporaryFile(suffix=".png", delete=False)
        try:
            image.save(temp_file, format="PNG")
            temp_file.close()
            result = IngredientDetectionService().detect(temp_file.name, "tomato.png")
            self.assertGreaterEqual(result.confidence, 0)
        finally:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
