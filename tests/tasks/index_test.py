from unittest.mock import MagicMock

import pytest  # type: ignore

from ddlh.tasks import index


class TestIndex:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.rag_index = MagicMock()
        self.rag = mocker.patch("ddlh.tasks.rag.get_rag_index_instance")
        self.rag.return_value = self.rag_index
        self.documents = MagicMock()

    def test_it_indexes_the_documents(self):
        """
        It passes the documents to the RAG indexer
        """
        index.apply(args=(self.documents,)).get()
        self.rag_index.index_documents.assert_called_with(self.documents)
