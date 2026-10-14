from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/profile/", include("profiles.urls")),
    path("api/history/", include("history.urls")),
    path("api/shopping-items/", include("shopping.urls")),
    path("api/recipes/", include("recipes.urls")),
    path("api/nutrition/", include("nutrition.urls")),
    path("api/ingredients/", include("ingredients.urls")),
    path("api/diet-plans/", include("diet_planner.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
