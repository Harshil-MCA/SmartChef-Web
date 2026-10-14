from __future__ import annotations

from rest_framework import serializers

from recipes.models import RecipeRecord


class RecipeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRecord
        fields = [
            "id",
            "recipe_name",
            "description",
            "ingredients",
            "steps",
            "nutrition",
            "estimated_cost",
            "cook_time",
            "difficulty",
            "servings",
            "input_ingredients",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecipeGenerateSerializer(serializers.Serializer):
    ingredients = serializers.ListField(
        child=serializers.CharField(max_length=80),
        allow_empty=False,
        required=False,
    )
    dish_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    serving_count = serializers.IntegerField(required=False, min_value=1, max_value=20, default=2)

    def validate(self, attrs):
        if not attrs.get("ingredients") and not attrs.get("dish_name"):
            raise serializers.ValidationError("Provide either ingredients or a dish name.")
        return attrs

    def create(self, validated_data):
        from recipes.services import generate_recipe_record

        return generate_recipe_record(user=self.context["request"].user, **validated_data)
