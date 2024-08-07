from unittest.mock import MagicMock

import pytest  # type: ignore

from ddlh.tasks import fetch


class TestFetch:

    @pytest.fixture(autouse=True, params=["text/html", "application/pdf"])
    def setup_mocks(self, request, mocker):
        self.content_type = request.param
        self.url = "http://example.com"

        self.document = MagicMock()
        self.text = MagicMock()
        self.enriched_document = MagicMock()
        self.response = MagicMock()

        self.extract_html = mocker.patch("ddlh.tasks.extract_html")
        self.extract_pdf = mocker.patch("ddlh.tasks.extract_pdf")
        self.content_type_function = mocker.patch("ddlh.tasks.content_type")
        self.get = mocker.patch("ddlh.tasks.get")

        self.document.link = self.url
        self.document.enrich_with_text.return_value = self.enriched_document
        self.get.return_value = self.response
        self.extract_pdf.return_value = self.text
        self.extract_html.return_value = self.text
        self.content_type_function.return_value = self.content_type

    def test_it_gets_the_url(self):
        fetch.apply(args=(self.document,)).get()
        self.get.assert_called_with(self.url)

    def test_it_parses_the_content_type(self):
        """
        It parses the content type of the response
        """
        fetch.apply(args=(self.document,)).get()
        self.content_type_function.assert_called_with(self.response)

    def test_dispatch_on_content_type(self):
        """
        it calls the appropriate ingestor, passing the appropriate
        representation of the response
        """
        fetch.apply(args=(self.document,)).get()

        if self.content_type == "text/html":
            self.extract_html.assert_called_with(self.response.text)
        elif self.content_type == "application/pdf":
            self.extract_pdf.assert_called_with(self.response.content)

    def test_it_enriches_the_document(self):
        """
        It enriches the document with the extracted text
        """
        fetch.apply(args=(self.document,)).get()
        self.document.enrich_with_text.assert_called_with(self.text)

    def test_it_returns_the_enriched_document(self):
        """
        It returns the enriched document
        """
        response = fetch.apply(args=(self.document,)).get()
        assert response == self.enriched_document
