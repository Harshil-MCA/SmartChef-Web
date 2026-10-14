from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent
MOBILE_APP_DIR = PROJECT_ROOT / "smartchef_app"

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
      return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _split_env(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_path(name: str, default: str) -> str:
    """Resolve configured data paths independently of the process cwd."""
    configured = os.getenv(name, default).strip()
    path = Path(configured)
    return str(path if path.is_absolute() else BASE_DIR / path)


def _database_config() -> dict[str, object]:
    database_url = os.getenv("DJANGO_DATABASE_URL", "sqlite:///db.sqlite3")
    parsed = urlparse(database_url)

    if parsed.scheme in {"sqlite", "sqlite3"}:
        db_name = parsed.path.lstrip("/") or "db.sqlite3"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / db_name,
        }

    if parsed.scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "localhost",
            "PORT": parsed.port or "5432",
        }

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }


DEBUG = _env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "smartchef-insecure-dev-secret-key"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false")
ALLOWED_HOSTS = _split_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "profiles",
    "history",
    "shopping",
    "recipes",
    "nutrition",
    "ingredients",
    "diet_planner",
    "ai",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": _database_config()}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "uploads"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = _split_env(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = _split_env("DJANGO_CSRF_TRUSTED_ORIGINS")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

TOKEN_ACCESS_LIFETIME = timedelta(
    minutes=int(os.getenv("DJANGO_ACCESS_TOKEN_LIFETIME_MINUTES", "15"))
)
TOKEN_REFRESH_LIFETIME = timedelta(
    days=int(os.getenv("DJANGO_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
)
SMARTCHEF_SESSION_TIMEOUT_MINUTES = int(os.getenv("SMARTCHEF_SESSION_TIMEOUT_MINUTES", "30"))

GEMINI_API_KEY = os.getenv("DJANGO_GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("DJANGO_GEMINI_MODEL", "gemini-3.6-flash").strip()
TESSERACT_CMD = os.getenv("DJANGO_TESSERACT_CMD", "").strip()

FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "").strip()
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "").strip()
INGREDIENT_DATASET_DIR = _env_path(
    "DJANGO_INGREDIENT_DATASET_DIR",
    str(BASE_DIR / "datasets" / "fruits-and-vegetables" / "train"),
)
INGREDIENT_MODEL_PATH = _env_path(
    "DJANGO_INGREDIENT_MODEL_PATH",
    str(BASE_DIR / "models" / "smartchef_model.tflite"),
)

NUTRITION_DATABASE_PATH = _env_path(
    "DJANGO_NUTRITION_DATABASE_PATH",
    str(BASE_DIR / "datasets" / "nutrition" / "nutrition_database.json"),
)
NUTRITION_ALIASES_PATH = _env_path(
    "DJANGO_NUTRITION_ALIASES_PATH",
    str(BASE_DIR / "datasets" / "nutrition" / "ingredient_aliases.json"),
)
NUTRITION_CSV_DIR = _env_path(
    "DJANGO_NUTRITION_CSV_DIR",
    str(BASE_DIR / "datasets" / "food_nutrition" / "FINAL FOOD DATASET"),
)
USDA_API_KEY = os.getenv("DJANGO_USDA_API_KEY", "").strip()
DATA_GOV_IN_API_KEY = os.getenv(
    "DJANGO_DATA_GOV_IN_API_KEY",
    os.getenv("DATA_GOV_IN_API_KEY", ""),
).strip()
