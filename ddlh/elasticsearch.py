from os import environ
from typing import Any

from elasticsearch import Elasticsearch

from ddlh.models import Document


def index(id: str, **document: Any) -> None:
    client = Elasticsearch(environ["ELASTICSEARCH_URL"])
    client.index(
        index=environ["ELASTICSEARCH_DOCUMENTS"],
        id=id,
        document=document,
    )


def update(id: str, **fields: Any) -> None:
    client = Elasticsearch(environ["ELASTICSEARCH_URL"])
    client.update(
        index=environ["ELASTICSEARCH_DOCUMENTS"],
        id=id,
        doc=fields,
    )


def get_document(id: str) -> Document:
    client = Elasticsearch(environ["ELASTICSEARCH_URL"])
    data = client.get(
        index=environ["ELASTICSEARCH_DOCUMENTS"],
        id=id,
    )
    return Document.from_dict(**data["_source"])
