from __future__ import annotations

from django.conf import settings
from django.db import models


class ScanRecord(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("unknown", "Unknown"),
        ("error", "Error"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scan_records")
    image = models.ImageField(upload_to="ingredient-scans/")
    image_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="unknown")
    detected_ingredients = models.JSONField(default=list, blank=True)
    candidates = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    margin = models.FloatField(null=True, blank=True)
    manual_corrections = models.JSONField(default=list, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.image_name or f"Scan {self.pk}"
