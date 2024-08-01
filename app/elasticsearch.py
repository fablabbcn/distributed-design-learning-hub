from os import environ
from typing import Any

from elasticsearch import Elasticsearch


def index(id: str, **document: Any) -> None:
    client = Elasticsearch(environ["ELASTICSEARCH_URL"])
    client.index(
        index=environ["ELASTICSEARCH_INDEX"],
        id=id,
        document=document,
    )


def update(id: str, **fields: Any) -> None:
    client = Elasticsearch(environ["ELASTICSEARCH_URL"])
    client.update(
        index=environ["ELASTICSEARCH_INDEX"],
        id=id,
        doc=fields,
    )
