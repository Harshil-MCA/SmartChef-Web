from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ingredients.models import ScanRecord
from ingredients.serializers import IngredientDetectSerializer
from ingredients.services import IngredientDetectionService, IngredientModelError
from history.models import HistoryEntry


class IngredientDetectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IngredientDetectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["image"]
        manual_corrections = serializer.validated_data.get("manual_corrections", [])

        record = ScanRecord.objects.create(
            user=request.user,
            image=upload,
            image_name=getattr(upload, "name", ""),
            manual_corrections=manual_corrections,
        )

        try:
            detection = IngredientDetectionService().detect(
                record.image.path,
                filename=record.image_name,
                manual_corrections=manual_corrections,
            )
            record.status = detection.status
            record.detected_ingredients = detection.items
            record.candidates = detection.candidates
            record.confidence = detection.confidence
            record.margin = detection.margin
            record.message = detection.message
            record.save(update_fields=[
                "status",
                "detected_ingredients",
                "candidates",
                "confidence",
                "margin",
                "message",
            ])

            if detection.items or manual_corrections:
                title = (
                    f"Ingredient scan: {detection.items[0]['name']}"
                    if detection.items
                    else f"Ingredient scan correction: {', '.join(manual_corrections)}"
                )
                HistoryEntry.objects.create(
                    user=request.user,
                    entry_type="ingredient",
                    title=title,
                    summary=detection.message,
                    payload={
                        "scan_id": record.pk,
                        "items": detection.items,
                        "candidates": detection.candidates,
                        "manual_corrections": manual_corrections,
                    },
                    source_app="web",
                )

            return Response(
                {
                    "id": record.pk,
                    "status": detection.status,
                    "items": detection.items,
                    "candidates": detection.candidates,
                    "confidence": detection.confidence,
                    "margin": detection.margin,
                    "message": detection.message,
                },
                status=status.HTTP_200_OK if detection.items else status.HTTP_202_ACCEPTED,
            )
        except IngredientModelError as error:
            record.status = "error"
            record.message = str(error)
            record.save(update_fields=["status", "message"])
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as error:
            record.status = "error"
            record.message = str(error)
            record.save(update_fields=["status", "message"])
            return Response(
                {"detail": "Ingredient detection failed.", "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
