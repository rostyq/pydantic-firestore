from typing import Generic, TypeVar, Any
from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    AliasChoices,
    ValidationInfo,
    WrapValidator,
    ValidatorFunctionWrapHandler
)


GenericModel = TypeVar("GenericModel", bound=BaseModel)


class DocumentModel(BaseModel, Generic[GenericModel]):
    create_time: datetime
    update_time: datetime

    data: GenericModel = Field(validation_alias=AliasChoices("_data", "data"))

    model_config = ConfigDict(frozen=True, from_attributes=False)


def _validate_document(value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
    create_time = info.data.get("create_time")
    update_time = info.data.get("update_time")

    is_snapshot = create_time is not None and update_time is not None

    if is_snapshot and isinstance(value, dict):
        value = {
            "create_time": create_time,
            "update_time": update_time,
            "data": value,
        }

    return handler(value)


document_validator = WrapValidator(_validate_document)
