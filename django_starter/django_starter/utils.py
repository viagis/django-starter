__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

import collections
import functools
from enum import Enum
from logging import Logger, getLogger
from time import time
from typing import List, Optional, Any, Callable, AnyStr, Union, Mapping, TypeVar, Tuple

from django.core.management import BaseCommand
from django.db import transaction

T = TypeVar('T')


class LogLevel(Enum):
    debug = 'DEBUG'
    info = 'INFO'
    warning = 'WARNING'
    error = 'ERROR'
    critical = 'CRITICAL'

    @property
    def short_name(self) -> str:
        return self.name[0]


class LogCommand(BaseCommand):
    log_level: LogLevel
    LOG_LEVEL_OPTIONS: List[LogLevel] = [it for it in LogLevel]
    LOGGER_NAME = 'default'

    def __init__(self):
        super().__init__()
        self.cron = False
        self.log: Logger = getLogger(self.LOGGER_NAME)
        self.log_level: LogLevel = LogLevel.debug

    def add_arguments(self, parser):
        parser.add_argument('-c', '--cron', action='store_true')
        parser.add_argument('-l', '--log-level', type=str,
                            help='Log messages below this level will be omitted. '
                                 f'({", ".join(f"{it.short_name}[{it.name}]" for it in self.LOG_LEVEL_OPTIONS)})')

    def handle(self, *args, **options):
        self.cron = options.get('cron', False)
        if self.cron:
            self.log = getLogger('cron')

        log_level_specifier = options.get('log_level', None)
        if log_level_specifier:
            level: Optional[LogLevel] = None
            for ll in self.LOG_LEVEL_OPTIONS:
                if ll.short_name == log_level_specifier or ll.name == log_level_specifier:
                    level = ll

            assert level is not None, f'Unknown log level: {log_level_specifier}'
            self.log_level = level

            # noinspection PyTypeChecker
            self.log.setLevel(self.log_level.value)


class DryRunException(Exception):
    pass


class DryRunCommand(LogCommand):

    def __init__(self):
        super().__init__()
        self.dry_run = False

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-n', '--dry-run', action='store_true')

    def run(self, *args, **options):
        pass

    def handle(self, *args, **options):
        super().handle(*args, **options)
        self.dry_run = options.get('dry_run', False)

        try:
            with transaction.atomic():
                self.run(*args, **options)
                if self.dry_run:
                    raise DryRunException()
        except DryRunException:
            pass


def measure(label: Optional[str] = None, output_handler: Optional[Callable[[str], Any]] = None):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with Measure(label, output_handler):
                return func(*args, **kwargs)

        return wrapper

    return actual_decorator


class Measure(object):

    def __init__(self, label: Optional[str] = None, output_handler: Optional[Callable[[str], Any]] = None):
        self.output_handler = output_handler if isinstance(output_handler, Callable) else None
        self.label = label
        self.start = None

    def __enter__(self):
        self.start = time()

    def __exit__(self, exc_type, exc_value, traceback):
        duration = round(time() - self.start, 3)
        if self.label:
            message = f'{self.label} took {duration:.3f}s'
        else:
            message = f'Took {duration:.3f}s'
        if self.output_handler:
            self.output_handler(message)
        else:
            print(message)


def gettype(
    instance: Union[Mapping, object],
    key: str,
    allowed_types: Union[type, Tuple[Union[type, Tuple[Any, ...]]]],
    default: Optional[T] = None
) -> Optional[T]:
    """
    Attempts to retrieve the value from `instance` (`None` if not present) and checks it's type.
    If the type does not match `None` is returned.
    Uses `instance.get()` when `instance` is a dict like type and `getattr()` for all other types

    :param instance: dict or object to retrieve the value/attribute from
    :param key: key for lookup
    :param allowed_types: used for type check of retrieved value
    :param default: default value if key was not found and/or type check failed
    :return: A value of type specified in `type` parameter otherwise None or default value (if provided)
    """
    if isinstance(instance, object):
        value = getattr(instance, key, default)
    else:
        value = instance.get(key, default)

    # bool workaround
    # https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance
    iterable_types = (set, tuple, list, collections.Iterable)
    types = tuple(allowed_types) if isinstance(allowed_types, iterable_types) else (allowed_types, )
    is_bool = isinstance(value, bool)
    if is_bool and bool not in types:
        has_valid_type = False
    else:
        has_valid_type = isinstance(value, types)

    return value if has_valid_type else (default if default is not None else None)


def is_blank(string: Optional[AnyStr]) -> bool:
    if string is None:
        return True

    if not isinstance(string, (str, bytes)):
        raise ValueError('Parameter must be `AnyStr` or `None`')

    return not bool((string or '').strip())


def none_if_blank(string: Optional[AnyStr]) -> Optional[AnyStr]:
    return None if is_blank(string) else string
