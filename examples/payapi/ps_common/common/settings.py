

import os

from dotenv import load_dotenv

from .helpers import env_var_bool
from .helpers import env_var_line
from .helpers import env_var_list

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, "dev-app.env"))

SECRET_KEY = env_var_line("SECRET_KEY") or "nokey"

DEBUG = env_var_bool("DEBUG")
SQL_DEBUG = env_var_bool("SQL_DEBUG")
DEFAULT_LOGGER_NAME = "stdout"

ALLOWED_HOSTS = ["*"]

RATE_SERVICE_URLS = env_var_list("RATE_SERVICE_URLS")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "common.payment_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "common.urls"
AUTH_USER_MODEL = "payment_api.wallet"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "common.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": (
            env_var_line("DB_FILEPATH")
            or
            os.path.join(BASE_DIR, "db.sqlite3")
        ),
        "ATOMIC_REQUESTS": False,
        "TEST": {
            "NAME": "test_base.sqlite3"
        },

    }
}

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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"

level = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },
    "disable_existing_loggers": False,
    "formatters": {
        "std_formatter": {
            "format": (
                "%(asctime)s.%(msecs)03d %(levelname)8s %(name)s "
                "%(filename)s:%(lineno)d %(message)s"
            ),
            "datefmt": "%Y-%m-%dT%H:%M:%S",
            "default_msec_format": "%s.%03d",
        }
    },
    "handlers": {
        DEFAULT_LOGGER_NAME: {
            "level": level,
            "class": "logging.StreamHandler",
            "formatter": "std_formatter",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": [DEFAULT_LOGGER_NAME],
            "level": "WARNING",
            "propagate": True
        },
        DEFAULT_LOGGER_NAME: {
            "handlers": [DEFAULT_LOGGER_NAME],
            "level": level,
        },
        "django.db": {
            "handlers": [DEFAULT_LOGGER_NAME] if SQL_DEBUG else [],
            "level": level,
        },
    },
}
