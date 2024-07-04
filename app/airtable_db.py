import os
from collections import defaultdict
from typing import Optional, TypedDict

from pyairtable import Api  # type: ignore

Document = TypedDict(
    "Document",
    {
        "link": str,
        "author": str,
        "title": str,
        "topic": str,
        "description": str,
        "themes": list[str],
        "tags": list[str],
    },
)


class AirtableDocumentDatabase:
    def __init__(
        self,
        token: Optional[str] = None,
        base_id: Optional[str] = None,
        table_id: Optional[str] = None,
    ):
        if token is None:
            token = os.environ.get("AIRTABLE_TOKEN")
        if base_id is None:
            base_id = os.environ.get("AIRTABLE_BASE_ID")
        if table_id is None:
            table_id = os.environ.get("AIRTABLE_TABLE_ID")
        self.api = Api(token)
        self.table = self.api.table(base_id, table_id)
        self.documents: dict[str, Document] = {}
        self.themes: dict[str, list[str]] = defaultdict(list)
        self.tags: dict[str, list[str]] = defaultdict(list)
        for row in self.table.all():
            document = row["fields"]
            self.documents[document["link"]] = document
            for theme in document.get("themes", []):
                self.themes[theme].append(document["link"])
            for tag in document.get("tags", []):
                self.tags[tag].append(document["link"])

    def get_all_documents(self) -> list[Document]:
        return list(self.documents.values())

    def get_all_tags(self) -> list[str]:
        return list(self.tags.keys())

    def get_all_themes(self) -> list[str]:
        return list(self.themes.keys())

    def get_documents_for_tag(self, tag: str) -> list[Document]:
        return [self.documents[link] for link in self.tags[tag]]

    def get_documents_for_theme(self, theme: str) -> list[Document]:
        return [self.documents[link] for link in self.themes[theme]]
