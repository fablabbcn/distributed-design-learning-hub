import json
from unittest.mock import MagicMock, call

import pytest  # type: ignore

from ddlh.redis_cache import RedisCache, RedisCacheConfig


class TestRedisCache:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.redis = MagicMock()
        mocker.patch("ddlh.redis_cache.redis.from_url", return_value=self.redis)

    def make_cache(self, prefix="queries", timeout=None):
        return RedisCache(
            RedisCacheConfig(redis_url="redis://test", prefix=prefix, timeout=timeout)
        )

    def test_it_stores_values_with_the_timeout_as_expiry(self):
        """
        On a cache miss, it calls the function and stores the result with the
        configured timeout as the key's expiry
        """
        self.redis.get.return_value = None
        func = MagicMock(return_value={"answer": 42})
        cache = self.make_cache(timeout=3600)

        value = cache.cached("query", ["foo"], func)

        assert value == {"answer": 42}
        func.assert_called_once_with("foo")
        self.redis.set.assert_called_once_with(
            "queries_query_foo", json.dumps({"answer": 42}), ex=3600
        )

    def test_it_stores_values_without_expiry_when_there_is_no_timeout(self):
        """
        With no timeout configured, values are stored without an expiry
        """
        self.redis.get.return_value = None
        cache = self.make_cache(timeout=None)

        cache.cached("query", ["foo"], MagicMock(return_value="bar"))

        self.redis.set.assert_called_once_with(
            "queries_query_foo", json.dumps("bar"), ex=None
        )

    def test_it_returns_cached_values_without_calling_the_function(self):
        """
        On a cache hit, it returns the stored value and does not regenerate it
        """
        self.redis.get.return_value = json.dumps("cached")
        func = MagicMock()
        cache = self.make_cache(timeout=3600)

        assert cache.cached("query", ["foo"], func) == "cached"
        func.assert_not_called()
        self.redis.set.assert_not_called()

    def test_clear_deletes_only_keys_under_the_prefix(self):
        """
        It scans for keys under its own prefix and deletes them, returning the
        number deleted
        """
        keys = [b"queries_query_a", b"queries_query_b"]
        self.redis.scan_iter.return_value = iter(keys)
        self.redis.delete.return_value = 2
        cache = self.make_cache()

        assert cache.clear() == 2
        self.redis.scan_iter.assert_called_once_with(match="queries_*", count=500)
        self.redis.delete.assert_called_once_with(*keys)

    def test_clear_deletes_in_batches(self, mocker):
        """
        It deletes keys in batches, rather than all at once
        """
        mocker.patch("ddlh.redis_cache.CLEAR_BATCH_SIZE", 2)
        self.redis.scan_iter.return_value = iter([b"q_1", b"q_2", b"q_3"])
        self.redis.delete.side_effect = [2, 1]
        cache = self.make_cache(prefix="q")

        assert cache.clear() == 3
        assert self.redis.delete.call_args_list == [
            call(b"q_1", b"q_2"),
            call(b"q_3"),
        ]

    def test_clear_does_nothing_when_the_cache_is_empty(self):
        """
        It does not call delete when there are no keys to delete
        """
        self.redis.scan_iter.return_value = iter([])
        cache = self.make_cache()

        assert cache.clear() == 0
        self.redis.delete.assert_not_called()

    def test_clear_escapes_glob_characters_in_the_prefix(self):
        """
        Glob metacharacters in the prefix are matched literally
        """
        self.redis.scan_iter.return_value = iter([])
        cache = self.make_cache(prefix="q*[1]?")

        cache.clear()

        self.redis.scan_iter.assert_called_once_with(
            match="q\\*\\[1\\]\\?_*", count=500
        )

    def test_clear_refuses_an_empty_prefix(self):
        """
        It refuses to clear when the prefix is empty, as that would match
        unrelated keys (e.g. Celery's) in the same Redis database
        """
        cache = self.make_cache(prefix="")

        with pytest.raises(ValueError):
            cache.clear()
        self.redis.scan_iter.assert_not_called()
