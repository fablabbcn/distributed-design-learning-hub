from __future__ import annotations

import traceback
import warnings
from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, NewType, Optional, TypeVar, cast

from ddlh.utils import compact, url_to_id

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
        allowed_values = {k: v for (k, v) in kwargs.items() if k in allowed_keys}
        return cls(**{**nulls, **allowed_values})

    def asdict(self: DataClassSubtype) -> dict[str, Any]:
        return asdict(self)

    def _warn_dict_like_access_deprecated(
        self, method_name: str = "subscript notation"
    ) -> None:
        template = (
            "Accessing fields of %s using %s is deprecated! "
            "Use dot notation to access model fields. Traceback:\n%s"
        )
        warnings.warn(
            template
            % (
                type(self),
                method_name,
                "\n".join(traceback.format_stack(limit=5)),
            )
        )

    def __getitem__(self, field: str) -> Any:
        self._warn_dict_like_access_deprecated()
        return getattr(self, field)

    def __setitem(self, field: str, value: Any) -> None:
        self._warn_dict_like_access_deprecated()
        return setattr(self, field, value)

    def get(self, field: str, default: Optional[T] = None) -> Any:
        self._warn_dict_like_access_deprecated(method_name="get")
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
    invisible_link: Optional[str]
    invisible_text: Optional[str]

    @property
    def id(self) -> str:
        return url_to_id(self.link)

    @property
    def embeddable_text(self) -> str:
        return "\n\n".join(
            compact(
                [
                    self.title,
                    self.description,
                    self.invisible_text,
                    "Themes: " + ", ".join(self.themes),
                    "Tags: " + ", ".join(self.tags),
                ]
            )
        )

    def enrich_with_text(self, text: str) -> DocumentWithText:
        return DocumentWithText.from_dict(**{**self.asdict(), **{"text": text}})


@dataclass
class DocumentWithText(Document):
    text: str

    @property
    def embeddable_text(self) -> str:
        return "\n\n------\n\n".join([super().embeddable_text, self.text])


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


@dataclass
class DocumentSummary(Model):
    document: str
    summary: str


@dataclass
class Summary(Model):
    top_sentence: Optional[str]
    document_summaries: list[DocumentSummary]

    @classmethod
    def from_dict(cls, **kwargs: dict[str, Any]) -> Summary:
        top_sentence = cast(str, kwargs["top_sentence"])
        summaries_data = cast(list[dict[str, Any]], kwargs["document_summaries"])
        document_summaries = [DocumentSummary.from_dict(**ds) for ds in summaries_data]
        return Summary(top_sentence=top_sentence, document_summaries=document_summaries)


@dataclass
class SearchResult(Model):
    query: str
    documents: list[str]
    summary: Summary

    @classmethod
    def from_dict(cls, **kwargs: dict[str, Any]) -> SearchResult:
        query = cast(str, kwargs["query"])
        documents = cast(list[str], kwargs["documents"])
        summary_data = kwargs["summary"]
        summary = Summary.from_dict(**summary_data)
        return SearchResult(query=query, documents=documents, summary=summary)
