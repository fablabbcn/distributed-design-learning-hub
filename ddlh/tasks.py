from os import environ
from typing import List

from celery import Celery
from celery.app.task import Task

from ddlh.extraction import extract_html, extract_pdf
from ddlh.fetching import content_type, get
from ddlh.models import Document, DocumentWithText
from ddlh.rag import index_documents

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa

app = Celery("ddhub-prototype", broker=environ["CELERY_BROKER_URL"])

app.conf.update(
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["application/json", "application/x-python-serialize"],
)


@app.task(bind=True)
def fetch(
    self: Task[[Document], DocumentWithText], document: Document
) -> DocumentWithText:
    url = document.link
    try:
        response = get(url)
        match content_type(response):
            case "text/html":
                text = extract_html(response.text)
            case "application/pdf":
                text = extract_pdf(response.content)
            case _:
                text = ""
    except Exception:
        text = ""
    return document.enrich_with_text(text)


@app.task(bind=True)
def index(
    self: Task[[List[DocumentWithText]], None], documents: List[DocumentWithText]
) -> None:
    index_documents(documents)
