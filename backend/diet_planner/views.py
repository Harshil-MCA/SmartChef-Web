from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from history.models import HistoryEntry
from diet_planner.models import DietPlanRecord
from diet_planner.serializers import DietPlanGenerateSerializer, DietPlanRecordSerializer
from diet_planner.services import DietPlannerService


class DietPlanRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DietPlanRecordSerializer

    def get_queryset(self):
        return DietPlanRecord.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        serializer = DietPlanGenerateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        HistoryEntry.objects.create(
            user=request.user,
            entry_type="diet",
            title=record.goal or "Diet Plan",
            summary="Generated a diet plan.",
            payload=DietPlanRecordSerializer(record).data,
            source_app="web",
        )
        return Response(DietPlanRecordSerializer(record).data, status=status.HTTP_201_CREATED)
