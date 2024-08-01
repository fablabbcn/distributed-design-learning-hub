import warnings
from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, NewType, Optional, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = NewType("DataclassInstance", Any)

DataClassSubtype = TypeVar("DataClassSubtype", bound=DataclassInstance)

T = TypeVar("T")


class Model:
    @classmethod
    def from_dict(
        cls: type[DataClassSubtype], **kwargs: dict[str, Any]
    ) -> DataClassSubtype:
        allowed_keys = set(f.name for f in fields(cls))
        nulls = {k: None for k in allowed_keys}
        allowed_values = {
            k: v for (k, v) in kwargs.items() if k in allowed_keys
        }
        return cls(**{**nulls, **allowed_values})

    def asdict(self: DataClassSubtype) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, field: str) -> Any:
        warnings.warn(
            "Accessing fields of %s using subscript notation is deprecated!"
            % type(self)
        )
        return getattr(self, field)

    def __setitem(self, field: str, value: Any) -> None:
        warnings.warn(
            "Accessing fields of %s using subscript notation is deprecated! "
            % type(self)
        )
        return setattr(self, field, value)

    def get(self, field: str, default: Optional[T] = None) -> Any:
        warnings.warn(
            "Accessing fields of %s using get is deprecated!" % type(self)
        )
        value = getattr(self, field)
        if value:
            return value
        else:
            return default


@dataclass
class Document(Model):
    link: str
    author: str
    title: str
    topic: str
    format: str
    format_type: str
    description: str
    themes: list[str]
    tags: list[str]
    image_url: Optional[str]


@dataclass
class Theme(Model):
    name: str
    summary: str
    documents: list[str]
    tags: set[str]


@dataclass
class Stats(Model):
    total_documents: int
    total_themes: int
    total_text_format: int
    total_audiovisual_format: int
    total_tool_format: int
    total_course_format: int
    total_unique_authors: int
