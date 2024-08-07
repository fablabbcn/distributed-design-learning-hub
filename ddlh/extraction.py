from io import BytesIO
from typing import cast

from boilerpy3.extractors import CanolaExtractor  # type: ignore
from pypdf import PdfReader


def extract_html(html: str) -> str:
    extractor = CanolaExtractor()
    return cast(str, extractor.get_content(html))


def extract_pdf(bytes: bytes) -> str:
    reader = PdfReader(BytesIO(bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
        text += "\n\n"
    return text.strip()
