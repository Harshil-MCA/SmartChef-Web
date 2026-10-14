from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import RecipeRecordViewSet

router = DefaultRouter()
router.register("", RecipeRecordViewSet, basename="recipe")

urlpatterns = [path("", include(router.urls))]
