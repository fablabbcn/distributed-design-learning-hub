from unittest.mock import MagicMock

import pytest  # type: ignore
from flask import Flask

from ddlh.tasks import index


class TestIndex:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.flask = Flask("test")
        self.rag_index = MagicMock()
        self.flask.config["rag_index"] = self.rag_index
        self.documents = MagicMock()

    def test_it_indexes_the_documents(self):
        """
        It passes the documents to the RAG indexer
        """
        with self.flask.app_context():
            index.apply(args=(self.documents,)).get()
            self.rag_index.index_documents.assert_called_with(self.documents)
