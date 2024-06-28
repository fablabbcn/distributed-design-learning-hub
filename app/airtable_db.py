import os
from collections import defaultdict
from pyairtable import Api
class AirtableDocumentDatabase:
    def __init__(self, token=None, base_id=None, table_id=None):
        if token is None:
            token = os.environ.get("AIRTABLE_TOKEN")
        if base_id is None:
            base_id = os.environ.get("AIRTABLE_BASE_ID")
        if table_id is None:
            table_id = os.environ.get("AIRTABLE_TABLE_ID")
        self.api = Api(token)
        self.table = self.api.table(base_id, table_id)
        self.documents = {}
        self.themes = defaultdict(list)
        self.tags = defaultdict(list)
        for row in self.table.all():
            document = row["fields"]
            self.documents[document["link"]] = document
            for theme in document.get("themes", []):
                self.themes[theme].append(document["link"])
            for tag in document.get("tags", []):
                self.tags[tag].append(document["link"])

    def get_all_documents(self):
        return list(self.documents.values())

    def get_all_tags(self):
        return list(self.tags.keys())

    def get_all_themes(self):
        return list(self.themes.keys())

    def get_documents_for_tag(self, tag):
        return [self.documents[link] for link in self.tags[tag]]

    def get_documents_for_theme(self, theme):
        return [self.documents[link] for link in self.themes[theme]]
