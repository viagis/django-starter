__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from typing import Any, Dict, Hashable

from django import template

register = template.Library()


@register.filter
def kv(dictionary: Dict, key: Hashable) -> Any:
    return dictionary.get(key, None)
