from dataclasses import dataclass
from os import environ
from typing import Sequence, Union, cast

from llama_index.core import Document as LlamaDocument
from llama_index.core import QueryBundle, VectorStoreIndex, get_response_synthesizer
from llama_index.core.base.response.schema import Response
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.schema import BaseNode, NodeWithScore, TextNode
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

AnyNode = Union[BaseNode, NodeWithScore]


@dataclass
class LlamaIndexConfig:
    embedding_model_name: str
    llm_model_name: str
    es_url: str
    es_embeddings_index: str
    es_embeddings_field: str
    es_kv_index: str
    es_node_index: str
    es_ref_doc_index: str
    es_metadata_index: str
    mistral_api_key: str
    embedding_chunk_size: int
    embedding_chunk_overlap: int
    retrieval_top_k: int


class LlamaIndex:
    def __init__(self, config: LlamaIndexConfig):
        vector_store = ElasticsearchVectorStore(
            es_url=config.es_url,
            index_name=config.es_embeddings_index,
            vector_field=config.es_embeddings_field,
        )
        docstore = ElasticsearchDocumentStore(
            elasticsearch_kvstore=ElasticsearchKVStore(
                index_name=config.es_kv_index,
                es_url=config.es_url,
                es_client=None,
            ),
            node_collection_index=config.es_node_index,
            ref_doc_collection_index=config.es_ref_doc_index,
            metadata_collection_index=config.es_metadata_index,
        )
        embedding_model = MistralAIEmbedding(
            config.embedding_model_name, api_key=config.mistral_api_key
        )
        llm = MistralAI(config.llm_model_name, api_key=config.mistral_api_key)
        splitter = SentenceSplitter(
            chunk_size=config.embedding_chunk_size,
            chunk_overlap=config.embedding_chunk_overlap,
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store, embed_model=embedding_model
        )
        index.storage_context.docstore = docstore
        response_synthesizer = get_response_synthesizer(
            llm=llm,
            response_mode=ResponseMode.REFINE,
        )
        pipeline = IngestionPipeline(
            transformations=[splitter, embedding_model],
            vector_store=vector_store,
            docstore=docstore,
        )
        retriever = index.as_retriever(similarity_top_k=config.retrieval_top_k)

        self.retriever = retriever
        self.pipeline = pipeline
        self.embedding_model = embedding_model
        self.response_synthesizer = response_synthesizer
        self.docstore = docstore
        # Even though we don't explicitly use this again, we need to
        # ensure we hold a reference to it, otherwise we get a
        # "Timeout context manager should be used inside a task" RuntimeError:
        self.vector_store = vector_store

    def index_documents(self, documents: list[DocumentWithText]) -> None:
        llama_documents = [
            LlamaDocument(text=document.embeddable_text, doc_id=document.id)
            for document in documents
        ]
        self.pipeline.run(documents=llama_documents)

    def get_document(self, doc_id: str) -> TextNode:
        return cast(TextNode, self.docstore.get_document(doc_id))

    def synthesize(self, prompt: str, nodes: Sequence[AnyNode]) -> Response:
        return cast(Response, self.response_synthesizer.synthesize(prompt, nodes=nodes))

    def query_documents(self, query: str) -> list[NodeWithScore]:
        bundle = QueryBundle(
            query, embedding=self.embedding_model.get_query_embedding(query)
        )
        return cast(list[NodeWithScore], self.retriever.retrieve(bundle))


def get_llamaindex_instance() -> LlamaIndex:
    config = LlamaIndexConfig(
        es_url=environ["ELASTICSEARCH_URL"],
        es_embeddings_index=environ["ELASTICSEARCH_EMBEDDINGS_INDEX"],
        es_kv_index=environ["ELASTICSEARCH_KV_INDEX"],
        es_node_index=environ["ELASTICSEARCH_NODE_INDEX"],
        es_ref_doc_index=environ["ELASTICSEARCH_REF_DOC_INDEX"],
        es_metadata_index=environ["ELASTICSEARCH_METADATA_INDEX"],
        mistral_api_key=environ["MISTRAL_API_KEY"],
        es_embeddings_field=environ["ELASTICSEARCH_EMBEDDINGS_FIELD"],
        embedding_model_name=environ["MISTRAL_EMBEDDING_MODEL_NAME"],
        llm_model_name=environ["MISTRAL_LANGUAGE_MODEL_NAME"],
        embedding_chunk_size=int(environ["EMBEDDING_CHUNK_SIZE"]),
        embedding_chunk_overlap=int(environ["EMBEDDING_CHUNK_OVERLAP"]),
        retrieval_top_k=int(environ["RETRIEVAL_TOP_K"]),
    )
    return LlamaIndex(config)
