from collections import OrderedDict, defaultdict
from typing import Optional, TypedDict, cast

import more_itertools as mit
from pyairtable.api.types import RecordDict
from pydash import _

from .airtable import AirtableDB
from .utils import url_to_id

Document = TypedDict(
    "Document",
    {
        "link": str,
        "author": str,
        "title": str,
        "topic": str,
        "format": str,
        "format_type": str,
        "description": str,
        "themes": list[str],
        "tags": list[str],
        "image_url": Optional[str],
    },
)

Theme = TypedDict(
    "Theme",
    {"name": str, "summary": str, "documents": list[str], "tags": set[str]},
)


class DocumentsRepository:

    def __init__(self, airtable: AirtableDB):
        self.airtable: AirtableDB = airtable
        self.documents: dict[str, Document] = {}
        self.themes: OrderedDict[str, Theme] = OrderedDict()
        self.tags: dict[str, list[str]] = defaultdict(list)

        for row in self.airtable.all("themes"):
            self._ingest_theme(row)

        for row in self.airtable.all("documents"):
            self._ingest_document(row)

    def _ingest_document(self, row: RecordDict) -> None:
        document = row["fields"]

        for theme_id in document.get("themes", []):
            self.themes[theme_id]["documents"].append(document["link"])
            self.themes[theme_id]["tags"].update(document.get("tags", []))
        document["themes"] = [
            self.themes[theme_id]["name"]
            for theme_id in document.get("themes", [])
        ]

        if "tags" not in document:
            document["tags"] = []
        for tag in document["tags"]:
            self.tags[tag].append(document["link"])

        format_id = mit.nth(document.get("format", []), 0)
        if format_id is not None:
            format = _.get(self.airtable.get("formats", format_id), "fields")
            if format is not None:
                document["format"] = format["name"]
                document["format_type"] = format["type"]

        self.documents[url_to_id(document["link"])] = cast(Document, document)

    def _ingest_theme(self, row: RecordDict) -> None:
        fields = row["fields"]
        id = row["id"]
        self.themes[id] = {
            "name": fields["name"],
            "summary": fields["summary"],
            "documents": [],
            "tags": set(),
        }

    def get_all_documents(self) -> list[Document]:
        return list(self.documents.values())

    def get_all_tags(self) -> list[str]:
        return list(self.tags.keys())

    def get_all_themes(self) -> list[str]:
        return [theme["name"] for theme in self.themes.values()]

    def get_documents_for_tag(self, tag: str) -> list[Document]:
        return [self.documents[url_to_id(link)] for link in self.tags[tag]]

    def get_documents_for_theme(self, theme_name: str) -> list[Document]:
        for theme in self.themes.values():
            if theme_name == theme["name"]:
                return [
                    self.documents[url_to_id(link)]
                    for link in theme["documents"]
                ]
        return []

    def get_tags_for_theme(self, theme_name: str) -> list[str]:
        for theme in self.themes.values():
            if theme_name == theme["name"]:
                return list(theme["tags"])
        return []

    def get_theme(self, theme_name: str) -> Optional[Theme]:
        for theme in self.themes.values():
            if theme_name == theme["name"]:
                return theme
        return None

    def get_document(self, id: str) -> Optional[Document]:
        return self.documents.get(id)
