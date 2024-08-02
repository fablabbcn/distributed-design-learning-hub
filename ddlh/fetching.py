from os import environ
from typing import Optional

import requests
from requests.structures import CaseInsensitiveDict


def _headers() -> CaseInsensitiveDict[str]:
    user_agent = environ["FETCHER_USER_AGENT"]
    headers = requests.utils.default_headers()
    headers.update({"User-Agent": user_agent})
    return headers


def content_type(url: str) -> Optional[str]:
    response = requests.head(url, headers=_headers())
    response.raise_for_status()
    return response.headers["Content-Type"].split(";")[0]


def get(url: str) -> requests.Response:
    response = requests.get(url, headers=_headers())
    response.raise_for_status()
    return response
