from os import environ
from typing import List

from celery import Celery, current_task
from celery.app.task import Task
from flask_socketio import SocketIO

from ddlh import rag
from ddlh.extraction import extract_html, extract_pdf
from ddlh.fetching import content_type, get
from ddlh.models import Document, DocumentWithText

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
    rag.index_documents(documents)


@app.task(bind=True)
def query(
    self: Task[[str], None],
    query: str,
) -> None:
    response = rag.query(query)
    msg = response[3].response
    socketio = SocketIO(message_queue=environ["REDIS_URL"])
    socketio.emit("msg", {"msg": msg}, to=current_task.request.id)
