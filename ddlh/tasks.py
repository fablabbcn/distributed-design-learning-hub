from io import BytesIO
from os import environ

import requests
from boilerpy3.extractors import CanolaExtractor  # type: ignore
from celery import Celery
from celery.app.task import Task
from pypdf import PdfReader
from requests.structures import CaseInsensitiveDict

from ddlh import elasticsearch
from ddlh.utils import url_to_id

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa

app = Celery("ddhub-prototype", broker=environ["CELERY_BROKER_URL"])


def get_headers() -> CaseInsensitiveDict[str]:
    user_agent = environ["FETCHER_USER_AGENT"]
    headers = requests.utils.default_headers()
    headers.update({"User-Agent": user_agent})
    return headers


@app.task(bind=True)
def dispatch(self: Task[[str], None], url: str) -> None:
    response = requests.head(url, headers=get_headers())
    content_type = response.headers["Content-Type"].split(";")[0]
    match content_type:
        case "text/html":
            ingest_html.delay(url)
        case "application/pdf":
            ingest_pdf.delay(url)


@app.task(bind=True)
def ingest_html(self: Task[[str], None], url: str) -> None:
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    extractor = CanolaExtractor()
    store.delay(url, extractor.get_content(response.text))


@app.task(bind=True)
def ingest_pdf(self: Task[[str], None], url: str) -> None:
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    reader = PdfReader(BytesIO(response.content))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
        text += "\n\n"
    store.delay(url, text.strip())


@app.task(bind=True)
def store(self: Task[[str, str], None], url: str, text: str) -> None:
    elasticsearch.update(url_to_id(url), text=text)
