from django.contrib import admin

from diet_planner.models import DietPlanRecord


@admin.register(DietPlanRecord)
class DietPlanRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "goal", "daily_budget", "created_at"]
    search_fields = ["goal", "user__email"]
