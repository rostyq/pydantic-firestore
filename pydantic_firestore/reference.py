from typing import TYPE_CHECKING, Any

from pydantic import (
    RootModel,
    ConfigDict,
    model_validator,
    Field,
    WrapValidator,
    ValidatorFunctionWrapHandler
)

from .path import FirestorePath

if TYPE_CHECKING:
    from google.cloud.firestore import DocumentReference, Client, CollectionReference


class ReferenceModel(RootModel):
    root: FirestorePath = Field(kw_only=False)

    model_config = ConfigDict(frozen=True)

    def __iter__(self):
        return self.root.__iter__()

    def __str__(self) -> str:
        return str(self.root)

    @property
    def parent(self):
        parent = self.root.parent
        return self.__class__(parent) if parent is not None else None


class FirestoreDocument(ReferenceModel):
    @model_validator(mode="after")
    def check_path(self):
        assert self.root.is_document, f"Path is not a document: {self.root}"
        return self

    def collection(self, id: str) -> "FirestoreCollection":
        return FirestoreCollection(root=self.root / id)

    @property
    def parent(self):
        parent = self.root.parent
        return FirestoreCollection(root=parent) if parent is not None else None

    @classmethod
    def from_firestore(cls, value: "DocumentReference") -> "FirestoreDocument":
        return cls.model_validate(value._path)

    def to_firestore(self, client: "Client") -> "DocumentReference":
        return client.document(*self.root)


class FirestoreCollection(ReferenceModel):
    @model_validator(mode="after")
    def check_path(self):
        assert self.root.is_collection, f"Path is not a collection: {self.root}"
        return self

    def document(self, id: str) -> "FirestoreDocument":
        return FirestoreDocument(root=self.root / id)

    @property
    def parent(self):
        parent = self.root.parent
        return FirestoreDocument(root=parent) if parent is not None else None

    @classmethod
    def from_firestore(cls, value: "CollectionReference") -> "FirestoreCollection":
        return cls.model_validate(value._path)

    def to_firestore(self, client: "Client") -> "CollectionReference":
        return client.collection(*self.root)


def _validate_collection(value: Any, handler: ValidatorFunctionWrapHandler):
    if isinstance(value, FirestoreCollection):
        return value
    elif isinstance(value, tuple):
        path = FirestorePath(root=value)
        return FirestoreCollection(root=path.parent if path.is_document else path)
    else:
        return handler(value)


collection_validator = WrapValidator(_validate_collection)
