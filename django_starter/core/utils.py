__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.utils.cache import patch_cache_control, add_never_cache_headers
from django.utils.datetime_safe import datetime


def patched_cache_last_key_download_response(
        response: HttpResponse, last_update_check: Optional[datetime]
) -> HttpResponse:
    if last_update_check is None:
        add_never_cache_headers(response)
        return response

    next_update_check = timezone.now()\
        .astimezone(settings.KEY_PUBLICATION_TIME_SLOT_TZ)\
        .replace(minute=0, second=0, microsecond=0) + settings.HOURLY_KEY_DOWNLOAD_OFFSET

    if next_update_check < timezone.now():
        next_update_check = next_update_check + timedelta(hours=1)

    max_age = next_update_check - timezone.now()
    patch_cache_control(response, max_age=max(0, max_age.seconds), must_revalidate=True, public=True)
    return response
