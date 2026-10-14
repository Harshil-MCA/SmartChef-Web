from django.urls import path

from profiles.views import MeProfileView

urlpatterns = [
    path("me/", MeProfileView.as_view(), name="profile-me"),
]
