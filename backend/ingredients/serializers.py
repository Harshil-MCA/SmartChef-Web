from __future__ import annotations

from rest_framework import serializers


class FlexibleStringListField(serializers.ListField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = [item.strip() for item in data.split(",") if item.strip()]
        return super().to_internal_value(data)


class IngredientDetectSerializer(serializers.Serializer):
    image = serializers.ImageField()
    manual_corrections = FlexibleStringListField(
        child=serializers.CharField(max_length=80),
        required=False,
        allow_empty=True,
    )
