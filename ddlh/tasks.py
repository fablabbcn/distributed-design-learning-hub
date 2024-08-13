from os import environ
from typing import List

from celery import current_task, shared_task
from celery.app.task import Task
from flask import current_app as app
from flask_socketio import SocketIO

from ddlh import rag
from ddlh.extraction import extract_html, extract_pdf
from ddlh.fetching import content_type, get
from ddlh.formatters import format_summary
from ddlh.models import Document, DocumentWithText

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa


@shared_task(ignore_result=False)
def fetch(document: Document) -> DocumentWithText:
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


@shared_task
def index(documents: List[DocumentWithText]) -> None:
    rag.index_documents(documents)


@shared_task
def query(
    query: str,
) -> None:
    response = rag.query(query)
    with app.test_request_context("localhost"):
        if response.summary:
            msg = format_summary(response.summary)
            socketio = SocketIO(message_queue=environ["REDIS_URL"])
            socketio.emit("msg", {"msg": msg}, to=current_task.request.id)
