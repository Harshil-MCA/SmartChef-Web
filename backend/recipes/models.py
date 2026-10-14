from __future__ import annotations

from django.conf import settings
from django.db import models


class RecipeRecord(models.Model):
    SOURCE_CHOICES = [
        ("ai", "AI"),
        ("manual", "Manual"),
        ("fallback", "Fallback"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_records")
    recipe_name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    ingredients = models.JSONField(default=list, blank=True)
    steps = models.JSONField(default=list, blank=True)
    nutrition = models.JSONField(default=dict, blank=True)
    estimated_cost = models.CharField(max_length=64, blank=True)
    cook_time = models.CharField(max_length=64, blank=True)
    difficulty = models.CharField(max_length=32, blank=True)
    servings = models.CharField(max_length=32, blank=True)
    input_ingredients = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default="fallback")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.recipe_name
