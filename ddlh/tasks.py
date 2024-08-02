from os import environ

from celery import Celery
from celery.app.task import Task

from ddlh import elasticsearch
from ddlh.extraction import extract_html, extract_pdf
from ddlh.fetching import content_type, get
from ddlh.utils import url_to_id

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa

app = Celery("ddhub-prototype", broker=environ["CELERY_BROKER_URL"])


@app.task(bind=True)
def dispatch(self: Task[[str], None], url: str) -> None:
    match content_type(url):
        case "text/html":
            ingest_html.delay(url)
        case "application/pdf":
            ingest_pdf.delay(url)


@app.task(bind=True)
def ingest_html(self: Task[[str], None], url: str) -> None:
    response = get(url)
    store.delay(url, extract_html(response.text))


@app.task(bind=True)
def ingest_pdf(self: Task[[str], None], url: str) -> None:
    response = get(url)
    store.delay(url, extract_pdf(response.content))


@app.task(bind=True)
def store(self: Task[[str, str], None], url: str, text: str) -> None:
    elasticsearch.update(url_to_id(url), text=text)
