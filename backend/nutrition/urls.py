from django.urls import path

from nutrition.views import NutritionLookupView, NutritionScanView

urlpatterns = [
    path("lookup/", NutritionLookupView.as_view(), name="nutrition-lookup"),
    path("scan/", NutritionScanView.as_view(), name="nutrition-scan"),
]
