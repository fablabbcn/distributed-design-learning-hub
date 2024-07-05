from unittest.mock import ANY, MagicMock

import pytest  # type: ignore

from app.celery import store


class TestIngestPDF:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.elasticsearch_constructor = mocker.patch(
            "app.celery.Elasticsearch"
        )
        self.elasticsearch_constructor.return_value = self.elasticsearch_client
        self.url_to_id = mocker.patch("app.celery.url_to_id")
        self.url_to_id.return_value = self.id

    def setup_method(self, method):
        self.elasticsearch_client = MagicMock()
        self.url = "https://www.example.com"
        self.text = "This is the extracted text"
        self.id = "This is the generated id"

    def test_it_creates_an_elasticsearch_client(self):
        """
        It instantiates an elasticsearch client to store
        the document.
        """

        # TODO: Extract the URL out into an env var and
        # test that its passed
        store.apply(args=(self.url, self.text)).get()
        self.elasticsearch_constructor.assert_called()

    def test_it_generates_an_id_from_the_url(self):
        """
        It generates a deterministic ID from the url
        of the document
        """
        store.apply(args=(self.url, self.text)).get()
        self.url_to_id.assert_called_with(self.url)

    def test_it_indexes_the_document(self):
        """
        It indexes the document in elasticsearch
        """
        # TODO: Extract the index name out into an env var and
        # test that its passed
        store.apply(args=(self.url, self.text)).get()
        self.elasticsearch_client.index.assert_called_with(
            index=ANY,
            id=self.id,
            document={"url": self.url, "text": self.text},
        )
