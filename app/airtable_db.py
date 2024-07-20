import os
from collections import defaultdict
from typing import Optional, TypedDict, cast

from pyairtable import Api

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

Theme = TypedDict(
    "Theme",
    {"name": str, "documents": list[str]},
)


class AirtableDocumentDatabase:
    def __init__(
        self,
        token: Optional[str] = None,
        base_id: Optional[str] = None,
        documents_table_id: Optional[str] = None,
        themes_table_id: Optional[str] = None,
    ):
        if token is None:
            token = os.environ["AIRTABLE_TOKEN"]
        if base_id is None:
            base_id = os.environ["AIRTABLE_BASE_ID"]
        if documents_table_id is None:
            documents_table_id = os.environ["AIRTABLE_DOCUMENTS_TABLE_ID"]
        if themes_table_id is None:
            themes_table_id = os.environ["AIRTABLE_THEMES_TABLE_ID"]
        self.api = Api(token)
        self.documents_table = self.api.table(base_id, documents_table_id)
        self.themes_table = self.api.table(base_id, themes_table_id)
        self.documents: dict[str, Document] = {}
        self.themes: dict[str, Theme] = {}
        self.tags: dict[str, list[str]] = defaultdict(list)
        for row in self.documents_table.all():
            document = row["fields"]
            for theme_id in document.get("themes", []):
                if theme_id not in self.themes:
                    theme_fields = self.themes_table.get(theme_id)["fields"]
                    self.themes[theme_id] = {
                        "name": theme_fields["name"],
                        "documents": [],
                    }

                self.themes[theme_id]["documents"].append(document["link"])
            document["themes"] = [
                self.themes[theme_id]["name"]
                for theme_id in document.get("themes", [])
            ]
            if "tags" not in document:
                document["tags"] = []
            for tag in document["tags"]:
                self.tags[tag].append(document["link"])
            self.documents[document["link"]] = cast(Document, document)

    def get_all_documents(self) -> list[Document]:
        return list(self.documents.values())

    def get_all_tags(self) -> list[str]:
        return list(self.tags.keys())

    def get_all_themes(self) -> list[str]:
        return [theme["name"] for theme in self.themes.values()]

    def get_documents_for_tag(self, tag: str) -> list[Document]:
        return [self.documents[link] for link in self.tags[tag]]

    def get_documents_for_theme(self, theme_name: str) -> list[Document]:
        for theme in self.themes.values():
            if theme_name == theme["name"]:
                return [self.documents[link] for link in theme["documents"]]
        return []
