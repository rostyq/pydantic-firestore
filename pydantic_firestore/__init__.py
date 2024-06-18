from typing import Optional, TYPE_CHECKING, Iterable

from pydantic import BaseModel

from .path import FirestorePath
from .reference import FirestoreCollection, FirestoreDocument
from .snapshot import FirestoreSnapshot
from .location import FirestoreLocation, Source

if TYPE_CHECKING:
    from google.api_core.retry import Retry


__all__ = [
    "FirestorePath",
    "FirestoreCollection",
    "FirestoreDocument",
    "FirestoreSnapshot",
    "FirestoreLocation",
    "FirestoreModel",
]


class FirestoreModel(BaseModel, FirestoreLocation):
    def create_to_firestore(
        self,
        source: Source,
        id: str,
        *args: str,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
    ):
        return self.firestore_create(
            source, self, id, *args, retry=retry, timeout=timeout
        )

    def set_to_firestore(
        self,
        source: Source,
        id: str,
        *args: str,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
        merge: bool = False,
    ):
        return self.firestore_set(
            source, self, id, *args, merge=merge, retry=retry, timeout=timeout
        )

    def update_to_firestore(
        self,
        source: Source,
        id: str,
        *args: str,
        retry: Optional["Retry"] = None,
        timeout: Optional[float] = None,
        ignore_flatten: Iterable[str] | None = None,
    ):
        return self.firestore_update(
            source,
            self,
            id,
            *args,
            retry=retry,
            timeout=timeout,
            ignore_flatten=ignore_flatten,
        )
