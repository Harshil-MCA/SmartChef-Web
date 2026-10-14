from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from history.models import HistoryEntry
from recipes.models import RecipeRecord
from recipes.serializers import RecipeGenerateSerializer, RecipeRecordSerializer


class RecipeRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RecipeRecordSerializer

    def get_queryset(self):
        return RecipeRecord.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        serializer = RecipeGenerateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        HistoryEntry.objects.create(
            user=request.user,
            entry_type="recipe",
            title=record.recipe_name,
            summary=record.description,
            payload=RecipeRecordSerializer(record).data,
            source_app="web",
        )
        return Response(RecipeRecordSerializer(record).data, status=status.HTTP_201_CREATED)
