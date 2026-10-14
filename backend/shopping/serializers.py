from __future__ import annotations

from rest_framework import serializers

from shopping.models import ShoppingItem


class ShoppingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingItem
        fields = [
            "id",
            "name",
            "quantity",
            "category",
            "is_purchased",
            "is_favorite",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return ShoppingItem.objects.create(user=self.context["request"].user, **validated_data)
