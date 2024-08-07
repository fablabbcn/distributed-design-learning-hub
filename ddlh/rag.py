import re
from collections import defaultdict
from os import environ
from typing import List, TypedDict, cast

from llama_index.core import Document as LlamaDocument
from llama_index.core import QueryBundle, VectorStoreIndex, get_response_synthesizer
from llama_index.core.base.response.schema import Response
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import BaseSynthesizer, ResponseMode
from llama_index.core.schema import (
    Node,
    NodeRelationship,
    NodeWithScore,
    RelatedNodeInfo,
)
from llama_index.embeddings.mistralai import MistralAIEmbedding  # type: ignore
from llama_index.llms.mistralai import MistralAI  # type: ignore
from llama_index.storage.docstore.elasticsearch import (  # type: ignore
    ElasticsearchDocumentStore,
)
from llama_index.storage.kvstore.elasticsearch import (  # type: ignore
    ElasticsearchKVStore,
)

from ddlh.models import DocumentWithText

from llama_index.vector_stores.elasticsearch import (  # type: ignore # isort:skip
    ElasticsearchStore as ElasticsearchVectorStore,
)


TOP_K: int = 10

RESPONSE_MODE: ResponseMode = ResponseMode.REFINE

EMBEDDING_MODEL_NAME: str = "mistral-embed"

LLM_MODEL_NAME: str = "open-mixtral-8x22b"

DOCUMENT_SUMMARY_PROMPT: str = """
<s>[INST]explain in one sentence how this document relates to the theme of \"{query}\".
 If the document does not contain information about the theme of \"{query}\",
 return \"This document is irrelevant\".[/INST]This document </s>
"""

TOP_SENTENCE_PROMPT: str = """
<s>[INST]Provide a one or two sentence description of \"{query}\"
 based on the information given.[/INST] {query}</s>
"""


def _vector_store() -> ElasticsearchVectorStore:
    return ElasticsearchVectorStore(
        es_url=environ["ELASTICSEARCH_URL"],
        index_name=environ["ELASTICSEARCH_EMBEDDINGS_INDEX"],
        vector_field="embedding",
    )


def _docstore() -> ElasticsearchDocumentStore:
    return ElasticsearchDocumentStore(
        elasticsearch_kvstore=ElasticsearchKVStore(
            index_name=environ["ELASTICSEARCH_KV_INDEX"],
            es_client=None,
            es_url=environ["ELASTICSEARCH_URL"],
        ),
        node_collection_index=environ["ELASTICSEARCH_NODE_INDEX"],
        ref_doc_collection_index=environ["ELASTICSEARCH_REF_DOC_INDEX"],
        metadata_collection_index=environ["ELASTICSEARCH_METADATA_INDEX"],
    )


def _embedding_model() -> MistralAIEmbedding:
    return MistralAIEmbedding(EMBEDDING_MODEL_NAME, api_key=environ["MISTRAL_API_KEY"])


def _llm() -> MistralAI:
    return MistralAI(LLM_MODEL_NAME, api_key=environ["MISTRAL_API_KEY"])


def _response_synthesizer() -> BaseSynthesizer:
    return get_response_synthesizer(llm=_llm(), response_mode=RESPONSE_MODE)


DocumentResult = TypedDict(
    "DocumentResult",
    {"doc_id": str, "score": float, "document": Node, "results": List[NodeWithScore]},
)


def _collate_and_rerank_by_document_ids(
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
            _docstore().get_document(doc_id)
        except Exception:
            print("doc id %s not found!" % doc_id)
            continue
        counter[doc_id] += 1
        scores[doc_id] = (
            scores[doc_id] * (counter[doc_id] - 1) / counter[doc_id]
            + (result.score or 0.0) / counter[doc_id]
        )
        if doc_id not in docs:
            docs[doc_id] = _docstore().get_document(doc_id)
        results_by_doc_id[doc_id].append(result)

    return [
        {
            "doc_id": id,
            "score": score,
            "document": docs[id],
            "results": results_by_doc_id[id],
        }
        for (id, score) in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ]


def _generate_document_summaries(
    sorted_docs: List[DocumentResult], query: str
) -> List[tuple[DocumentResult, Response]]:
    responses: list[tuple[DocumentResult, Response]] = []
    for doc in sorted_docs:
        if len(responses) > 2:
            break
        response = _response_synthesizer().synthesize(
            DOCUMENT_SUMMARY_PROMPT.format(query=query),
            nodes=[NodeWithScore(node=doc["document"], score=doc["score"])],
        )
        if not re.search("irrelevant", response.response):
            responses.append((doc, response))
    return responses


def _generate_top_sentence(
    responses: list[tuple[DocumentResult, Response]], query: str
) -> Response:
    return cast(
        Response,
        _response_synthesizer().synthesize(
            TOP_SENTENCE_PROMPT.format(query=query),
            nodes=[r2 for (d, r) in responses for r2 in d["results"]],
        ),
    )


def index_documents(documents: List[DocumentWithText]) -> None:
    llama_documents = [
        LlamaDocument(text=document.embeddable_text, doc_id=document.id)
        for document in documents
    ]
    embedding = _embedding_model()
    splitter = SentenceSplitter(chunk_size=350, chunk_overlap=50)
    es_vector_store = _vector_store()
    es_docstore = _docstore()
    pipeline = IngestionPipeline(
        transformations=[splitter, embedding],
        vector_store=es_vector_store,
        docstore=es_docstore,
    )
    pipeline.run(documents=llama_documents)


def query(
    query: str,
) -> tuple[
    list[Node], list[DocumentResult], list[tuple[DocumentResult, Response]], Response
]:
    embed_model = _embedding_model()
    index = VectorStoreIndex.from_vector_store(_vector_store(), embed_model=embed_model)
    index.storage_context.docstore = _docstore()
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    bundle = QueryBundle(query, embedding=embed_model.get_query_embedding(query))
    results = retriever.retrieve(bundle)
    sorted_docs = _collate_and_rerank_by_document_ids(results)
    responses = _generate_document_summaries(sorted_docs, query)
    top_sentence = _generate_top_sentence(responses, query)
    return (results, sorted_docs, responses, top_sentence)
