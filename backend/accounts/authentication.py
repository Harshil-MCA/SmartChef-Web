from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from accounts.jwt import JWTError, decode_token
from accounts.session import touch_session


class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].decode("utf-8") != self.keyword:
            return None
        if len(auth) != 2:
            raise AuthenticationFailed("Invalid authorization header.")

        token = auth[1].decode("utf-8")
        try:
            payload = decode_token(token, expected_type="access")
        except JWTError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        User = get_user_model()
        try:
            user = User.objects.get(pk=payload["sub"])
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found.") from exc

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        session_id = payload.get("sid")
        if session_id and not touch_session(session_id, user.pk):
            raise AuthenticationFailed("SmartChef session expired. Please log in again.")

        return user, payload
