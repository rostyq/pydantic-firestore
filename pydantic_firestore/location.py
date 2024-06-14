from typing import ClassVar, Union, Optional, cast, TYPE_CHECKING
from abc import ABCMeta
from itertools import chain, takewhile, zip_longest
from functools import lru_cache

from .reference import FirestoreCollection
from .document import GenericModel
from .snapshot import FirestoreSnapshot
from .utils import to_flatten


if TYPE_CHECKING:
    from google.cloud.firestore import Transaction, Client, WriteOption
    from google.cloud.firestore_v1 import DocumentReference, CollectionReference
    from google.api_core.retry import Retry


Source = Union["Transaction", "Client"]


def source_to_tuple(source: Source) -> tuple["Client", Optional["Transaction"]]:
    return (source._client, source) if hasattr(source, "_client") else (source, None)


class FirestoreLocation(metaclass=ABCMeta):
    firestore_location: ClassVar[tuple[str, ...]] = ()

    @classmethod
    @lru_cache
    def firestore_collection(cls, *args: str):
        assert len(cls.firestore_location) > 0
        assert len(args) == len(cls.firestore_location) - 1, "Invalid args count"
        return FirestoreCollection(
            takewhile(
                lambda x: x is not None,
                chain.from_iterable(
                    zip_longest(cls.firestore_location, reversed(args))
                ),
            )
        )

    @classmethod
    def firestore_document(cls, id: str, *args: str):
        return cls.firestore_collection(*args).document(id)

    @classmethod
    def document_reference(
        cls, client: "Client", id: str, *args: str
    ) -> "DocumentReference":
        return cls.firestore_document(id, *args).to_firestore(client)

    @classmethod
    def collection_reference(
        cls, client: "Client", *args: str
    ) -> "CollectionReference":
        return cls.firestore_collection(*args).to_firestore(client)

    @classmethod
    def create_to_firestore(
        cls,
        source: Source,
        data: GenericModel,
        id: str,
        *args: str,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
        merge: Optional[bool] = None,
        **kwargs,
    ):
        client, transaction = source_to_tuple(source)
        reference = cls.document_reference(client, id, *args)

        data = data.__pydantic_serializer__.to_python(
            data, mode="python", by_alias=True, **kwargs
        )

        if transaction is not None:
            if merge is None:
                transaction.create(reference, data)
            else:
                transaction.set(reference, data, merge=merge)
        else:
            if merge is None:
                return reference.create(
                    data, timeout=timeout, retry=default_retry(retry)
                )
            else:
                return reference.set(
                    data, merge=merge, timeout=timeout, retry=default_retry(retry)
                )

    @classmethod
    def read_from_firestore(
        cls: type[GenericModel],
        source: Source,
        id: str,
        *args: str,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
    ) -> FirestoreSnapshot[GenericModel]:
        client, transaction = source_to_tuple(source)
        return FirestoreSnapshot[cls].from_firestore(
            cast(type["FirestoreLocation"], cls)
            .document_reference(client, id, *args)
            .get(transaction=transaction, timeout=timeout, retry=default_retry(retry))
        )

    @classmethod
    def update_to_firestore(
        cls,
        source: Source,
        data: GenericModel,
        id: str,
        *args: str,
        option: Optional["WriteOption"] = None,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
        ignore_flatten: set[str] | None = None,
        **kwargs,
    ):
        client, transaction = source_to_tuple(source)
        reference = cls.document_reference(client, id, *args)

        data = to_flatten(
            data.__pydantic_serializer__.to_python(
                data, mode="python", by_alias=True, exclude_unset=True, **kwargs
            ),
            exclude=ignore_flatten,
        )

        if transaction is not None:
            transaction.update(reference, data, option=option)
        else:
            return reference.update(
                data, timeout=timeout, retry=default_retry(retry), option=option
            )

    @classmethod
    def delete_from_firestore(
        cls,
        source: Source,
        id: str,
        *args: str,
        option: Optional["WriteOption"] = None,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
    ):
        client, transaction = source_to_tuple(source)
        reference = cls.document_reference(client, id, *args)

        if transaction is not None:
            transaction.delete(reference, option=option)
        else:
            return reference.delete(timeout=timeout, retry=default_retry(retry))


def default_retry(value: Optional["Retry"]) -> "Retry":
    from google.api_core.gapic_v1.method import DEFAULT

    return value if value is not None else DEFAULT
