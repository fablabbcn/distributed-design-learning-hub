from unittest.mock import MagicMock

import pytest  # type: ignore
from llama_index.core.base.response.schema import Response

from ddlh import rag
from ddlh.models import DocumentSummary
from ddlh.rag import (
    DEFAULT_QUERY_CACHE_TIMEOUT,
    DOCUMENT_SUMMARY_PROMPT,
    TOP_SENTENCE_PROMPT,
    RAGIndex,
    get_query_cache_timeout,
)


class TestPrompts:

    @pytest.mark.parametrize("prompt", [DOCUMENT_SUMMARY_PROMPT, TOP_SENTENCE_PROMPT])
    def test_prompts_contain_no_model_specific_markers(self, prompt):
        """
        Prompts are plain text, without Mixtral-style instruction markers
        """
        for marker in ["<s>", "</s>", "[INST]", "[/INST]"]:
            assert marker not in prompt

    @pytest.mark.parametrize("prompt", [DOCUMENT_SUMMARY_PROMPT, TOP_SENTENCE_PROMPT])
    def test_prompts_include_the_query(self, prompt):
        """
        The query is interpolated into the prompt, quoted
        """
        formatted = prompt.format(query="circular design")
        assert '"circular design"' in formatted
        assert "{" not in formatted

    def test_document_summary_prompt_asks_for_the_irrelevance_sentinel(self):
        """
        The prompt asks for the phrase that marks a document as irrelevant
        """
        assert '"This document is irrelevant"' in DOCUMENT_SUMMARY_PROMPT


class TestRAGIndex:

    def setup_method(self, method):
        self.llamaindex = MagicMock()
        self.rag_index = RAGIndex(
            llamaindex=self.llamaindex,
            document_repository=MagicMock(),
            cache=MagicMock(),
            max_document_summaries=3,
        )

    def doc(self, doc_id):
        return {"doc_id": doc_id, "score": 1.0, "results": []}

    @pytest.mark.parametrize(
        "response,expected",
        [
            ("This document explores repair.", "explores repair."),
            ("this document explores repair.", "explores repair."),
            ("The document explores repair.", "explores repair."),
            ("  This document explores repair.", "explores repair."),
            ("Explores repair.", "Explores repair."),
            (
                "The documentation explores repair.",
                "The documentation explores repair.",
            ),
        ],
    )
    def test_it_strips_the_document_prefix_from_summaries(self, response, expected):
        """
        The leading "This document" is removed, as summaries are shown after
        the document's title
        """
        summary = self.rag_index._make_summary(
            Response(response="Top sentence."),
            [(self.doc("doc1"), Response(response=response))],
        )
        assert summary.top_sentence == "Top sentence."
        assert summary.document_summaries == [
            DocumentSummary(document="doc1", summary=expected)
        ]

    def test_it_skips_documents_the_model_marks_as_irrelevant(self):
        """
        Documents summarised as irrelevant are dropped from the summaries
        """
        self.llamaindex.synthesize.side_effect = [
            Response(response="This document is irrelevant."),
            Response(response="This document explores repair."),
        ]
        docs = [self.doc("doc1"), self.doc("doc2")]

        responses = self.rag_index._generate_document_summaries(docs, "repair")

        assert [d["doc_id"] for (d, _r) in responses] == ["doc2"]
        prompt = self.llamaindex.synthesize.call_args_list[0].args[0]
        assert prompt == DOCUMENT_SUMMARY_PROMPT.format(query="repair")

    def test_it_stops_after_the_maximum_number_of_summaries(self):
        """
        No more than max_document_summaries documents are summarised
        """
        self.llamaindex.synthesize.return_value = Response(
            response="This document explores repair."
        )
        docs = [self.doc(f"doc{i}") for i in range(5)]

        responses = self.rag_index._generate_document_summaries(docs, "repair")

        assert len(responses) == 3
        assert self.llamaindex.synthesize.call_count == 3


class TestQueryCacheTimeout:

    def test_it_defaults_to_the_default_timeout(self, monkeypatch):
        """
        Without REDIS_QUERY_CACHE_TIMEOUT, summaries expire after the default
        """
        monkeypatch.delenv("REDIS_QUERY_CACHE_TIMEOUT", raising=False)
        assert get_query_cache_timeout() == DEFAULT_QUERY_CACHE_TIMEOUT
        assert 30 * 86400 <= DEFAULT_QUERY_CACHE_TIMEOUT <= 90 * 86400

    def test_it_treats_an_empty_value_as_the_default(self, monkeypatch):
        """
        An empty REDIS_QUERY_CACHE_TIMEOUT also uses the default
        """
        monkeypatch.setenv("REDIS_QUERY_CACHE_TIMEOUT", "")
        assert get_query_cache_timeout() == DEFAULT_QUERY_CACHE_TIMEOUT

    def test_it_reads_the_timeout_from_the_environment(self, monkeypatch):
        """
        REDIS_QUERY_CACHE_TIMEOUT sets the expiry in seconds
        """
        monkeypatch.setenv("REDIS_QUERY_CACHE_TIMEOUT", "86400")
        assert get_query_cache_timeout() == 86400

    def test_zero_disables_expiry(self, monkeypatch):
        """
        A timeout of 0 means cached summaries never expire
        """
        monkeypatch.setenv("REDIS_QUERY_CACHE_TIMEOUT", "0")
        assert get_query_cache_timeout() is None

    def test_the_rag_index_cache_uses_the_timeout(self, mocker, monkeypatch):
        """
        The RAG index's query cache is created with the configured timeout
        """
        monkeypatch.setenv("REDIS_QUERY_CACHE_PREFIX", "queries")
        monkeypatch.setenv("REDIS_QUERY_CACHE_TIMEOUT", "1234")
        monkeypatch.setenv("RETRIEVAL_MAX_DOCUMENT_SUMMARIES", "3")
        mocker.patch.object(rag, "get_llamaindex_instance")
        create_cache = mocker.patch.object(rag, "create_cache")

        rag.get_rag_index_instance(MagicMock())

        create_cache.assert_called_once_with(prefix="queries", timeout=1234)
