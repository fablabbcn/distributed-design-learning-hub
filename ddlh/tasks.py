from os import environ
from typing import List

from celery import current_task, shared_task
from celery.app.task import Task
from flask import current_app as app
from flask_socketio import SocketIO

from ddlh import rag
from ddlh.extraction import extract_html, extract_pdf
from ddlh.fetching import content_type, get
from ddlh.formatters import format_search_result
from ddlh.models import Document, DocumentWithText

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa


def extract_text_from_link(url: str) -> str:
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
    return text


@shared_task(ignore_result=False)
def fetch(document: Document) -> DocumentWithText:
    text = extract_text_from_link(document.link)
    if document.invisible_link:
        text += "\n\n\n" + extract_text_from_link(document.invisible_link)
    return document.enrich_with_text(text)


@shared_task
def index(documents: List[DocumentWithText]) -> None:
    rag_index = rag.get_rag_index_instance()
    rag_index.index_documents(documents)


@shared_task
def query(
    query: str,
) -> None:
    rag_index = rag.get_rag_index_instance()
    response = rag_index.query(query)
    with app.test_request_context("localhost"):
        if response.summary:
            msg = format_search_result(response)
            socketio = SocketIO(message_queue=environ["REDIS_URL"])
            socketio.emit("msg", {"msg": msg}, to=current_task.request.id)
