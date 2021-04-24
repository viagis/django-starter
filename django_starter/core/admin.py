__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import User


@admin.register(User)
class AuthorAdmin(UserAdmin):
    pass
