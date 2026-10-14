from __future__ import annotations

from io import BytesIO
from PIL import Image, ImageOps
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from history.models import HistoryEntry
from nutrition.serializers import NutritionLookupSerializer
from nutrition.services import NutritionService
from ai.services import GeminiService
from ingredients.services import IngredientDetectionService, IngredientModelError
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from nutrition.image_processing import normalise_weight, read_scale_weight


class NutritionLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NutritionLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = NutritionService()

        ingredient = serializer.validated_data.get("ingredient", "").strip()
        ingredients = serializer.validated_data.get("ingredients") or ([] if not ingredient else [ingredient])
        grams = serializer.validated_data.get("grams")

        matches = []
        for item in ingredients:
            if grams is not None:
                match = service.scale_nutrition(item, grams)
            else:
                lookup = service.lookup(item)
                match = lookup["nutrition"] | {"name": lookup["name"]} if lookup else None
            if match:
                matches.append(match)

        if matches:
            HistoryEntry.objects.create(
                user=request.user,
                entry_type="nutrition",
                title=f"Nutrition lookup: {ingredients[0]}",
                summary="Looked up nutrition data.",
                payload={"matches": matches, "input": serializer.validated_data},
                source_app="web",
            )

        response = {
            "matches": matches,
            "count": len(matches),
        }
        return Response(response, status=status.HTTP_200_OK)


class NutritionScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "Upload an image containing the ingredient and scale display."}, status=400)
        ingredient = str(request.data.get("ingredient", "")).strip().lower()
        try:
            weight = float(request.data.get("grams", 0) or 0)
        except (TypeError, ValueError):
            weight = 0
        detection = None
        if not ingredient or weight <= 0:
            image.seek(0)
            try:
                original_scan_bytes = image.read()
                scan_bytes = original_scan_bytes
                with Image.open(BytesIO(original_scan_bytes)) as source:
                    optimized = ImageOps.exif_transpose(source).convert("RGB")
                    optimized.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    buffer = BytesIO()
                    optimized.save(buffer, format="JPEG", quality=88, optimize=True)
                    scan_bytes = buffer.getvalue()
                def detect_ingredient():
                    temporary_path = ""
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temporary:
                            temporary.write(scan_bytes)
                            temporary_path = temporary.name
                        return IngredientDetectionService().detect(temporary_path)
                    finally:
                        if temporary_path:
                            try:
                                os.unlink(temporary_path)
                            except FileNotFoundError:
                                pass

                # Match Flutter's flow: local model inference and OCR start
                # together.  Results are deliberately resolved independently:
                # an unavailable classifier must never discard a readable LCD,
                # and an OCR failure must never discard food recognition.
                with ThreadPoolExecutor(max_workers=2) as executor:
                    detection_future = executor.submit(detect_ingredient) if not ingredient else None
                    weight_future = executor.submit(read_scale_weight, original_scan_bytes) if weight <= 0 else None
                    try:
                        detection = detection_future.result() if detection_future else None
                    except (RuntimeError, OSError, ValueError, IngredientModelError):
                        detection = None
                    try:
                        local_weight = weight_future.result() if weight_future else None
                    except (RuntimeError, OSError, ValueError):
                        local_weight = None
                if detection and detection.items:
                    ingredient = detection.items[0]["name"]
                if local_weight:
                    weight = local_weight
                with Image.open(BytesIO(scan_bytes)) as image_for_ocr:
                    scale_top = int(image_for_ocr.height * 0.52)
                    scale_crop = image_for_ocr.crop((0, scale_top, image_for_ocr.width, image_for_ocr.height))
                    scale_crop.thumbnail((1400, 900), Image.Resampling.LANCZOS)
                    ocr_buffer = BytesIO()
                    scale_crop.save(ocr_buffer, format="JPEG", quality=95, optimize=True)
                parsed = None
                if weight <= 0:
                    try:
                        parsed = GeminiService().recognize_nutrition_scan(
                            image_bytes=ocr_buffer.getvalue(), mime_type="image/jpeg", timeout=45
                        )
                    except (RuntimeError, TimeoutError, OSError, ValueError):
                        parsed = None
                if not ingredient:
                    try:
                        vision = GeminiService().recognize_ingredients_from_image(
                            image_bytes=scan_bytes, mime_type="image/jpeg", timeout=45
                        )
                    except (RuntimeError, TimeoutError, OSError, ValueError):
                        vision = None
                    candidates = vision.get("ingredients", []) if vision else []
                    if candidates and isinstance(candidates[0], dict):
                        ingredient = str(candidates[0].get("name", "")).strip().lower()
            except (OSError, ValueError):
                # Invalid uploads still produce the manual-fallback response.
                parsed = None
            if parsed:
                if not ingredient:
                    ingredient = str(parsed.get("ingredient", "")).strip().lower()
                weight = normalise_weight(parsed.get("weight_grams")) or 0
        weight = normalise_weight(weight) or 0
        response = {
            "ingredient": ingredient or None,
            "weight_grams": weight or None,
            "ingredient_detected": bool(ingredient),
            "weight_detected": bool(weight),
            "candidates": detection.candidates if detection else [],
        }
        if not ingredient or not weight:
            response["message"] = (
                "Ingredient detected, but weight could not be read. Please enter the weight manually."
                if ingredient else "Weight detected, but ingredient could not be identified. Please enter the ingredient manually."
                if weight else "Ingredient and scale weight could not be read. Please enter them manually."
            )
            return Response(response, status=status.HTTP_200_OK)
        match = NutritionService().scale_nutrition(ingredient, weight)
        if not match:
            return Response({"detail": f"No nutrition dataset match found for '{ingredient}'."}, status=422)
        response["message"] = "Ingredient and scale weight detected. Review them, then calculate nutrition."
        return Response(response)
