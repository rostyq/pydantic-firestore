from typing import TypeVar, Generic
from enum import Enum, auto, global_enum
from functools import cache
from numbers import Number

from pydantic import RootModel, Field, ConfigDict, model_serializer

from .utils import to_firestore


N = TypeVar("N", bound=Number)
Item = TypeVar("Item")


@global_enum
class Sentinel(Enum):
    FIRESTORE_TIMESTAMP = auto()
    FIRESTORE_DELETE = auto()

    @classmethod
    @cache
    def firestore_mapping(cls):
        from google.cloud.firestore_v1.transforms import SERVER_TIMESTAMP, DELETE_FIELD

        return {cls.FIRESTORE_TIMESTAMP: SERVER_TIMESTAMP, cls.FIRESTORE_FIELD: DELETE_FIELD}

    def to_firestore(self, **kwargs):
        return self.__class__.firestore_mapping()[self]


class Array(RootModel, Generic[Item]):
    root: list[Item] = Field(kw_only=False)

    def __len__(self):
        return len(self.root)

    def __iter__(self):
        return self.root.__iter__()


class ArrayRemove(Array[Item]):
    @model_serializer(mode="plain", return_type=object)
    def to_firestore(self, **kwargs):
        from google.cloud.firestore_v1.transforms import ArrayRemove

        return ArrayRemove(self.root)


class ArrayUnion(Array[Item]):
    @model_serializer(mode="plain", return_type=object)
    def to_firestore(self, **kwargs):
        from google.cloud.firestore_v1.transforms import ArrayUnion

        return ArrayUnion(self.root)


class Numeric(RootModel, Generic[N]):
    root: N = Field(kw_only=False)
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    def __gt__(self, other):
        return self.root > other

    def __lt__(self, other):
        return self.root < other

    def __ge__(self, other):
        return self.root >= other

    def __le__(self, other):
        return self.root <= other


class Increment(Numeric[N]):
    @model_serializer(mode="plain", return_type=object)
    def to_firestore(self, **kwargs):
        from google.cloud.firestore_v1.transforms import Increment

        return Increment(to_firestore(self.root))


class Maximum(Numeric[N]):
    @model_serializer(mode="plain", return_type=object)
    def to_firestore(self, **kwargs):
        from google.cloud.firestore_v1.transforms import Maximum

        return Maximum(to_firestore(self.root))


class Minimum(Numeric[N]):
    @model_serializer(mode="plain", return_type=object)
    def to_firestore(self, **kwargs):
        from google.cloud.firestore_v1.transforms import Minimum

        return Minimum(to_firestore(self.root))
