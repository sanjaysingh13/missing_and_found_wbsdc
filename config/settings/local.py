from .base import *  # noqa
from .base import DATABASES, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="e8KRL4le0E5dCAvwdnRfwAvx6gNJtdTDdo9FuB1tHDD9qBtcrWxcmt1JppAB276W",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "3.111.96.240",
    ".ccsneo4jdigitalocean.com",
    ".wbkhoyapaya.com",
]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405
# Celery
# ------------------------------------------------------------------------------
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = True
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True
# Your stuff...
# ------------------------------------------------------------------------------
# need to add production settings. This will be loaded only if RUNNING_ON_AWS is set
try:
    RUNNING_ON_AWS = env("RUNNING_ON_AWS")
    DEBUG = False
    # DATABASES
    # ------------------------------------------------------------------------------
    DATABASES["default"]["CONN_MAX_AGE"] = env.int(
        "CONN_MAX_AGE", default=60
    )  # noqa F405

    # CACHES
    # ------------------------------------------------------------------------------
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicing memcache behavior.
                # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }

    # SECURITY
    # ------------------------------------------------------------------------------

    # https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
    SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
        "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
    )

    # STORAGES
    # ------------------------------------------------------------------------------
    # https://django-storages.readthedocs.io/en/latest/#installation
    INSTALLED_APPS += ["storages"]  # noqa F405
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_QUERYSTRING_AUTH = False
    # DO NOT change these unless you know what you're doing.
    _AWS_EXPIRY = 60 * 60 * 24 * 7
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate"
    }
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_S3_MAX_MEMORY_SIZE = env.int(
        "DJANGO_AWS_S3_MAX_MEMORY_SIZE",
        default=100_000_000,  # 100MB
    )
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME", default=None)
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#cloudfront
    AWS_S3_CUSTOM_DOMAIN = env("DJANGO_AWS_S3_CUSTOM_DOMAIN", default=None)
    aws_s3_domain = (
        AWS_S3_CUSTOM_DOMAIN
        or f"{AWS_STORAGE_BUCKET_NAME}.s3.ap-south-1.amazonaws.amazonaws.com"
    )
    # STATIC
    # ------------------------
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    # MEDIA
    # ------------------------------------------------------------------------------
    DEFAULT_FILE_STORAGE = "missing_persons_match_unidentified_dead_bodies.utils.storages.MediaRootS3Boto3Storage"
    MEDIA_URL = f"https://{aws_s3_domain}/media/"

    # EMAIL
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
    DEFAULT_FROM_EMAIL = env(
        "DJANGO_DEFAULT_FROM_EMAIL",
        default="Missing Persons & Unidentified Dead Bodies <support@wbkhoyapaya.com>",
    )
    # https://docs.djangoproject.com/en/dev/ref/settings/#server-email
    SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
    EMAIL_SUBJECT_PREFIX = env(
        "DJANGO_EMAIL_SUBJECT_PREFIX",
        default="[Missing Persons & Unidentified Dead Bodies]",
    )

    # ADMIN
    # ------------------------------------------------------------------------------
    # Django Admin URL regex.
    ADMIN_URL = env("DJANGO_ADMIN_URL")

    # Anymail
    # ------------------------------------------------------------------------------
    # https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
    INSTALLED_APPS += ["anymail"]  # noqa F405
    # https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
    # https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
    # https://anymail.readthedocs.io/en/stable/esps/sendgrid/
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {
        "SENDGRID_API_KEY": env("SENDGRID_API_KEY"),
        "SENDGRID_API_URL": env(
            "SENDGRID_API_URL", default="https://api.sendgrid.com/v3/"
        ),
    }
    # LOGGING
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#logging
    # See https://docs.djangoproject.com/en/dev/topics/logging for
    # more details on how to customize your logging configuration.
    # A sample logging configuration. The only tangible logging
    # performed by this configuration is to send an email to
    # the site admins on every HTTP 500 error when DEBUG=False.
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
        },
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            }
        },
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "filters": ["require_debug_false"],
                "class": "django.utils.log.AdminEmailHandler",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "django.request": {
                "handlers": ["mail_admins"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.security.DisallowedHost": {
                "level": "ERROR",
                "handlers": ["console", "mail_admins"],
                "propagate": True,
            },
        },
    }
    CELERY_TASK_ALWAYS_EAGER = False
    # https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
    CELERY_TASK_EAGER_PROPAGATES = False
except Exception as e:
    print(str(e))
    pass


# Your stuff...
# ------------------------------------------------------------------------------
