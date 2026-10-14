from __future__ import annotations

from django.contrib.auth import password_validation
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.conf import settings
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
from rest_framework import serializers

from accounts.jwt import create_token
from accounts.models import User
from profiles.models import Profile


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name", read_only=True)
    photo_url = serializers.CharField(source="profile.photo_url", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "firebase_uid", "display_name", "photo_url", "date_joined"]
        read_only_fields = ["firebase_uid"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=120)

    def validate_password(self, value: str) -> str:
        try:
            password_validation.validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        display_name = validated_data.pop("display_name", "").strip()
        user = User.objects.create_user(**validated_data)
        if display_name:
            profile = user.profile
            profile.display_name = display_name
            profile.save(update_fields=["display_name"])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            user = self._firebase_user(attrs["email"], attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is disabled."})
        attrs["user"] = user
        return attrs

    @staticmethod
    def _firebase_user(email: str, password: str):
        api_key = getattr(settings, "FIREBASE_WEB_API_KEY", "")
        if not api_key:
            return None
        request = Request(
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
            f"?key={api_key}",
            data=json.dumps({"email": email, "password": password, "returnSecureToken": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=8) as response:
                firebase_user = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, ValueError):
            return None
        firebase_email = str(firebase_user.get("email", email)).lower().strip()
        if not firebase_email:
            return None
        user, created = User.objects.get_or_create(email=firebase_email, defaults={"is_active": True})
        if created or not user.has_usable_password():
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AuthTokenFactory:
    @staticmethod
    def build_token_pair(user: User, session_id: str | None = None) -> dict[str, str]:
        access = create_token(
            user_id=str(user.pk),
            token_type="access",
            expires_in=settings.TOKEN_ACCESS_LIFETIME,
            session_id=session_id,
        )
        refresh = create_token(
            user_id=str(user.pk),
            token_type="refresh",
            expires_in=settings.TOKEN_REFRESH_LIFETIME,
            session_id=session_id,
        )
        return {"access": access, "refresh": refresh}


class FirebaseExchangeSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=120)
    platform = serializers.ChoiceField(choices=["flutter", "web"])
