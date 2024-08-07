from unittest.mock import MagicMock

import pytest  # type: ignore

from ddlh.tasks import index


class TestIndex:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.index_documents = mocker.patch("ddlh.tasks.index_documents")
        self.documents = MagicMock()

    def test_it_indexes_the_documents(self):
        """
        It passes the documents to the RAG indexer
        """
        index.apply(args=(self.documents,)).get()
        self.index_documents.assert_called_with(self.documents)
