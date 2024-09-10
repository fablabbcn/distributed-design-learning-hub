import re
from collections import defaultdict
from os import environ
from typing import List, Optional, TypedDict

from ddlh import airtable
from ddlh.models import (
    Document,
    DocumentSummary,
    DocumentWithText,
    SearchResult,
    Summary,
)
from ddlh.rag.llamaindex import (
    GenerationResult,
    LlamaIndex,
    RetrievalResult,
    get_llamaindex_instance,
)
from ddlh.redis_cache import RedisCache, create_cache
from ddlh.repositories import DocumentsRepository
from ddlh.utils import compact

DOCUMENT_SUMMARY_PROMPT: str = """
<s>[INST]explain in one sentence how this document relates to the theme of \"{query}\".
 If the document does not contain information about the theme of \"{query}\",
 return \"This document is irrelevant\".[/INST]This document </s>
"""

TOP_SENTENCE_PROMPT: str = """
<s>[INST]Provide a one or two sentence description of \"{query}\"
 based on the information given.[/INST] {query}</s>
"""

DocumentResult = TypedDict(
    "DocumentResult",
    {
        "doc_id": str,
        "score": float,
        "results": List[RetrievalResult],
    },
)


class RAGIndex:
    def __init__(
        self,
        llamaindex: LlamaIndex,
        document_repository: DocumentsRepository,
        cache: RedisCache,
        max_document_summaries: int,
    ):
        self.llamaindex = llamaindex
        self.document_repository = document_repository
        self.cache = cache
        self.max_document_summaries = max_document_summaries

    def _collate_and_rerank_by_document_ids(
        self,
        results: List[RetrievalResult],
    ) -> List[DocumentResult]:
        scores: dict[str, float] = defaultdict(float)
        counter: dict[str, int] = defaultdict(int)
        results_by_doc_id: dict[str, List[RetrievalResult]] = defaultdict(list)
        for result in results:
            doc_id = self.llamaindex.get_document_id_for_result(result)
            if doc_id:
                counter[doc_id] += 1
                scores[doc_id] = (
                    scores[doc_id] * (counter[doc_id] - 1) / counter[doc_id]
                    + (result.score or 0.0) / counter[doc_id]
                )
                results_by_doc_id[doc_id].append(result)

        return [
            {
                "doc_id": id,
                "score": score,
                "results": results_by_doc_id[id],
            }
            for (id, score) in sorted(
                scores.items(), key=lambda kv: kv[1], reverse=True
            )
        ]

    def _generate_document_summaries(
        self, sorted_docs: List[DocumentResult], query: str
    ) -> List[tuple[DocumentResult, GenerationResult]]:
        responses: list[tuple[DocumentResult, GenerationResult]] = []
        for doc in sorted_docs:
            if len(responses) > self.max_document_summaries - 1:
                break
            response = self.llamaindex.synthesize(
                DOCUMENT_SUMMARY_PROMPT.format(query=query),
                nodes=doc["results"],
            )
            if response.response and not re.search(
                "(not |ir)relevant", response.response
            ):
                responses.append((doc, response))
        return responses

    def _generate_top_sentence(
        self, responses: list[tuple[DocumentResult, GenerationResult]], query: str
    ) -> GenerationResult:
        return self.llamaindex.synthesize(
            TOP_SENTENCE_PROMPT.format(query=query),
            nodes=[r2 for (d, _r) in responses for r2 in d["results"]],
        )

    def _query_docs(
        self,
        query: str,
    ) -> List[DocumentResult]:
        results = self.llamaindex.query_results(query)
        return self._collate_and_rerank_by_document_ids(results)

    def _make_summary(
        self,
        top_sentence: GenerationResult,
        responses: list[tuple[DocumentResult, GenerationResult]],
    ) -> Summary:
        document_summaries = []
        for document, response in responses:
            if response.response:
                summary = re.sub(
                    "^th(e|is) document", "", response.response, flags=re.IGNORECASE
                )
                document_summaries.append(
                    DocumentSummary(document=document["doc_id"], summary=summary)
                )
        return Summary(
            top_sentence=top_sentence.response or "",
            document_summaries=document_summaries,
        )

    def _uncached_query(
        self,
        query: str,
    ) -> SearchResult:
        sorted_docs = self._query_docs(query)
        responses = self._generate_document_summaries(sorted_docs, query)
        top_sentence = self._generate_top_sentence(responses, query)
        summary = self._make_summary(top_sentence, responses)
        return SearchResult(
            query=query,
            documents=[d["doc_id"] for d in sorted_docs],
            summary=summary,
        )

    def get_documents_for_query(self, query: str) -> List[Document]:
        sorted_docs = self._query_docs(query)
        return compact(
            [
                self.document_repository.get_document(doc["doc_id"])
                for doc in sorted_docs
            ]
        )

    def get_related_documents(
        self, query_doc: Document, limit: Optional[int] = None
    ) -> List[Document]:
        return [
            doc
            for doc in self.get_documents_for_query(query_doc.embeddable_text)
            if doc != query_doc
        ][0:limit]

    def query(self, query: str) -> SearchResult:
        return self.cache.cached(
            "query",
            [query],
            self._uncached_query,
            serializer=lambda sr: sr.asdict(),
            deserializer=lambda attrs: SearchResult.from_dict(**attrs),
        )

    def get_cached_query_response(self, query: str) -> Optional[SearchResult]:
        return self.cache.get_if_cached(
            "query",
            [query],
            deserializer=lambda attrs: SearchResult.from_dict(**attrs),
        )

    def index_documents(self, documents: List[DocumentWithText]) -> None:
        self.llamaindex.index_documents(documents)


def get_rag_index_instance(
    documents_repository: Optional[DocumentsRepository] = None,
) -> RAGIndex:
    llamaindex = get_llamaindex_instance()
    if documents_repository is None:
        documents_repository = DocumentsRepository(airtable.get_db_instance())
    cache = create_cache(prefix=environ["REDIS_QUERY_CACHE_PREFIX"])
    max_document_summaries = int(environ["RETRIEVAL_MAX_DOCUMENT_SUMMARIES"])
    return RAGIndex(llamaindex, documents_repository, cache, max_document_summaries)
