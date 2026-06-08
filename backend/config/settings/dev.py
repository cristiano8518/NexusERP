from .base import *  # noqa: F403

DEBUG = True

# Dev: fallback cache if Redis unavailable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),  # noqa: F405
    },
    "locmem": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "nexuserp-fallback",
    },
}

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Avoid 500 if token_blacklist migrations were not applied yet
SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = False  # noqa: F405
