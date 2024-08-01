from hashlib import sha256
from typing import Optional, TypedDict

from flask import url_for

Breadcrumb = TypedDict(
    "Breadcrumb",
    {
        "title": str,
        "url": Optional[str],
    },
    total=False,
)


def url_to_id(url: str) -> str:
    return sha256(url.encode("UTF-8")).hexdigest()


def get_breadcrumbs(*breadcrumbs: Breadcrumb) -> list[Breadcrumb]:
    homepage: Breadcrumb = {
        "title": "Learning Hub",
        "url": url_for("homepage"),
    }
    return [homepage] + list(breadcrumbs)
