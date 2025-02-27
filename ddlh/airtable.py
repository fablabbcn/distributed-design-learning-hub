import os
from dataclasses import dataclass
from time import sleep
from typing import Optional, Sequence

from pyairtable import Api
from pyairtable.api.types import RecordDict

from ddlh.redis_cache import RedisCache, create_cache

# Maximum 5 requests per second per base:
# see https://airtable.com/developers/web/api/rate-limits
REQUEST_TIMEOUT = 1 / 5.0


@dataclass
class AirtableConfig:
    token: str
    base_id: str
    table_ids: dict[str, str]
    view_ids: dict[str, str]


class AirtableDB:
    def __init__(self, config: AirtableConfig, cache: RedisCache):
        self.config = config
        self.cache = cache
        self.api = Api(config.token)

    def all(self, table_name: str) -> Sequence[RecordDict]:
        return self.cache.cached("all", [table_name], self._uncached_all)

    def get(self, table_name: str, id: str) -> Optional[RecordDict]:
        return self.cache.cached("get", [table_name, id], self._uncached_get)

    def _uncached_all(self, table_name: str) -> Sequence[RecordDict]:
        table_id = self._table_id(table_name)
        if table_id:
            result = self.api.table(self.config.base_id, table_id).all(
                view=self._view_id(table_name)
            )
            sleep(REQUEST_TIMEOUT)
            return result
        return []

    def _uncached_get(self, table_name: str, id: str) -> Optional[RecordDict]:
        table_id = self._table_id(table_name)
        if table_id:
            result = self.api.table(self.config.base_id, table_id).get(id)
            sleep(REQUEST_TIMEOUT)
            return result
        return None

    def _table_id(self, table_name: str) -> Optional[str]:
        return self.config.table_ids.get(table_name)

    def _view_id(self, table_name: str) -> Optional[str]:
        return self.config.view_ids.get(table_name)


def get_db_instance() -> AirtableDB:
    airtable_config = AirtableConfig(
        token=os.environ["AIRTABLE_TOKEN"],
        base_id=os.environ["AIRTABLE_BASE_ID"],
        table_ids={
            "documents": os.environ["AIRTABLE_DOCUMENTS_TABLE_ID"],
            "themes": os.environ["AIRTABLE_THEMES_TABLE_ID"],
            "formats": os.environ["AIRTABLE_FORMATS_TABLE_ID"],
            "featured_documents": os.environ["AIRTABLE_FEATURED_DOCUMENTS_TABLE_ID"],
        },
        view_ids={
            "themes": os.environ["AIRTABLE_THEMES_VIEW_ID"],
            "featured_documents": os.environ["AIRTABLE_FEATURED_DOCUMENTS_VIEW_ID"],
        },
    )

    cache = create_cache(
        prefix=os.environ["REDIS_DOCUMENT_CACHE_PREFIX"],
        timeout=int(os.environ["REDIS_DOCUMENT_CACHE_TIMEOUT"]),
    )

    return AirtableDB(airtable_config, cache)
