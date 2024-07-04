from hashlib import sha256
from io import BytesIO

import requests
from boilerpy3.extractors import CanolaExtractor  # type: ignore
from celery import Celery
from celery.app.task import Task
from elasticsearch import Elasticsearch  # type: ignore
from pypdf import PdfReader  # type: ignore

# Monkey-patch needed for celery-types: https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined] # noqa

app = Celery("ddhub-prototype", broker="redis://redis:6379/0")
user_agent = "FablabBCN-DDLH-indexer/0.0.0"
headers = requests.utils.default_headers()
headers.update({"User-Agent": user_agent})


@app.task(bind=True)
def dispatch(self: Task[[str], None], url: str) -> None:
    response = requests.head(url, headers=headers)
    content_type = response.headers["Content-Type"].split(";")[0]
    match content_type:
        case "text/html":
            ingest_html.delay(url)
        case "application/pdf":
            ingest_pdf.delay(url)


@app.task(bind=True)
def ingest_html(self: Task[[str], None], url: str) -> None:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    extractor = CanolaExtractor()
    store.delay(url, extractor.get_content(response.text))


@app.task(bind=True)
def ingest_pdf(self: Task[[str], None], url: str) -> None:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    pdf_data = BytesIO()
    pdf_data.write(response.content)
    pdf_data.seek(0)
    text = ""
    reader = PdfReader(pdf_data)
    for page in reader.pages:
        text += page.extract_text()
        text += "\n\n"
    store.delay(url, text)


@app.task(bind=True)
def store(self: Task[[str, str], None], url: str, text: str) -> None:
    client = Elasticsearch("http://elasticsearch:9200/")
    client.index(
        index="ddhub-prototype",
        id=url_to_id(url),
        document={"url": url, "text": text},
    )


def url_to_id(url: str) -> str:
    return sha256(url.encode("UTF-8")).hexdigest()
