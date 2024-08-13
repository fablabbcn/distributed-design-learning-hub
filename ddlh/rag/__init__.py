import re
from collections import defaultdict
from typing import List, TypedDict, cast

from llama_index.core.base.response.schema import Response
from llama_index.core.schema import (
    NodeRelationship,
    NodeWithScore,
    RelatedNodeInfo,
    TextNode,
)

from ddlh import airtable
from ddlh.models import (
    Document,
    DocumentSummary,
    DocumentWithText,
    SearchResult,
    Summary,
)
from ddlh.rag.llamaindex import LlamaIndex, get_llamaindex_instance
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
        "document": TextNode,
        "results": List[NodeWithScore],
    },
)


class RAGIndex:
    def __init__(
        self, llamaindex: LlamaIndex, document_repository: DocumentsRepository
    ):
        self.llamaindex = llamaindex
        self.document_repository = document_repository

    def _collate_and_rerank_by_document_ids(
        self,
        results: List[NodeWithScore],
    ) -> List[DocumentResult]:
        scores: dict[str, float] = defaultdict(float)
        counter: dict[str, int] = defaultdict(int)
        results_by_doc_id: dict[str, List[NodeWithScore]] = defaultdict(list)
        docs = {}
        for result in results:
            source_node = cast(
                RelatedNodeInfo, result.node.relationships[NodeRelationship.SOURCE]
            )
            doc_id = source_node.node_id
            try:
                self.llamaindex.get_document(doc_id)
            except Exception:
                print("doc id %s not found!" % doc_id)
                continue
            counter[doc_id] += 1
            scores[doc_id] = (
                scores[doc_id] * (counter[doc_id] - 1) / counter[doc_id]
                + (result.score or 0.0) / counter[doc_id]
            )
            if doc_id not in docs:
                docs[doc_id] = self.llamaindex.get_document(doc_id)
            results_by_doc_id[doc_id].append(result)

        return [
            {
                "doc_id": id,
                "score": score,
                "document": docs[id],
                "results": results_by_doc_id[id],
            }
            for (id, score) in sorted(
                scores.items(), key=lambda kv: kv[1], reverse=True
            )
        ]

    def _generate_document_summaries(
        self, sorted_docs: List[DocumentResult], query: str
    ) -> List[tuple[DocumentResult, Response]]:
        responses: list[tuple[DocumentResult, Response]] = []
        for doc in sorted_docs:
            if len(responses) > 2:
                break
            response = self.llamaindex.synthesize(
                DOCUMENT_SUMMARY_PROMPT.format(query=query),
                # nodes=[NodeWithScore(node=doc["document"], score=doc["score"])],
                nodes=doc["results"],
            )
            if response.response and not re.search(
                "(not |ir)relevant", response.response
            ):
                responses.append((doc, response))
        return responses

    def _generate_top_sentence(
        self, responses: list[tuple[DocumentResult, Response]], query: str
    ) -> Response:
        return self.llamaindex.synthesize(
            TOP_SENTENCE_PROMPT.format(query=query),
            nodes=[r2 for (d, _r) in responses for r2 in d["results"]],
        )

    def _query_to_sorted_docs(
        self,
        query: str,
    ) -> tuple[list[NodeWithScore], List[DocumentResult]]:
        results = self.llamaindex.query_documents(query)
        return (results, self._collate_and_rerank_by_document_ids(results))

    def _make_summary(
        self, top_sentence: Response, responses: list[tuple[DocumentResult, Response]]
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

    def get_documents_for_query(self, query: str) -> List[Document]:
        sorted_docs = self._query_to_sorted_docs(query)[1]
        return compact(
            [
                self.document_repository.get_document(doc["doc_id"])
                for doc in sorted_docs
            ]
        )

    def query(
        self,
        query: str,
    ) -> SearchResult:
        (results, sorted_docs) = self._query_to_sorted_docs(query)
        responses = self._generate_document_summaries(sorted_docs, query)
        top_sentence = self._generate_top_sentence(responses, query)
        summary = self._make_summary(top_sentence, responses)
        return SearchResult(
            query=query,
            documents=[d["doc_id"] for d in sorted_docs],
            summary=summary,
        )

    def index_documents(self, documents: List[DocumentWithText]) -> None:
        self.llamaindex.index_documents(documents)


def get_rag_index_instance() -> RAGIndex:
    llamaindex = get_llamaindex_instance()
    repository = DocumentsRepository(airtable.get_db_instance())
    return RAGIndex(llamaindex, repository)
