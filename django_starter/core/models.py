__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db.models import UUIDField, BooleanField, DateTimeField
from safedelete.models import SafeDeleteModel

from django_starter.managers import SafeDeleteUserManager
from django_starter.mixins import HistoryMixin


class User(HistoryMixin, SafeDeleteModel, AbstractUser):
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    modified_on = DateTimeField(auto_now=True, db_index=True)
    email_verified = BooleanField(default=False)

    objects = SafeDeleteUserManager()
