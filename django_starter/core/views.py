__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render


def index(request: HttpRequest):
    return render(request, 'index.html', {
        'languages': {code: name for code, name in settings.LANGUAGES}
    })
