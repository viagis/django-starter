__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

import re
from abc import ABCMeta, ABC, abstractmethod
from enum import Enum, EnumMeta
from typing import Any, Optional, Tuple, List, Set

from django.conf import settings
from django.utils import translation
from django.utils.translation import pgettext, get_language


class EnumCaseNotFound(Exception):
    pass


class MetaEnumABC(EnumMeta, ABCMeta):
    pass


class BaseEnum(ABC, Enum, metaclass=MetaEnumABC):

    @staticmethod
    def localize(context: str, enum_value: Any, language: Optional[str] = None) -> str:
        """
        :param context: Context used with `pgettext`
        :param enum_value: `BaseEnum.value` or an arbitrary value
        :param language: Used for translation override, defaults to `get_language()`
        """
        language = language or get_language()
        with translation.override(language):
            return pgettext(context, str(enum_value))

    @classmethod
    def from_value(cls, value: Any, default: Optional['BaseEnum'] = None) -> Optional['BaseEnum']:
        return next((it for it in cls if it.value == value), default)

    @classmethod
    def from_key(cls, key: str) -> 'BaseEnum':
        """
        :raises EnumCaseNotFound
        """
        try:
            return cls[key]
        except KeyError:
            raise EnumCaseNotFound(f'Unknown value for {cls.__name__}: {key} [{"|".join(cls.__members__.keys())}]')

    @classmethod
    def is_valid_value(cls, value: Any) -> bool:
        return value in {it.value for it in cls}

    @classmethod
    def choices(cls) -> List[Tuple[Any, str]]:
        return [(it.value, it.localized_value) for it in cls]

    @classmethod
    def max_length(cls) -> int:
        return max(len(it.value) for it in cls)

    @classmethod
    @abstractmethod
    def localize_value(cls, value: Any, language: Optional[str] = None) -> str:
        pass

    @classmethod
    def values(cls) -> List[str]:
        """
        The value for each enum case
        """
        return [it.value for it in cls]

    @classmethod
    def all_value_variants(cls) -> Set[str]:
        variants = [it.value_variants for it in cls]
        return {y for x in variants for y in x}

    @property
    def localized_value(self) -> str:
        """
        Returns the localized value for the current language
        """
        return self.get_localized_value()

    @property
    def variant_base_values(self) -> Set[str]:
        base_values = set()
        base_values.add(self.value)
        for lang, _ in settings.LANGUAGES:
            base_values.add(self.get_localized_value(language=lang))

        return base_values

    @property
    def value_variants(self) -> Set[str]:
        variants = set()

        base_values = self.variant_base_values

        def strip_all_space(s: str) -> str:
            return re.sub(r'\s', '', s, flags=re.UNICODE)

        for value in base_values:
            variants.add(value)
            variants.add(strip_all_space(value))

        return {it.lower() for it in variants}

    def get_localized_value(self, language: Optional[str] = None):
        """
        Uses the class name as the localization context for `localize(context, enum_value)`
        """
        return BaseEnum.localize(self.__class__.__name__, enum_value=self.value, language=language)


class Environment(BaseEnum):
    debug = 'debug'
    staging = 'staging'
    production = 'production'

    @classmethod
    def localize_value(cls, value: Any, language: Optional[str] = None) -> str:
        return cls.localize(cls.__name__, value, language)
