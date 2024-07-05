from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from app.celery import dispatch


class TestDispatch:
    @pytest.fixture(autouse=True, params=["text/html", "application/pdf"])
    def setup_content_type(self, request):
        self.set_content_type(request.param)

    def set_content_type(self, content_type):
        self.content_type = content_type
        self.response.headers = {"Content-Type": self.content_type}

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.ingest_html_task = mocker.patch("app.celery.ingest_html")
        self.ingest_pdf_task = mocker.patch("app.celery.ingest_pdf")
        self.requests = mocker.patch("app.celery.requests")
        self.requests.head.return_value = self.response

    def setup_method(self, method):
        self.url = "http://example.com"
        self.response = MagicMock()

    def test_http_head_request(self, mocker):
        """
        It does an http head request for the specified URL,
        """
        dispatch.apply(args=(self.url,)).get()
        self.requests.head.assert_called_with(self.url, headers=ANY)

    def test_http_user_agent(self, mocker):
        """
        It provides an appropriate user_agent string when requesting
        """
        dispatch.apply(args=(self.url,)).get()
        headers = self.requests.head.call_args.kwargs["headers"]
        assert headers["User-Agent"] == "FablabBCN-DDLH-indexer/0.0.0"

    def test_dispatch_on_content_type(self, mocker):
        """
        It queues the appropriate ingestor task, passing the url
        """
        dispatch.apply(args=(self.url,)).get()
        if self.content_type == "text/html":
            self.ingest_html_task.delay.assert_called_with(self.url)
        elif self.content_type == "application/pdf":
            self.ingest_pdf_task.delay.assert_called_with(self.url)

    def test_it_ignores_charset_info_when_dispatching(self, mocker):
        """
        If the response content type specifies a charset, it is ignored
        for the purposes of identifying the correct dispatcher
        """
        original_content_type = self.content_type
        self.set_content_type(f"{original_content_type};charset=UTF-8")
        dispatch.apply(args=(self.url,)).get()
        if original_content_type == "text/html":
            self.ingest_html_task.delay.assert_called_with(self.url)
        elif original_content_type == "application/pdf":
            self.ingest_pdf_task.delay.assert_called_with(self.url)
