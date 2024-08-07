from unittest.mock import MagicMock

import pytest  # type: ignore

from ddlh.extraction import extract_html, extract_pdf


class TestExtractHTML:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.raw_html = "<p>This is the raw html</p>"
        self.extracted_text = "This is the extracted text"
        self.extractor = MagicMock()

        self.extractor_constructor = mocker.patch("ddlh.extraction.CanolaExtractor")

        self.extractor_constructor.return_value = self.extractor
        self.extractor.get_content.return_value = self.extracted_text

    def test_boilerpipe_called(self):
        """
        It uses the Boilerpipe CanolaExtractor to extract the text
        """
        extract_html(self.raw_html)
        self.extractor_constructor.assert_called()
        self.extractor.get_content.assert_called_with(self.raw_html)

    def test_it_returns_the_extracted_text(self):
        """
        It returns the extracted text
        """
        result = extract_html(self.raw_html)
        assert result == self.extracted_text


class TestExtractPDF:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.page_texts = [
            "the text of page 1",
            "the text of page 2",
        ]

        self.pages = []
        for page_text in self.page_texts:
            page = MagicMock()
            page.extract_text.return_value = page_text
            self.pages.append(page)

        self.bytes_io = MagicMock()
        self.pdf_reader = MagicMock()
        self.response_content = MagicMock()

        self.bytes_io_constructor = mocker.patch("ddlh.extraction.BytesIO")
        self.pdf_reader_constructor = mocker.patch("ddlh.extraction.PdfReader")

        self.pdf_reader.pages = self.pages
        self.bytes_io_constructor.return_value = self.bytes_io
        self.pdf_reader_constructor.return_value = self.pdf_reader

    def test_it_reads_the_response_as_a_pdf(self):
        """
        It converts the request content to a BytesIO,
        then passes that to the PdfReader.
        """
        extract_pdf(self.response_content)
        self.bytes_io_constructor.assert_called_with(self.response_content)
        self.pdf_reader_constructor.assert_called_with(self.bytes_io)

    def test_it_extracts_the_text_of_each_page_of_the_pdf(self):
        """
        It extracts the text from each page of the PDF
        """
        extract_pdf(self.response_content)
        for page in self.pages:
            page.extract_text.assert_called()

    def test_it_calls_store_task_with_url_and_content(self):
        """
        It queues a store task with the url and
        the extracted content of all the pages
        """
        result = extract_pdf(self.response_content)
        assert result == "\n\n".join(self.page_texts)
