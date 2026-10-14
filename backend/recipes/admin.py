from django.contrib import admin

from recipes.models import RecipeRecord


@admin.register(RecipeRecord)
class RecipeRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "recipe_name", "source", "created_at"]
    search_fields = ["recipe_name", "description", "user__email"]
