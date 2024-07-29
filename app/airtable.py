import json
import os
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, TypeVar, cast

import redis
from pyairtable import Api
from pyairtable.api.types import RecordDict


@dataclass
class AirtableConfig:
    token: str
    base_id: str
    table_ids: dict[str, str]
    view_ids: dict[str, str]


@dataclass
class RedisCacheConfig:
    redis_url: str
    prefix: str
    timeout: int


T = TypeVar("T")


class RedisCache:
    def __init__(self, config: RedisCacheConfig):
        self.config = config
        self.redis = redis.from_url(config.redis_url)

    def cached(
        self, prefix: str, args: list[str], func: Callable[..., T]
    ) -> T:
        key = self._get_key(prefix, args)
        cached_value = self.redis.get(key)
        if cached_value is not None:
            return cast(T, json.loads(cached_value))
        else:
            value = func(*args)
            self.redis.set(key, json.dumps(value))
            self.redis.expire(key, self.config.timeout)
            return value

    def _get_key(self, prefix: str, args: list[str]) -> str:
        return "_".join([self.config.prefix, prefix] + args)


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
            return self.api.table(self.config.base_id, table_id).all(
                view=self._view_id(table_name)
            )
        return []

    def _uncached_get(self, table_name: str, id: str) -> Optional[RecordDict]:
        table_id = self._table_id(table_name)
        if table_id:
            return self.api.table(self.config.base_id, table_id).get(id)
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
            "featured_documents": os.environ[
                "AIRTABLE_FEATURED_DOCUMENTS_TABLE_ID"
            ],
            "ui_strings": os.environ["AIRTABLE_UI_STRINGS_TABLE_ID"],
        },
        view_ids={
            "themes": os.environ["AIRTABLE_THEMES_VIEW_ID"],
            "featured_documents": os.environ[
                "AIRTABLE_FEATURED_DOCUMENTS_VIEW_ID"
            ],
        },
    )

    cache_config = RedisCacheConfig(
        redis_url=os.environ["REDIS_URL"],
        timeout=int(os.environ["REDIS_CACHE_TIMEOUT"]),
        prefix=os.environ["REDIS_CACHE_PREFIX"],
    )

    cache = RedisCache(cache_config)

    return AirtableDB(airtable_config, cache)
