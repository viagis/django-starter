__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from datetime import datetime, date

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma, intword, naturaltime, naturalday

register = template.Library()


@register.filter(is_safe=True)
def intword_or_comma(value, use_l10n=True) -> str:
    if value is None:
        return '-'

    if not value or value < 1_000_000:
        return intcomma(value, use_l10n=use_l10n)
    else:
        return intword(value)


@register.filter(expects_localtime=True)
def naturaldaytime(value, arg=None) -> str:
    tzinfo = getattr(value, 'tzinfo', None)
    try:
        value_date = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    today = datetime.now(tzinfo).date()
    delta = value_date - today
    if delta.days == 0:
        return naturaltime(value)
    else:
        return f'{naturalday(value, arg=arg)} {naturaltime(value)}'
