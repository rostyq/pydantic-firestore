from typing import (
    Callable,
    ClassVar,
    Union,
    Optional,
    cast,
    TYPE_CHECKING,
    Iterable,
    Any,
    Literal,
    TypedDict,
    Unpack,
    NotRequired,
    Awaitable,
    overload,
)
from itertools import chain, takewhile, zip_longest
from functools import lru_cache, cache
from inspect import isclass

from pydantic import BaseModel

from .reference import FirestoreCollection
from .document import GenericModel
from .snapshot import FirestoreSnapshot
from .utils import to_flatten


if TYPE_CHECKING:
    from google.api_core.retry import Retry
    from google.cloud.firestore import (
        Transaction,
        AsyncTransaction,
        Client,
        AsyncClient,
        WriteOption,
        Query,
        AsyncQuery,
        WriteBatch,
        AsyncWriteBatch,
        DocumentReference,
        AsyncDocumentReference,
        CollectionReference,
        AsyncCollectionReference,
    )
    from google.cloud.firestore_v1.types import WriteResult
    from google.cloud.firestore_v1.document import Timestamp
    from google.cloud.firestore_v1.bulk_writer import BulkWriter


Source = Union[
    "Client",
    "AsyncClient",
    "Transaction",
    "AsyncTransaction",
    "WriteBatch",
    "AsyncWriteBatch",
    "BulkWriter",
]


class PydanticParams(TypedDict):
    include: NotRequired[Iterable[str] | None]
    exclude: NotRequired[Iterable[str] | None]
    by_alias: NotRequired[bool]
    exclude_unset: NotRequired[bool]
    exclude_defaults: NotRequired[bool]
    exclude_none: NotRequired[bool]
    round_trip: NotRequired[bool]
    warnings: NotRequired[bool | Literal["none", "warn", "error"]]
    fallback: NotRequired[Callable[[Any], Any] | None]
    serialize_as_any: NotRequired[bool]
    context: NotRequired[Any | None]


class FirestoreBaseParams(TypedDict):
    retry: NotRequired[Optional["Retry"]]
    timeout: NotRequired[float | None]


class FirestoreCreateParams(FirestoreBaseParams):
    attempts: NotRequired[int | None]


class FirestoreReadParams(FirestoreBaseParams):
    field_paths: NotRequired[Iterable[str] | None]


class FirestoreUpdateParams(FirestoreCreateParams):
    option: NotRequired[Optional["WriteOption"]]


class FirestoreSetParams(FirestoreCreateParams):
    merge: NotRequired[bool]


class FirestoreWriteParams(FirestoreSetParams, FirestoreUpdateParams):
    pass


class CreateParams(FirestoreCreateParams, PydanticParams):
    pass


class UpdateParams(FirestoreUpdateParams, PydanticParams):
    pass


class SetParams(FirestoreSetParams, PydanticParams):
    pass


class FirestoreDict(TypedDict, total=False):
    id_field: str
    path_fields: tuple[str, ...]
    location: Union[str, tuple[str, ...]]


@cache
def default_param():
    from google.api_core.gapic_v1.method import DEFAULT

    return DEFAULT


class FirestoreHandler:
    def create(
        self,
        reference: "DocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreCreateParams],
    ) -> Optional["WriteResult"]:
        return reference.create(
            data,
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
        )

    def set(
        self,
        reference: "DocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreSetParams],
    ) -> Optional["WriteResult"]:
        return reference.set(
            data,
            merge=kwargs.get("merge", False),
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
        )

    def update(
        self,
        reference: "DocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreUpdateParams],
    ) -> Optional["WriteResult"]:
        return reference.update(
            data,
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
            option=kwargs.get("option"),
        )

    def delete(
        self,
        reference: "DocumentReference",
        **kwargs: Unpack[FirestoreUpdateParams],
    ) -> Optional["Timestamp"]:
        return reference.delete(
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
            option=kwargs.get("option"),
        )

    def write(
        self,
        method: Literal["create", "set", "update", "delete"],
        reference: "DocumentReference",
        data: dict | None = None,
        **kwargs: Unpack[FirestoreWriteParams],
    ) -> "Union[None, WriteResult, Timestamp]":
        return getattr(self, method)(reference, data=data, **kwargs)


class AsyncFirestoreHandler:
    async def create(
        self,
        reference: "AsyncDocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreCreateParams],
    ) -> Optional["WriteResult"]:
        return await reference.create(
            data,
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
        )

    async def set(
        self,
        reference: "AsyncDocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreSetParams],
    ) -> Optional["WriteResult"]:
        return await reference.set(
            data,
            merge=kwargs.get("merge", False),
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
        )

    async def update(
        self,
        reference: "AsyncDocumentReference",
        data: dict,
        **kwargs: Unpack[FirestoreUpdateParams],
    ) -> Optional["WriteResult"]:
        return await reference.update(
            data,
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
            option=kwargs.get("option"),
        )

    async def delete(
        self,
        reference: "AsyncDocumentReference",
        **kwargs: Unpack[FirestoreUpdateParams],
    ) -> Optional["Timestamp"]:
        return await reference.delete(
            timeout=kwargs.get("timeout"),
            retry=kwargs.get("retry", default_param()),
            option=kwargs.get("option"),
        )

    async def write(
        self,
        method: Literal["create", "set", "update", "delete"],
        reference: "AsyncDocumentReference",
        data: dict | None = None,
        **kwargs: Unpack[FirestoreWriteParams],
    ) -> "Union[None, WriteResult, Timestamp]":
        return await getattr(self, method)(reference, data=data, **kwargs)


class TransactionHandler(FirestoreHandler):
    def __init__(
        self,
        writer: "Union[Transaction, AsyncTransaction, WriteBatch, AsyncWriteBatch]",
    ):
        self.writer = writer

    def create(self, reference, data, **kwargs):
        self.writer.create(reference, data)

    def set(self, reference, data, **kwargs):
        self.writer.set(
            reference,
            data,
            merge=kwargs.get("merge", False),
        )

    def update(self, reference, data, **kwargs):
        self.writer.update(
            reference,
            data,
            option=kwargs.get("option"),
        )

    def delete(self, reference, **kwargs):
        self.writer.delete(reference, option=kwargs.get("option"))


class BulkHandler(FirestoreHandler):
    def __init__(self, writer: "BulkWriter"):
        self.writer = writer

    def create(self, reference, data, **kwargs):
        self.writer.create(reference, data, attempts=kwargs.get("attempts", 0))

    def set(self, reference, data, **kwargs):
        self.writer.set(
            reference,
            data,
            merge=kwargs.get("merge", False),
            attempts=kwargs.get("attempts", 0),
        )

    def update(self, reference, data, **kwargs):
        self.writer.update(
            reference,
            data,
            option=kwargs.get("option"),
            attempts=kwargs.get("attempts", 0),
        )

    def delete(self, reference, **kwargs):
        self.writer.delete(
            reference, option=kwargs.get("option"), attempts=kwargs.get("attempts", 0)
        )


fallback_handler = FirestoreHandler()
async_fallback_handler = AsyncFirestoreHandler()


@lru_cache
def source_to_handler(
    source: Source,
) -> tuple[
    "Union[Client, AsyncClient]", Union[FirestoreHandler, AsyncFirestoreHandler]
]:
    from google.cloud.firestore import (
        Transaction,
        WriteBatch,
        Client,
        AsyncClient,
        AsyncWriteBatch,
        AsyncTransaction,
    )
    from google.cloud.firestore_v1.bulk_writer import BulkWriter

    if isinstance(source, (Transaction, AsyncTransaction, WriteBatch, AsyncWriteBatch)):
        return source._client, TransactionHandler(source)
    elif isinstance(source, BulkWriter):
        return source._client, BulkHandler(source)
    elif isinstance(source, Client):
        return source, fallback_handler
    elif isinstance(source, AsyncClient):
        return source, async_fallback_handler
    else:
        raise ValueError("Invalid firestore source")


@lru_cache
def source_to_tuple(
    source: "Union[Client, Transaction, WriteBatch, BulkWriter]",
) -> "tuple[Client, Optional[Transaction]]":
    from google.cloud.firestore import Transaction, Client

    if isinstance(source, Transaction):
        return source._client, source
    elif isinstance(source, Client):
        return source, None
    else:
        raise ValueError("Invalid firestore source")


@lru_cache
def async_source_to_tuple(
    source: "Union[Client, AsyncClient, AsyncTransaction, AsyncWriteBatch]",
) -> "tuple[AsyncClient, Optional[AsyncTransaction]]":
    from google.cloud.firestore import AsyncTransaction, AsyncClient

    if isinstance(source, AsyncTransaction):
        return source._client, source
    elif isinstance(source, AsyncClient):
        return source, None
    else:
        raise ValueError("Invalid firestore source")


class FirestoreModel(BaseModel):
    firestore_id_field: ClassVar[str | None] = None
    firestore_path_fields: ClassVar[tuple[str, ...]] = ()
    firestore_location: ClassVar[tuple[str, ...]] = ()
    firestore_config: ClassVar[FirestoreDict] = {}

    def __init_subclass__(cls, **kwargs):
        if (id_field := cls.firestore_config.get("id_field")) is not None:
            cls.firestore_id_field = str(id_field)
        if (location := cls.firestore_config.get("location")) is not None:
            cls.firestore_location = (
                (location,) if isinstance(location, str) else location
            )
        if (path_fields := cls.firestore_config.get("path_fields")) is not None:
            cls.firestore_path_fields = path_fields

        if cls.firestore_location != ():
            for value in cls.__dict__.values():
                if isclass(value) and issubclass(value, FirestoreModel):
                    value.firestore_location = cls.firestore_location
                    value.firestore_id_field = cls.firestore_id_field
                    value.firestore_path_fields = cls.firestore_path_fields

        super().__init_subclass__(**kwargs)

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

    @overload
    @classmethod
    def document_reference(
        cls, client: "Client", id: str, *args: str
    ) -> "DocumentReference": ...
    @overload
    @classmethod
    def document_reference(
        cls, client: "AsyncClient", id: str, *args: str
    ) -> "AsyncDocumentReference": ...
    @classmethod
    def document_reference(
        cls, client: "Union[Client, AsyncClient]", id: str, *args: str
    ) -> "Union[DocumentReference, AsyncDocumentReference]":
        return cls.firestore_document(id, *args).to_firestore(client)

    @overload
    @classmethod
    def collection_reference(
        cls, client: "Client", *args: str
    ) -> "CollectionReference": ...
    @overload
    @classmethod
    def collection_reference(
        cls, client: "AsyncClient", *args: str
    ) -> "AsyncCollectionReference": ...
    @classmethod
    def collection_reference(
        cls, client: "Union[Client, AsyncClient]", *args: str
    ) -> "Union[CollectionReference, AsyncCollectionReference]":
        return cls.firestore_collection(*args).to_firestore(client)

    @classmethod
    def firestore_dump(
        cls, data: GenericModel, **kwargs: Unpack[PydanticParams]
    ) -> dict[str, Any]:
        return data.__pydantic_serializer__.to_python(
            data,
            mode="python",
            by_alias=kwargs.get("by_alias", True),
            exclude=kwargs.get("exclude"),
            include=kwargs.get("include"),
            exclude_unset=kwargs.get("exclude_unset", False),
            exclude_defaults=kwargs.get("exclude_defaults", False),
            exclude_none=kwargs.get("exclude_none", False),
            warnings=kwargs.get("warnings", True),
            round_trip=kwargs.get("round_trip", False),
            fallback=kwargs.get("fallback"),
            serialize_as_any=kwargs.get("serialize_as_any", False),
            context=kwargs.get("context"),
        )

    @classmethod
    def firestore_write(
        cls,
        method: Literal["create", "set", "update", "delete"],
        source: Source,
        id: str,
        *args: str,
        data: dict[str, Any] | None = None,
        **kwargs: Unpack[FirestoreWriteParams],
    ):
        client, handler = source_to_handler(source)
        return handler.write(
            method, cls.document_reference(client, id, *args), data=data, **kwargs
        )

    @classmethod
    def firestore_create(
        cls,
        source: Source,
        data: GenericModel,
        id: str,
        *args: str,
        **kwargs: Unpack[CreateParams],
    ):
        return cls.firestore_write(
            "create",
            source,
            id,
            *args,
            data=cls.firestore_dump(data, **kwargs),
            **kwargs,
        )

    @classmethod
    def firestore_set(
        cls,
        source: Source,
        data: GenericModel,
        id: str,
        *args: str,
        **kwargs: Unpack[SetParams],
    ) -> Optional["WriteResult"]:
        return cls.firestore_write(
            "set",
            source,
            id,
            *args,
            data=cls.firestore_dump(data, **kwargs),
            **kwargs,
        )

    @classmethod
    def firestore_context(cls, **kwargs) -> dict[str]:
        return {
            "firestore_id_field": cls.firestore_id_field,
            "firestore_path_fields": cls.firestore_path_fields,
            **kwargs,
        }

    @overload
    @classmethod
    def firestore_read(
        cls: type[GenericModel],
        source: Union["Client", "Transaction"],
        id: str,
        *args: str,
        strict: bool = False,
        context: dict[str, Any] | None = None,
        **kwargs: Unpack[FirestoreReadParams],
    ) -> FirestoreSnapshot[GenericModel]:
        client, transaction = source_to_tuple(source)
        _cls = cast(type[FirestoreModel], cls)
        return FirestoreSnapshot[cls].from_firestore(
            _cls.document_reference(client, id, *args).get(
                transaction=transaction,
                field_paths=kwargs.get("field_paths"),
                timeout=kwargs.get("timeout"),
                retry=kwargs.get("retry"),
            ),
            strict=strict,
            context=_cls.firestore_context(**(context or {})),
        )

    @classmethod
    async def firestore_read_async(
        cls: type[GenericModel],
        source: Union["AsyncClient", "AsyncTransaction"],
        id: str,
        *args: str,
        strict: bool = False,
        context: dict[str, Any] | None = None,
        **kwargs: Unpack[FirestoreReadParams],
    ) -> FirestoreSnapshot[GenericModel]:
        client, transaction = async_source_to_tuple(source)
        _cls = cast(type[FirestoreModel], cls)
        return FirestoreSnapshot[cls].from_firestore(
            await _cls.document_reference(client, id, *args).get(
                transaction=transaction,
                field_paths=kwargs.get("field_paths"),
                timeout=kwargs.get("timeout"),
                retry=kwargs.get("retry"),
            ),
            strict=strict,
            context=_cls.firestore_context(**(context or {})),
        )

    @classmethod
    def firestore_update(
        cls,
        source: Source,
        data: GenericModel,
        id: str,
        *args: str,
        ignore_flatten: Iterable[str] | None = None,
        **kwargs: Unpack[UpdateParams],
    ) -> Optional["WriteResult"]:
        return cls.firestore_write(
            "update",
            source,
            id,
            *args,
            data=to_flatten(
                cls.firestore_dump(data, exclude_unset=True, **kwargs),
                exclude=ignore_flatten,
            ),
            **kwargs,
        )

    @classmethod
    def firestore_delete(
        cls,
        source: Source,
        id: str,
        *args: str,
        **kwargs: Unpack[FirestoreUpdateParams],
    ) -> Optional["Timestamp"]:
        return cls.firestore_write("delete", source, id, *args, **kwargs)

    @overload
    @classmethod
    def firestore_query(
        cls,
        source: "Union[Client, Transaction]",
        *args: str,
    ) -> "Query": ...
    @overload
    @classmethod
    def firestore_query(
        cls,
        source: "Union[AsyncClient, AsyncTransaction]",
        *args: str,
    ) -> "AsyncQuery": ...
    @classmethod
    def firestore_query(
        cls,
        source: "Union[Client, AsyncClient, Transaction, AsyncTransaction]",
        *args: str,
    ) -> "Union[Query, AsyncQuery]":
        client, _ = source_to_handler(source)
        return cls.collection_reference(client, *args)._query()

    def _firestore_path(self, *args: str) -> tuple[str, ...]:
        if (len_args := len(args)) == (len_loc := len(self.firestore_location)):
            id, *args = args
        elif len_args == (len_loc - 1):
            id = getattr(self, self.firestore_id_field)
        else:
            id, args = getattr(self, self.firestore_id_field), tuple(
                getattr(self, field_name) for field_name in self.firestore_path_fields
            )
        return (id, args)

    def create_to_firestore(
        self,
        source: Source,
        *args: str,
        context: dict[str, Any] | None = None,
        **kwargs: Unpack[CreateParams],
    ):
        id, args = self._firestore_path(*args)
        return self.firestore_create(source, self, id, *args, context=context, **kwargs)

    def set_to_firestore(
        self,
        source: Source,
        *args: str,
        context: dict[str, Any] | None = None,
        **kwargs: Unpack[SetParams],
    ):
        id, args = self._firestore_path(*args)
        return self.firestore_set(source, self, id, *args, context=context, **kwargs)

    def update_to_firestore(
        self,
        source: Source,
        *args: str,
        ignore_flatten: Iterable[str] | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Unpack[UpdateParams],
    ):
        id, args = self._firestore_path(*args)
        return self.firestore_update(
            source,
            self,
            id,
            *args,
            ignore_flatten=ignore_flatten,
            context=context,
            **kwargs,
        )

    def delete_to_firestore(
        self,
        source: Source,
        *args: str,
        **kwargs: Unpack[FirestoreUpdateParams],
    ):
        id, args = self._firestore_path(*args)
        return self.firestore_delete(source, id, *args, **kwargs)
