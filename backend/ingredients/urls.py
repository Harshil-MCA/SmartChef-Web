from django.urls import path

from ingredients.views import IngredientDetectView

urlpatterns = [
    path("detect/", IngredientDetectView.as_view(), name="ingredient-detect"),
]
