from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from app.celery import ingest_html


class TestIngestHTML:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.store_task = mocker.patch("app.celery.store")
        self.extractor_constructor = mocker.patch("app.celery.CanolaExtractor")
        self.extractor_constructor.return_value = self.extractor
        self.requests = mocker.patch("app.celery.requests")
        self.requests.get.return_value = self.response

    def setup_method(self, method):
        self.url = "http://example.com"
        self.response_text = "<p>this is the response_text</p>"
        self.extracted_text = "this is the extracted text"
        self.response = MagicMock()
        self.response.text = self.response_text
        self.extractor = MagicMock()
        self.extractor.get_content.return_value = self.extracted_text

    def test_http_get_request(self):
        """
        It makes an http get request for the url
        """
        ingest_html.apply(args=(self.url,)).get()
        self.requests.get.assert_called_with(self.url, headers=ANY)

    def test_http_user_agent(self, mocker):
        """
        It provides an appropriate user_agent string when requesting
        """
        ingest_html.apply(args=(self.url,)).get()
        headers = self.requests.get.call_args.kwargs["headers"]
        assert headers["User-Agent"] == "FablabBCN-DDLH-indexer/0.0.0"

    def test_it_raises_on_http_errors(self):
        """
        It raises an error on HTTP errors so that celery
        can retry the task
        """
        ingest_html.apply(args=(self.url,)).get()
        self.response.raise_for_status.assert_called()

    def test_it_extracts_content_with_boilerpipe(self):
        """
        It uses the boilerpipe CanolaExtractor to extract the
        text content of the page
        """
        ingest_html.apply(args=(self.url,)).get()
        self.extractor_constructor.assert_called()
        self.extractor.get_content.assert_called_with(self.response_text)

    def test_it_calls_store_task_with_url_and_content(self):
        """
        It queues a store task with the url and
        the extracted content
        """
        ingest_html.apply(args=(self.url,)).get()
        self.store_task.delay.assert_called_with(self.url, self.extracted_text)
