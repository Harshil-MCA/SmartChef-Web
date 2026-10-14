from __future__ import annotations

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from shopping.models import ShoppingItem
from shopping.serializers import ShoppingItemSerializer


class ShoppingItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingItemSerializer

    def get_queryset(self):
        return ShoppingItem.objects.filter(user=self.request.user)
