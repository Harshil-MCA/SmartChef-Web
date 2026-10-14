from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shopping.views import ShoppingItemViewSet

router = DefaultRouter()
router.register("", ShoppingItemViewSet, basename="shopping-item")

urlpatterns = [path("", include(router.urls))]
