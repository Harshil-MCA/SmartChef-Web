from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    THEME_CHOICES = [
        ("system", "System"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    UNIT_CHOICES = [
        ("metric", "Metric"),
        ("imperial", "Imperial"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    photo_url = models.URLField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    theme_preference = models.CharField(max_length=16, choices=THEME_CHOICES, default="system")
    unit_preference = models.CharField(max_length=16, choices=UNIT_CHOICES, default="metric")
    language = models.CharField(max_length=32, default="English")
    notifications_enabled = models.BooleanField(default=True)
    dietary_preference = models.CharField(max_length=80, blank=True)
    medical_restrictions = models.CharField(max_length=120, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    gender = models.CharField(max_length=32, blank=True)
    activity_level = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__email"]

    def __str__(self) -> str:
        return self.display_name or self.user.email
