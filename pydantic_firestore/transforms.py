from typing import Annotated, Literal, Union, Any, Callable, TypeVar, Tuple
from enum import StrEnum, auto, global_enum
from functools import cache

from pydantic import WrapSerializer, ValidationInfo

from .utils import firestore_serializer


__all__ = [
    "Sentinel",
    "FIRESTORE_TIMESTAMP",
    "FIRESTORE_DELETE",
    "FIRESTORE_REMOVE",
    "FIRESTORE_UNION",
    "FIRESTORE_INCREMENT",
    "FIRESTORE_MAXIMUM",
    "FIRESTORE_MINIMUM",
    "FirestoreArray",
    "FirestoreNumeric",
    "FirestoreMinMax",
    "FirestoreTimestamp",
    "FirestoreDelete",
    "FirestoreSentinel",
    "sentinel_serializer",
]


@global_enum
class Sentinel(StrEnum):
    FIRESTORE_TIMESTAMP = auto()
    FIRESTORE_DELETE = auto()

    FIRESTORE_REMOVE = auto()
    FIRESTORE_UNION = auto()

    FIRESTORE_INCREMENT = auto()
    FIRESTORE_MAXIMUM = auto()
    FIRESTORE_MINIMUM = auto()

    @classmethod
    @cache
    def firestore_mapping(cls):
        from google.cloud.firestore_v1.transforms import (
            SERVER_TIMESTAMP,
            DELETE_FIELD,
            ArrayRemove,
            ArrayUnion,
            Increment,
            Maximum,
            Minimum,
        )

        return {
            cls.FIRESTORE_TIMESTAMP: lambda _: SERVER_TIMESTAMP,
            cls.FIRESTORE_DELETE: lambda _: DELETE_FIELD,
            cls.FIRESTORE_REMOVE: ArrayRemove,
            cls.FIRESTORE_UNION: ArrayUnion,
            cls.FIRESTORE_INCREMENT: Increment,
            cls.FIRESTORE_MAXIMUM: Maximum,
            cls.FIRESTORE_MINIMUM: Minimum,
        }

    def to_firestore(self, *, value=None, **kwargs) -> object:
        return self.__class__.firestore_mapping()[self](value)


FIRESTORE_TIMESTAMP = Sentinel.FIRESTORE_TIMESTAMP
FIRESTORE_DELETE = Sentinel.FIRESTORE_DELETE

FIRESTORE_REMOVE = Sentinel.FIRESTORE_REMOVE
FIRESTORE_UNION = Sentinel.FIRESTORE_UNION

FIRESTORE_INCREMENT = Sentinel.FIRESTORE_INCREMENT
FIRESTORE_MAXIMUM = Sentinel.FIRESTORE_MAXIMUM
FIRESTORE_MINIMUM = Sentinel.FIRESTORE_MINIMUM

FirestoreArray = Literal[Sentinel.FIRESTORE_REMOVE, Sentinel.FIRESTORE_UNION]
FirestoreNumeric = Literal[
    Sentinel.FIRESTORE_INCREMENT, Sentinel.FIRESTORE_MAXIMUM, Sentinel.FIRESTORE_MINIMUM
]
FirestoreMinMax = Literal[Sentinel.FIRESTORE_MAXIMUM, Sentinel.FIRESTORE_MINIMUM]

FirestoreTimestamp = Annotated[
    Literal[Sentinel.FIRESTORE_TIMESTAMP], firestore_serializer
]
FirestoreDelete = Annotated[Literal[Sentinel.FIRESTORE_DELETE], firestore_serializer]


def _serialize_sentinel(value: Any, handler: Callable, info: ValidationInfo):
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and (isinstance(value[0], Sentinel) or value[0] in Sentinel)
    ):
        sentinel, value = value
        return Sentinel(sentinel).to_firestore(value=handler(value))
    else:
        return handler(value)


sentinel_serializer = WrapSerializer(_serialize_sentinel, return_type=object)

T = TypeVar("T")
FirestoreSentinel = Annotated[Union[T, Tuple[Sentinel, T]], sentinel_serializer]
