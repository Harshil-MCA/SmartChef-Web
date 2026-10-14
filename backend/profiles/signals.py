from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import Profile


@receiver(post_save, sender=get_user_model())
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, display_name=instance.email.split("@")[0])
