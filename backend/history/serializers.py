from __future__ import annotations

from rest_framework import serializers

from history.models import HistoryEntry


class HistoryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoryEntry
        fields = [
            "id",
            "entry_type",
            "title",
            "summary",
            "payload",
            "source_app",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class HistoryEntryCreateSerializer(serializers.Serializer):
    entry_type = serializers.ChoiceField(choices=[choice[0] for choice in HistoryEntry.ENTRY_TYPES])
    title = serializers.CharField(max_length=160)
    summary = serializers.CharField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False, default=dict)
    source_app = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]
        return HistoryEntry.objects.create(user=request.user, **validated_data)
