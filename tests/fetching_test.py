from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from ddlh.fetching import content_type, get


class TestParsingContentType:

    def setup_method(self, method):
        self.url = "https://example.com"
        self.content_type = "text/html;charset=utf-8"
        self.response = MagicMock()
        self.response.headers = {"Content-Type": self.content_type}

    def test_return_value(self):
        """
        It returns the content type, stripping charset info
        """
        result = content_type(self.response)
        assert result == "text/html"


class TestFetchingGet:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.user_agent = "The/UserAgent-0.0;charset=UTF-8"
        self.url = "https://example.com"
        self.default_request_headers = {"Accept": "*"}

        self.response = MagicMock()

        self.environ = mocker.patch("ddlh.fetching.environ")
        self.requests_get = mocker.patch("ddlh.fetching.requests.get")
        self.default_headers_func = mocker.patch(
            "ddlh.fetching.requests.utils.default_headers"
        )

        self.environ.__getitem__.return_value = self.user_agent
        self.requests_get.return_value = self.response
        self.default_headers_func.return_value = self.default_request_headers

    def test_gets_user_agent_from_environment(self):
        """
        It fetches the user-agent from the environment
        """
        get(self.url)
        self.environ.__getitem__.assert_called_with("FETCHER_USER_AGENT")

    def test_http_get_request(self):
        """
        It does an http get request for the specified URL,
        """
        get(self.url)
        self.requests_get.assert_called_with(self.url, headers=ANY)

    def test_it_raises_on_http_errors(self):
        """
        It raises an error on HTTP errors so that celery
        can retry the task
        """
        get(self.url)
        self.response.raise_for_status.assert_called()

    def test_http_user_agent(self):
        """
        It provides an appropriate user_agent string when requesting,
        ignoring charset info
        """
        get(self.url)
        headers = self.requests_get.call_args.kwargs["headers"]
        assert headers["User-Agent"] == self.user_agent

    def test_other_http_headers(self):
        """
        It includes default headers from requests
        """
        get(self.url)
        headers = self.requests_get.call_args.kwargs["headers"]
        self.default_headers_func.assert_called()
        assert self.default_request_headers.items() <= headers.items()

    def test_return_value(self):
        """
        It returns the response
        """
        result = get(self.url)
        assert result == self.response
