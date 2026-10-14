from __future__ import annotations

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from profiles.models import Profile
from profiles.serializers import ProfileSerializer


class MeProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return Profile.objects.select_related("user").get(user=self.request.user)
