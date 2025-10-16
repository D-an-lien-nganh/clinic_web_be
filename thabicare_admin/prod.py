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
