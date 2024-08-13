import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

import redis


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
            self.redis.set(key, json_value)
            if self.config.timeout is not None:
                self.redis.expire(key, self.config.timeout)
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

    def _get_key(self, prefix: str, args: list[str]) -> str:
        return "_".join([self.config.prefix, prefix] + args)


def create_cache(prefix: str, timeout: Optional[int] = None) -> RedisCache:
    config = RedisCacheConfig(
        redis_url=os.environ["REDIS_URL"], prefix=prefix, timeout=timeout
    )
    return RedisCache(config)
