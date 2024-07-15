from typing import Union, TYPE_CHECKING, Any, Iterable
from uuid import UUID
from decimal import Decimal
from functools import singledispatch
from collections.abc import MutableMapping
from ipaddress import IPv4Address, IPv6Address

from pydantic import PlainSerializer
from pydantic_core import Url


if TYPE_CHECKING:
    from google.cloud.firestore_v1.field_path import FieldPath


@singledispatch
def to_firestore(value):
    if hasattr(value, "to_firestore"):
        return value.to_firestore()
    else:
        return value


@to_firestore.register
def _(value: Decimal) -> Union[int, float]:
    if value.as_integer_ratio()[1] == 1:
        return int(value)
    else:
        return float(value)


@to_firestore.register
def _(value: Url) -> str:
    return str(value)


@to_firestore.register
def _(value: UUID) -> str:
    return str(value)


@to_firestore.register
def _(value: IPv4Address) -> str:
    return str(value)


@to_firestore.register
def _(value: IPv6Address) -> str:
    return str(value)


def _to_flatten(
    obj: dict[str, Any],
    *,
    exclude: set["FieldPath"],
    parent: "FieldPath",
) -> dict["FieldPath", Any]:
    items: list[tuple["FieldPath", Any]] = []

    for key, value in obj.items():
        field = parent + key
        if field not in exclude and isinstance(value, MutableMapping):
            items.extend(_to_flatten(value, parent=field, exclude=exclude).items())
        else:
            items.append((field, value))

    return dict(items)


def to_flatten(
    obj: dict[str, Any],
    *,
    exclude: Iterable[str] | None = None,
) -> dict[str, Any]:
    from google.cloud.firestore_v1.field_path import FieldPath

    if exclude is None:
        exclude = set()
    else:
        exclude = {FieldPath.from_string(path) for path in exclude}

    output = _to_flatten(obj, exclude=exclude, parent=FieldPath())

    return {field.to_api_repr(): value for field, value in output.items()}


firestore_serializer = PlainSerializer(to_firestore, return_type=object)
