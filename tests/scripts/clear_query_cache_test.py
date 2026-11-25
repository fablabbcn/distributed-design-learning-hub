from ddlh.scripts import clear_query_cache


class TestClearQueryCache:

    def test_it_clears_the_query_cache(self, mocker, monkeypatch):
        """
        It clears the cache under REDIS_QUERY_CACHE_PREFIX and returns the
        number of deleted summaries
        """
        monkeypatch.setenv("REDIS_QUERY_CACHE_PREFIX", "queries")
        create_cache = mocker.patch.object(clear_query_cache, "create_cache")
        create_cache.return_value.clear.return_value = 7

        assert clear_query_cache.clear_query_cache() == 7
        create_cache.assert_called_once_with(prefix="queries")
