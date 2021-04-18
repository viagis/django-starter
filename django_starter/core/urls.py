__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from django.urls import path

from core.views import index

urlpatterns = [
    path('', index, name='index'),
]
