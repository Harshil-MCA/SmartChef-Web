from django.urls import include, path
from rest_framework.routers import DefaultRouter

from diet_planner.views import DietPlanRecordViewSet

router = DefaultRouter()
router.register("", DietPlanRecordViewSet, basename="diet-plan")

urlpatterns = [path("", include(router.urls))]
