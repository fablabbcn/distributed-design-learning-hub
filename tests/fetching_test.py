from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from ddlh.fetching import content_type, get


class TestFetchingContentType:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.environ = mocker.patch("ddlh.fetching.environ")
        self.requests_head = mocker.patch("ddlh.fetching.requests.head")
        self.default_headers_func = mocker.patch(
            "ddlh.fetching.requests.utils.default_headers"
        )
        self.environ.__getitem__.return_value = self.user_agent
        self.requests_head.return_value = self.response
        self.default_headers_func.return_value = self.default_request_headers

    def setup_method(self, method):
        self.user_agent = "The/UserAgent-0.0;charset=UTF-8"
        self.url = "https://example.com"
        self.content_type = "text/html"
        self.response = MagicMock()
        self.response.headers = {"Content-Type": self.content_type}
        self.default_request_headers = {"Accept": "*"}

    def test_gets_user_agent_from_environment(self):
        """
        It fetches the user-agent from the environment
        """
        content_type(self.url)
        self.environ.__getitem__.assert_called_with("FETCHER_USER_AGENT")

    def test_http_head_request(self):
        """
        It does an http head request for the specified URL,
        """
        content_type(self.url)
        self.requests_head.assert_called_with(self.url, headers=ANY)

    def test_it_raises_on_http_errors(self):
        """
        It raises an error on HTTP errors so that celery
        can retry the task
        """
        content_type(self.url)
        self.response.raise_for_status.assert_called()

    def test_http_user_agent(self):
        """
        It provides an appropriate user_agent string when requesting,
        ignoring charset info
        """
        content_type(self.url)
        headers = self.requests_head.call_args.kwargs["headers"]
        assert headers["User-Agent"] == self.user_agent

    def test_other_http_headers(self):
        """
        It includes default headers from requests
        """
        content_type(self.url)
        headers = self.requests_head.call_args.kwargs["headers"]
        self.default_headers_func.assert_called()
        assert self.default_request_headers.items() <= headers.items()

    def test_return_value(self):
        """
        It returns the content type
        """
        result = content_type(self.url)
        assert result == self.content_type


class TestFetchingGet:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.environ = mocker.patch("ddlh.fetching.environ")
        self.requests_get = mocker.patch("ddlh.fetching.requests.get")
        self.default_headers_func = mocker.patch(
            "ddlh.fetching.requests.utils.default_headers"
        )
        self.environ.__getitem__.return_value = self.user_agent
        self.requests_get.return_value = self.response
        self.default_headers_func.return_value = self.default_request_headers

    def setup_method(self, method):
        self.user_agent = "The/UserAgent-0.0;charset=UTF-8"
        self.url = "https://example.com"
        self.response = MagicMock()
        self.default_request_headers = {"Accept": "*"}

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
