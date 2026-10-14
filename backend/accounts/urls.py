from django.urls import path

from accounts.views import FirebaseExchangeView, LoginView, LogoutView, MeView, PasswordResetView, RefreshView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("firebase/", FirebaseExchangeView.as_view(), name="auth-firebase"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password-reset/", PasswordResetView.as_view(), name="auth-password-reset"),
]
