from django.contrib import admin

from ingredients.models import ScanRecord


@admin.register(ScanRecord)
class ScanRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "image_name", "status", "confidence", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["image_name", "user__email"]
