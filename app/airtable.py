import os
from dataclasses import dataclass
from typing import Optional, Sequence

from pyairtable import Api
from pyairtable.api.types import RecordDict


@dataclass
class AirtableConfig:
    token: str
    base_id: str
    table_ids: dict[str, str]


class AirtableDB:
    def __init__(self, airtable_config: AirtableConfig):
        self.airtable_config = airtable_config
        self.api = Api(airtable_config.token)

    def all(self, table_name: str) -> Sequence[RecordDict]:
        table_id = self._table_id(table_name)
        if table_id:
            return self.api.table(self.airtable_config.base_id, table_id).all()
        return []

    def get(self, table_name: str, id: str) -> Optional[RecordDict]:
        table_id = self._table_id(table_name)
        if table_id:
            return self.api.table(self.airtable_config.base_id, table_id).get(
                id
            )
        return None

    def _table_id(self, table_name: str) -> Optional[str]:
        return self.airtable_config.table_ids.get(table_name)


def get_db_instance() -> AirtableDB:
    airtable_config = AirtableConfig(
        token=os.environ["AIRTABLE_TOKEN"],
        base_id=os.environ["AIRTABLE_BASE_ID"],
        table_ids={
            "documents": os.environ["AIRTABLE_DOCUMENTS_TABLE_ID"],
            "themes": os.environ["AIRTABLE_THEMES_TABLE_ID"],
            "formats": os.environ["AIRTABLE_FORMATS_TABLE_ID"],
            "featured_documents": os.environ[
                "AIRTABLE_FEATURED_DOCUMENTS_TABLE_ID"
            ],
            "ui_strings": os.environ["AIRTABLE_UI_STRINGS_TABLE_ID"],
        },
    )
    return AirtableDB(airtable_config)
