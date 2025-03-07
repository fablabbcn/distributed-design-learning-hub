from collections import OrderedDict, defaultdict
from typing import Optional, cast

import more_itertools as mit
from pyairtable.api.types import RecordDict
from pydash import _

from .airtable import AirtableDB
from .models import Document, Stats, Theme
from .utils import url_to_id


class DocumentsRepository:

    def __init__(self, airtable: AirtableDB):
        self.airtable: AirtableDB = airtable
        self.documents: dict[str, Document] = {}
        self.featured_document_ids: list[str] = []
        self.airtable_ids_to_ids: dict[str, str] = {}
        self.themes: OrderedDict[str, Theme] = OrderedDict()
        self.tags: dict[str, list[str]] = defaultdict(list)
        self.authors: set[str] = set()
        self.by_format_type: dict[str, list[str]] = defaultdict(list)

        for row in self.airtable.all("featured_documents"):
            self._ingest_featured_document(row)

        for row in self.airtable.all("themes"):
            self._ingest_theme(row)

        for row in self.airtable.all("documents"):
            self._ingest_document(row)

    def _ingest_featured_document(self, row: RecordDict) -> None:
        airtable_id = _.get(row, "fields.document.0")
        if airtable_id:
            self.featured_document_ids.append(airtable_id)

    def _ingest_document(self, row: RecordDict) -> None:
        document = row["fields"]
        if document.get("live"):
            theme_names = []
            for theme_id in document.get("themes", []):
                theme = self.themes.get(theme_id)
                if theme:
                    theme.documents.append(document["link"])
                    theme.tags.update(document.get("tags", []))
                    theme_names.append(theme.name)
            document["themes"] = theme_names

            if "tags" not in document:
                document["tags"] = []
            for tag in document["tags"]:
                self.tags[tag].append(document["link"])

            format_id = mit.nth(document.get("format", []), 0)
            if format_id is not None:
                format = _.get(self.airtable.get("formats", format_id), "fields")
                if format is not None and format.get("live"):
                    document["format"] = format["name"]
                    document["format_type"] = format["type"]
                    self.by_format_type[format["type"]].append(document["link"])

            if "author" in document:
                self.authors.add(document["author"])

            id = url_to_id(document["link"])
            self.airtable_ids_to_ids[row["id"]] = id
            self.documents[id] = Document.from_dict(**document)

    def _ingest_theme(self, row: RecordDict) -> None:
        fields = row["fields"]
        if fields.get("live"):
            id = row["id"]
            self.themes[id] = Theme(
                name=fields["name"],
                summary=fields["summary"],
                documents=[],
                tags=set(),
            )

    def get_all_documents(self) -> list[Document]:
        return list(self.documents.values())

    def get_all_tags(self) -> list[str]:
        return list(self.tags.keys())

    def get_all_themes(self) -> list[str]:
        return [theme.name for theme in self.themes.values()]

    def get_documents_for_tag(self, tag: str) -> list[Document]:
        return [self.documents[url_to_id(link)] for link in self.tags[tag]]

    def get_documents_for_theme(self, theme_name: str) -> list[Document]:
        for theme in self.themes.values():
            if theme_name == theme.name:
                return [self.documents[url_to_id(link)] for link in theme.documents]
        return []

    def get_documents_for_format_type(self, format_type: str) -> list[Document]:
        if format_type in self.by_format_type:
            return [
                self.documents[url_to_id(link)]
                for link in self.by_format_type[format_type]
            ]
        return []

    def get_tags_for_theme(self, theme_name: str) -> list[str]:
        for theme in self.themes.values():
            if theme_name == theme.name:
                return list(theme.tags)
        return []

    def get_theme(self, theme_name: str) -> Optional[Theme]:
        for theme in self.themes.values():
            if theme_name == theme.name:
                return theme
        return None

    def get_document(self, id: str) -> Optional[Document]:
        return self.documents.get(id)

    def get_featured_documents(self) -> list[Document]:
        return cast(
            list[Document],
            _.compact(
                [
                    self.get_document(self.airtable_ids_to_ids[id])
                    for id in self.featured_document_ids
                ]
            ),
        )

    def get_stats(self) -> Stats:
        return Stats(
            total_documents=len(self.documents),
            total_themes=len(self.themes),
            total_text_format=len(self.by_format_type["text"]),
            total_audiovisual_format=len(self.by_format_type["audiovisual"]),
            total_tool_format=len(self.by_format_type["tool"]),
            total_course_format=len(self.by_format_type["course"]),
            total_unique_authors=len(self.authors),
        )
