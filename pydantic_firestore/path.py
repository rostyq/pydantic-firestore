from typing import Any, Self

from pydantic import (
    Field,
    RootModel,
    ConfigDict,
    model_serializer,
    model_validator,
    ValidationInfo,
)


class FirestorePath(RootModel):
    root: tuple[str, ...] = Field(kw_only=False)

    model_config = ConfigDict(frozen=True)

    @model_serializer(when_used="json")
    def to_json(self) -> str:
        return str(self)

    @model_validator(mode="before")
    def validate_path(value: Any, info: ValidationInfo):
        if isinstance(value, str):
            value = tuple(value.split("/"))

        return value

    @property
    def id(self) -> str:
        return self.root[-1]

    @property
    def root_id(self) -> str:
        return self.root[0]

    @property
    def parent_id(self) -> str | None:
        return self.root[-2]

    @property
    def is_root(self) -> bool:
        return len(self.root) == 1

    @property
    def is_document(self) -> bool:
        return len(self.root) % 2 == 0

    @property
    def is_collection(self) -> bool:
        return len(self.root) % 2 == 1

    @property
    def parent(self):
        return self.__class__(self.root[:-1]) if len(self.root) > 1 else None

    def __iter__(self):
        return self.root.__iter__()

    def __str__(self) -> str:
        return "/".join(self.root)

    def __truediv__(self, other) -> Self:
        return self.__class__((*self.root, str(other)))
