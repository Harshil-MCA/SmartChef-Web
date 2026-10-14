from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from history.models import HistoryEntry
from history.serializers import HistoryEntryCreateSerializer, HistoryEntrySerializer


class HistoryEntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HistoryEntry.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return HistoryEntryCreateSerializer
        return HistoryEntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        output = HistoryEntrySerializer(entry)
        return Response(output.data, status=status.HTTP_201_CREATED)
