__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from django.contrib.auth.models import UserManager
from safedelete.managers import SafeDeleteManager


class SafeDeleteUserManager(SafeDeleteManager, UserManager):
    pass
