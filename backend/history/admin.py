from django.contrib import admin

from history.models import HistoryEntry


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    list_display = ["user", "entry_type", "title", "created_at"]
    list_filter = ["entry_type", "created_at"]
    search_fields = ["title", "summary", "user__email"]
