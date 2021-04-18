__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

# Import default settings
# noinspection PyUnresolvedReferences
from .settings import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Add database connections details - refer to default settings for a list of required databases
# DATABASES['default'] = {**DATABASES['default'], **{
#     'NAME': 'db_name',
#     'USER': 'db_user',
#     'PASSWORD': 'password'
# }}
# ...

if ENVIRONMENT == ENVIRONMENT.debug:
    # For local development
    ALLOWED_HOSTS += [
        '127.0.0.1',
        'localhost',
        # '<dev-machine-ip>',
    ]

    # Disable cache
    # WEBPACK_LOADER['DEFAULT']['CACHE'] = False

    # LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'  # sql queries
    # LOGGING['loggers']['django.template']['level'] = 'INFO'  # silence template errors
    # LOGGING['loggers']['default']['level'] = 'INFO'
    # LOGGING['loggers']['cron']['level'] = 'DEBUG'  # overwrite cron level (default: warning)

elif ENVIRONMENT in [Environment.staging, Environment.production]:
    # ALLOWED_HOSTS += [
    #     '<hostname>'
    # ]

    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
