import json
import os
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, cast

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

    def cached(self, prefix: str, args: list[str], func: Callable[..., T]) -> T:
        key = self._get_key(prefix, args)
        cached_value = self.redis.get(key)
        if cached_value is not None:
            return cast(T, json.loads(cached_value))
        else:
            value = func(*args)
            self.redis.set(key, json.dumps(value))
            if self.config.timeout is not None:
                self.redis.expire(key, self.config.timeout)
            return value

    def _get_key(self, prefix: str, args: list[str]) -> str:
        return "_".join([self.config.prefix, prefix] + args)


def create_cache(prefix: str, timeout: Optional[int] = None) -> RedisCache:
    config = RedisCacheConfig(
        redis_url=os.environ["REDIS_URL"], prefix=prefix, timeout=timeout
    )
    return RedisCache(config)
