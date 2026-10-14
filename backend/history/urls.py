from django.urls import include, path
from rest_framework.routers import DefaultRouter

from history.views import HistoryEntryViewSet

router = DefaultRouter()
router.register("", HistoryEntryViewSet, basename="history")

urlpatterns = [path("", include(router.urls))]
