from __future__ import annotations

from rest_framework import serializers

from profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "email",
            "display_name",
            "photo_url",
            "phone_number",
            "theme_preference",
            "unit_preference",
            "language",
            "notifications_enabled",
            "dietary_preference",
            "medical_restrictions",
            "age",
            "weight_kg",
            "height_cm",
            "gender",
            "activity_level",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at"]
