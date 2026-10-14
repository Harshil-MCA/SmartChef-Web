from __future__ import annotations

from rest_framework import serializers


class NutritionLookupSerializer(serializers.Serializer):
    ingredient = serializers.CharField(required=False, allow_blank=True)
    ingredients = serializers.ListField(
        child=serializers.CharField(max_length=120),
        required=False,
        allow_empty=False,
    )
    grams = serializers.FloatField(required=False, min_value=0)
