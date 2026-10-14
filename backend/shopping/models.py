from __future__ import annotations

from django.conf import settings
from django.db import models


class ShoppingItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_items")
    name = models.CharField(max_length=160)
    quantity = models.CharField(max_length=64, blank=True)
    category = models.CharField(max_length=64, default="General")
    is_purchased = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_favorite", "category", "name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name", "category"], name="unique_user_shopping_name_category")
        ]

    def __str__(self) -> str:
        return self.name
