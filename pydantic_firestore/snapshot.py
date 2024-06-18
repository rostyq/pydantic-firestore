from typing import Any, Generic, TYPE_CHECKING, Annotated, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, AliasChoices, AliasPath

from .reference import collection_validator, FirestoreCollection, FirestoreDocument
from .document import GenericModel, DocumentModel, document_validator

if TYPE_CHECKING:
    from google.cloud.firestore import DocumentSnapshot


def fix_snapshot(obj: "DocumentSnapshot") -> "DocumentSnapshot":
    for key in ("create_time", "update_time", "read_time"):
        value = obj.__dict__.get(key, None)

        if (
            value is not None
            and not isinstance(value, datetime)
            and hasattr(value, "ToDatetime")
        ):
            obj.__dict__[key] = value.ToDatetime()

    return obj


class FirestoreSnapshot(BaseModel, Generic[GenericModel]):
    id: str = Field(
        validation_alias=AliasChoices(AliasPath("_reference", "_path", -1), "id")
    )
    path: Annotated[FirestoreCollection, collection_validator] = Field(
        validation_alias=AliasChoices(AliasPath("_reference", "_path"), "path")
    )

    read_time: datetime

    create_time: datetime | None = Field(None, exclude=True)
    update_time: datetime | None = Field(None, exclude=True)

    document: Annotated[Optional[DocumentModel[GenericModel]], document_validator] = (
        Field(None, validation_alias=AliasChoices("_data", "document"))
    )

    model_config = ConfigDict(frozen=True)

    @property
    def reference(self) -> FirestoreDocument:
        return self.path.document(self.id)

    @property
    def exists(self) -> bool:
        return self.document is not None

    @property
    def data(self):
        return self.document.data if self.document is not None else None

    @classmethod
    def from_firestore(
        cls,
        snapshot: "DocumentSnapshot",
        strict: bool = False,
        context: dict[str, Any] | None = None,
    ) -> "FirestoreSnapshot[GenericModel]":
        return cls.__pydantic_validator__.validate_python(
            fix_snapshot(snapshot), strict=strict, from_attributes=True, context=context
        )
