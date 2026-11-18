import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

import more_itertools as mit
import redis

CLEAR_BATCH_SIZE = 500


def _escape_glob(value: str) -> str:
    """Escape Redis glob-style pattern metacharacters."""
    return re.sub(r"([*?\[\]\\])", r"\\\1", value)


@dataclass
class RedisCacheConfig:
    redis_url: str
    prefix: str
    timeout: Optional[int]


T = TypeVar("T")


class RedisCache:
    def __init__(self, config: RedisCacheConfig):
        self.config = config
        self.redis = redis.from_url(config.redis_url)

    def cached(
        self,
        prefix: str,
        args: list[str],
        func: Callable[..., T],
        serializer: Optional[Callable[[T], dict[str, Any]]] = None,
        deserializer: Optional[Callable[[dict[str, Any]], T]] = None,
    ) -> T:
        key = self._get_key(prefix, args)
        cached_value = self.get_if_cached(prefix, args, deserializer)
        if cached_value is not None:
            return cached_value
        else:
            value = func(*args)
            if serializer:
                serialized_value = serializer(value)
                json_value = json.dumps(serialized_value)
            else:
                json_value = json.dumps(value)
            self.redis.set(key, json_value, ex=self.config.timeout)
            return value

    def get_if_cached(
        self,
        prefix: str,
        args: list[str],
        deserializer: Optional[Callable[[dict[str, Any]], T]] = None,
    ) -> Optional[T]:
        key = self._get_key(prefix, args)
        cached_value = self.redis.get(key)
        if cached_value is not None:
            json_value = json.loads(cached_value)
            if deserializer:
                deserialized = deserializer(json_value)
            else:
                deserialized = json_value
            return deserialized
        else:
            return None

    def clear(self) -> int:
        """
        Delete every key matching "<prefix>_*" and return how many were
        deleted. Other data sharing the Redis database (e.g. the Celery
        broker, or the Airtable cache) is left untouched.
        """
        if not self.config.prefix:
            raise ValueError("Refusing to clear a cache with an empty prefix")
        pattern = f"{_escape_glob(self.config.prefix)}_*"
        deleted = 0
        keys = self.redis.scan_iter(match=pattern, count=CLEAR_BATCH_SIZE)
        for batch in mit.chunked(keys, CLEAR_BATCH_SIZE):
            deleted += self.redis.delete(*batch)
        return deleted

    def _get_key(self, prefix: str, args: list[str]) -> str:
        return "_".join([self.config.prefix, prefix] + args)


def create_cache(prefix: str, timeout: Optional[int] = None) -> RedisCache:
    config = RedisCacheConfig(
        redis_url=os.environ["REDIS_URL"], prefix=prefix, timeout=timeout
    )
    return RedisCache(config)
