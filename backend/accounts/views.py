from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.jwt import JWTError, decode_token
from accounts.models import User
from accounts.firebase import FirebaseIdentityError, verify_id_token
from accounts.session import (
    ActiveSmartChefSessionError,
    acquire_session,
    release_session,
)
from accounts.serializers import (
    AuthTokenFactory,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    FirebaseExchangeSerializer,
    TokenPairSerializer,
    UserSerializer,
)
from profiles.serializers import ProfileSerializer
from .models import TokenBlacklist


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
            profile = user.profile
        try:
            session = acquire_session(user, request.data.get("platform", "web"))
        except ActiveSmartChefSessionError as error:
            return Response({"detail": str(error)}, status=409)
        token_pair = AuthTokenFactory.build_token_pair(user, str(session.session_id))
        response = {
            **token_pair,
            "user": UserSerializer(user).data,
            "profile": ProfileSerializer(profile).data,
        }
        return Response(response, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            session = acquire_session(user, request.data.get("platform", "web"))
        except ActiveSmartChefSessionError as error:
            return Response({"detail": str(error)}, status=409)
        token_pair = AuthTokenFactory.build_token_pair(user, str(session.session_id))
        response = {
            **token_pair,
            "user": UserSerializer(user).data,
            "profile": ProfileSerializer(user.profile).data,
        }
        return Response(response)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data.get("refresh", "").strip()
        if not refresh:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = decode_token(refresh, expected_type="refresh")
        except JWTError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        if TokenBlacklist.objects.filter(jti=payload["jti"]).exists():
            return Response({"detail": "Refresh token has been revoked."}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_user_model().objects.get(pk=payload["sub"])
        session_id = payload.get("sid")
        if session_id:
            from accounts.session import touch_session
            if not touch_session(session_id, user.pk):
                return Response({"detail": "SmartChef session expired. Please log in again."}, status=401)
        token_pair = AuthTokenFactory.build_token_pair(user, session_id)
        return Response(token_pair)


class FirebaseExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FirebaseExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            identity = verify_id_token(serializer.validated_data["id_token"])
        except FirebaseIdentityError as error:
            return Response({"detail": str(error)}, status=401)

        firebase_uid = identity["firebase_uid"]
        email = identity["email"]
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        if user is None:
            user = User.objects.filter(email__iexact=email).first()
            if user is not None and user.firebase_uid and user.firebase_uid != firebase_uid:
                return Response({"detail": "This email is linked to another Firebase account."}, status=409)
            if user is None:
                user = User(email=email, firebase_uid=firebase_uid, is_active=True)
                user.set_unusable_password()
                user.save()
            else:
                user.firebase_uid = firebase_uid
                user.email = email
                user.save(update_fields=["firebase_uid", "email", "updated_at"])

        profile = user.profile
        display_name = serializer.validated_data.get("display_name", "").strip() or identity["display_name"]
        update_fields = []
        if display_name and not profile.display_name:
            profile.display_name = display_name
            update_fields.append("display_name")
        if identity["photo_url"] and not profile.photo_url:
            profile.photo_url = identity["photo_url"]
            update_fields.append("photo_url")
        if update_fields:
            profile.save(update_fields=update_fields + ["updated_at"])

        try:
            session = acquire_session(user, serializer.validated_data["platform"])
        except ActiveSmartChefSessionError as error:
            return Response({"detail": str(error)}, status=409)
        token_pair = AuthTokenFactory.build_token_pair(user, str(session.session_id))
        return Response({**token_pair, "user": UserSerializer(user).data, "profile": ProfileSerializer(user.profile).data})


class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data.get("refresh", "").strip()
        if refresh:
            try:
                payload = decode_token(refresh, expected_type="refresh")
            except JWTError:
                payload = None
            if payload:
                release_session(payload.get("sid"), payload.get("sub"))
                TokenBlacklist.objects.get_or_create(
                    jti=payload["jti"],
                    defaults={"expires_at": payload.get("exp")},
                )
        return Response({"detail": "Signed out successfully."})


class MeView(APIView):
    def get(self, request):
        profile = request.user.profile
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "profile": ProfileSerializer(profile).data,
            }
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        exists = User.objects.filter(email__iexact=email).exists()
        return Response(
            {
                "detail": "If an account exists for that email, a reset link can be sent from the configured email backend.",
                "email_exists": exists,
            }
        )
