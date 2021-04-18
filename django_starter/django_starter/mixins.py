__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from django.db.models import Model, DateTimeField


class HistoryMixin(Model):
    create_date = DateTimeField(auto_now_add=True, db_index=True)
    modified_date = DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
