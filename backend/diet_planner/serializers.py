from __future__ import annotations

from rest_framework import serializers

from diet_planner.models import DietPlanRecord


class DietPlanRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietPlanRecord
        fields = [
            "id",
            "input_payload",
            "result_payload",
            "goal",
            "daily_budget",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DietPlanGenerateSerializer(serializers.Serializer):
    age = serializers.IntegerField(min_value=1, max_value=120)
    weight = serializers.FloatField(min_value=1)
    height = serializers.FloatField(min_value=1)
    daily_budget = serializers.FloatField(min_value=0)
    goal = serializers.CharField(max_length=120)

    def create(self, validated_data):
        from diet_planner.services import DietPlannerService

        result = DietPlannerService().generate(**validated_data)
        return DietPlanRecord.objects.create(
            user=self.context["request"].user,
            input_payload=validated_data,
            result_payload=result,
            goal=validated_data["goal"],
            daily_budget=validated_data["daily_budget"],
        )
