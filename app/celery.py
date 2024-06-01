from celery import Celery
from boilerpy3.extractors import CanolaExtractor
from pypdf import PdfReader
import requests
from io import BytesIO
from elasticsearch import Elasticsearch
from hashlib import sha256

app = Celery('ddhub-prototype', broker='redis://redis:6379/0')

@app.task
def hello():
    return 'hello world'


@app.task
def dispatch(url):
    response = requests.head(url)
    content_type = response.headers['Content-Type'].split(";")[0]
    match content_type:
        case "text/html":
            ingest_html.delay(url)
        case "application/pdf":
            ingest_pdf.delay(url)

@app.task
def ingest_html(url):
    response = requests.get(url)
    extractor = CanolaExtractor()
    store.delay(url, extractor.get_content(response.text))

@app.task
def ingest_pdf(url):
    response = requests.get(url)
    pdf_data = BytesIO()
    pdf_data.write(response.content)
    pdf_data.seek(0)
    text = ""
    reader = PdfReader(pdf_data)
    for page in reader.pages:
        text += page.extract_text()
        text += "\n\n"
    store.delay(url, text)

@app.task
def store(url, text):
    client = Elasticsearch("http://elasticsearch:9200/")
    client.index(index="ddhub-prototype", id=url_to_id(url), document={"url": url, "text": text})

def url_to_id(url):
    return sha256(url.encode("UTF-8")).hexdigest()
