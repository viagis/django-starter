__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

from typing import Optional, Any, Union, Dict, List

from django.conf import settings
from django.http import JsonResponse
from rest_framework.response import Response


class SuccessErrorJsonResponse(JsonResponse):

    def __init__(
        self,
        error: Optional[Any] = None,
        data: Optional[Union[Dict, List]] = None,
        status: Optional[int] = None,
        *args, **kwargs
    ):
        _data = {
            'success': not error,
        }
        if error:
            _data['error'] = error

        if data:
            _data = {**_data, **data}

        if status is None:
            status = 200 if not error else 400

        json_dumps_params = {**({'indent': 4} if settings.DEBUG else {}), **kwargs.get('json_dumps_params', {})}
        super().__init__(data=_data, json_dumps_params=json_dumps_params, status=status, *args, **kwargs)


class SuccessErrorResponse(Response):

    def __init__(
        self,
        error: Optional[Any] = None,
        data: Optional[Union[Dict]] = None,
        status_code: Optional[int] = None,
        *args, **kwargs
    ):
        response_data = {
            'success': not error,
        }
        if error is not None:
            response_data['error'] = error

        response_data = {**response_data, **(data or {})}

        if not isinstance(status_code, int):
            status_code = 200 if not error else 400

        super().__init__(data=response_data, status=status_code, *args, **kwargs)
