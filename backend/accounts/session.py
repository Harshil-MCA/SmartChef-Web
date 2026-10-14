from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import SmartChefSession, User


class ActiveSmartChefSessionError(Exception):
    pass


def acquire_session(user: User, platform: str) -> SmartChefSession:
    now = timezone.now()
    timeout = timedelta(minutes=getattr(settings, "SMARTCHEF_SESSION_TIMEOUT_MINUTES", 30))
    with transaction.atomic():
        current = SmartChefSession.objects.select_for_update().filter(user=user).first()
        if current and current.expires_at > now:
            raise ActiveSmartChefSessionError(
                "Your account is already active on another device. Please log out first."
            )
        if current:
            current.delete()
        return SmartChefSession.objects.create(
            user=user,
            platform=platform,
            expires_at=now + timeout,
        )


def touch_session(session_id: str | None, user_id: int) -> bool:
    if not session_id:
        return True
    now = timezone.now()
    timeout = timedelta(minutes=getattr(settings, "SMARTCHEF_SESSION_TIMEOUT_MINUTES", 30))
    updated = SmartChefSession.objects.filter(
        session_id=session_id,
        user_id=user_id,
        expires_at__gt=now,
    ).update(last_seen=now, expires_at=now + timeout)
    return updated == 1


def release_session(session_id: str | None, user_id: int | None = None) -> None:
    if not session_id:
        return
    query = SmartChefSession.objects.filter(session_id=session_id)
    if user_id is not None:
        query = query.filter(user_id=user_id)
    query.delete()
