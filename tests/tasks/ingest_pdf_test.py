from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from ddlh.tasks import ingest_pdf


class TestIngestPDF:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.environ = mocker.patch("ddlh.tasks.environ")
        self.environ.__getitem__.return_value = self.user_agent
        self.store_task = mocker.patch("ddlh.tasks.store")
        self.requests = mocker.patch("ddlh.tasks.requests")
        self.requests.utils.default_headers.return_value = {}
        self.bytes_io_constructor = mocker.patch("ddlh.tasks.BytesIO")
        self.bytes_io_constructor.return_value = self.bytes_io
        self.pdf_reader_constructor = mocker.patch("ddlh.tasks.PdfReader")
        self.pdf_reader_constructor.return_value = self.pdf_reader
        self.requests.get.return_value = self.response

    def setup_method(self, method):
        self.url = "http://example.com"
        self.response_content = "this is the response content"
        self.user_agent = "this-is/the-USER-AGENT"
        self.page_texts = [
            "the text of page 1",
            "the text of page 2",
        ]
        self.pages = []
        for page_text in self.page_texts:
            page = MagicMock()
            page.extract_text.return_value = page_text
            self.pages.append(page)
        self.response = MagicMock()
        self.response.content = self.response_content
        self.bytes_io = MagicMock()
        self.pdf_reader = MagicMock()
        self.pdf_reader.pages = self.pages

    def test_http_get_request(self):
        """
        It makes an http get request for the url
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.requests.get.assert_called_with(self.url, headers=ANY)

    def test_http_user_agent(self, mocker):
        """
        It provides an appropriate user_agent string when requesting
        """
        ingest_pdf.apply(args=(self.url,)).get()
        headers = self.requests.get.call_args.kwargs["headers"]
        assert headers["User-Agent"] == self.user_agent

    def test_it_raises_on_http_errors(self):
        """
        It raises an error on HTTP errors so that celery
        can retry the task
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.response.raise_for_status.assert_called()

    def test_it_reads_the_response_as_a_pdf(self):
        """
        It converts the request content to a BytesIO,
        then passes that to the PdfReader.
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.bytes_io_constructor.assert_called_with(self.response_content)
        self.pdf_reader_constructor.assert_called_with(self.bytes_io)

    def test_it_extracts_the_text_of_each_page_of_the_pdf(self):
        """
        It extracts the text from each page of the PDF
        """
        ingest_pdf.apply(args=(self.url,)).get()
        for page in self.pages:
            page.extract_text.assert_called()

    def test_it_calls_store_task_with_url_and_content(self):
        """
        It queues a store task with the url and
        the extracted content of all the pages
        """
        ingest_pdf.apply(args=(self.url,)).get()
        self.store_task.delay.assert_called_with(
            self.url, "\n\n".join(self.page_texts)
        )
