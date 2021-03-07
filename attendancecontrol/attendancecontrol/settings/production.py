import os
from .base import *     # noqa: F403

DEBUG = False

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('SQL_DATABASE', os.path.join(BASE_DIR, 'db.sqlite3')),       # noqa: F405
        'USER': os.environ.get('SQL_USER', 'user'),
        'PASSWORD': os.environ.get('SQL_PASSWORD', 'password'),
        'HOST': os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get('SQL_PORT', ''),
    },
    'probes': {
        'ENGINE': (
            os.environ.get('SQL_PROBES_ENGINE', '') or os.environ.get('SQL_ENGINE', 'django.db.backends.sqlite3')
        ),
        'NAME': os.environ.get('SQL_PROBES_DATABASE', os.path.join(BASE_DIR, 'probes.sqlite3')),       # noqa: F405
        'USER': os.environ.get('SQL_PROBES_USER', '') or os.environ.get('SQL_USER', 'user'),
        'PASSWORD': os.environ.get('SQL_PROBES_PASSWORD', '') or os.environ.get('SQL_PASSWORD', 'password'),
        'HOST': os.environ.get('SQL_PROBES_HOST', '') or os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get('SQL_PROBES_PORT', '') or os.environ.get('SQL_PORT', ''),
    },
}
