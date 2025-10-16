from .base import *
DEBUG = False
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("NAME_PROD"),
        'HOST': env("HOST_PROD"),
        'PORT': env("PORT_PROD"),
        'USER':  env("USER_PROD"),
        'PASSWORD': env("PASSWORD_PROD"),
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
            'charset': 'utf8mb4',
            'use_unicode': True,
        }
    }
}
STATIC_URL = '/static/'
STATIC_ROOT = '/srv/thabicare/static_root'   # 👈 mới

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.request": {  # lỗi 500 sẽ đổ vào đây kèm traceback
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
