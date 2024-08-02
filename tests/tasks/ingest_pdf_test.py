from unittest.mock import MagicMock

import pytest  # type: ignore

from ddlh.tasks import ingest_pdf


class TestIngestPDF:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.fetcher = mocker.patch("ddlh.tasks.get")
        self.extractor = mocker.patch("ddlh.tasks.extract_pdf")
        self.store_task = mocker.patch("ddlh.tasks.store")
        self.fetcher.return_value = self.response
        self.extractor.return_value = self.extracted_text

    def setup_method(self, method):
        self.url = "http://example.com"
        self.response_content = "this is the raw response content"
        self.extracted_text = "this is the extracted text"
        self.response = MagicMock()
        self.response.content = self.response_content

    def test_http_get_request(self):
        """
        It makes an http get request for the url
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.fetcher.assert_called_with(self.url)

    def test_it_extracts_content(self):
        """
        It calls the html extractor with the raw response html
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.extractor.assert_called_with(self.response_content)

    def test_it_calls_store_task_with_url_and_content(self):
        """
        It queues a store task with the url and
        the extracted content
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.store_task.delay.assert_called_with(self.url, self.extracted_text)
