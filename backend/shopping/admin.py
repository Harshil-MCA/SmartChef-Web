from django.contrib import admin

from shopping.models import ShoppingItem


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "category", "is_purchased", "is_favorite", "updated_at"]
    list_filter = ["category", "is_purchased", "is_favorite"]
    search_fields = ["name", "notes", "user__email"]
