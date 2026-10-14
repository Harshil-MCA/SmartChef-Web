from django.contrib import admin

from profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "display_name", "theme_preference", "unit_preference", "updated_at"]
    search_fields = ["user__email", "display_name"]
