"""
Django settings for base project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from os import getenv
from dotenv import load_dotenv
from pathlib import Path
from .restframework_settings import *
from .db import *
from .email import *

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(getenv("DEBUG"))

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_celery_results",
    "django_celery_beat",
    "corsheaders",
    "storages",
    # "base",
    "commons",
    "users",
    "posts",
    "relations",
    "images",
    "notifications",
    "chats",
    "ai",
]
if not DEBUG:
    INSTALLED_APPS.append("django_elasticsearch_dsl")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "base.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "base.wsgi.application"
ASGI_APPLICATION = "base.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": getenv("CACHE_HOST"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(getenv("CHANNEL_LAYER_HOST"), 6379)],
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

LOGIN_URL = "/_/admin/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "users.User"


CELERY_BROKER_URL = getenv("CACHE_HOST")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TIMEZONE = "Asia/Seoul"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


CELERY_ACCEPT_CONTENT = ["pickle", "json"]
CELERY_TASK_SERIALIZER = "pickle"


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://cottontest.honeycombpizza.link",
    "http://192.168.0.7",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.honeycombpizza\.link$",
    r"^https://\w+\.cottontest.honeycombpizza\.link$",
]

# S3

AWS_S3_ENDPOINT_URL = getenv("AWS_S3_ENDPOINT_URL")
AWS_STORAGE_BUCKET_NAME = getenv("AWS_STORAGE_BUCKET_NAME")
AWS_CACHE_BUCKET_NAME = getenv("AWS_CACHE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
AWS_QUERYSTRING_AUTH = False
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


# THIRD PARTY
KAKAO_CLIENT_KEY = getenv("KAKAO_CLIENT_KEY")
KAKAO_SECRET_KEY = getenv("KAKAO_SECRET_KEY")

OLLAMA_URL = getenv("OLLAMA_URL")

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": getenv("ES_HOST"),
        "http_auth": getenv("ES_AUTH", "").split(","),
    }
}
if not DEBUG:
    ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = "posts.dsl_processor.CelerySignalProcessor"
SENTRY_DSN = getenv("SENTRY_DSN")
if SENTRY_DSN and not DEBUG:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # ELA# ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = (
        #     "django_elasticsearch_dsl.signals.CelerySignalProcessor"
    )
