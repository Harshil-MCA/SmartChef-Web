from __future__ import annotations

from django.conf import settings
from django.db import models


class HistoryEntry(models.Model):
    ENTRY_TYPES = [
        ("ingredient", "Ingredient"),
        ("recipe", "Recipe"),
        ("nutrition", "Nutrition"),
        ("diet", "Diet"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="history_entries")
    entry_type = models.CharField(max_length=24, choices=ENTRY_TYPES)
    title = models.CharField(max_length=160)
    summary = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    source_app = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.entry_type}: {self.title}"
