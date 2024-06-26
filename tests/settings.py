from __future__ import annotations

SECRET_KEY = "NOTASECRET"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}

TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "django_harlequin",
]

USE_TZ = True
