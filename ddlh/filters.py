from typing import Optional, TypeVar, Union

from flask import current_app as app

from .models import Document
from .utils import Breadcrumb, compact, url_to_id

U = TypeVar("U")


def get_first(items: list[U], n: Optional[int] = None) -> Optional[Union[U, list[U]]]:
    if items is not None:
        if n is not None:
            return items[0:n]
        elif len(items) > 0:
            return items[0]
        else:
            return None


def document_css_classes(document: Document) -> str:
    return " ".join(
        compact(
            [
                document.format_type,
                ("with-image" if document.image_url is not None else None),
            ]
        )
    )


def page_title_from_breadcrumbs(breadcrumbs: list[Breadcrumb]) -> str:
    return " | ".join(
        ["Distributed Design Learning Hub"] + [b["title"] for b in breadcrumbs[1:]]
    )


def any(collection: list[U]) -> bool:
    return len(collection) > 0


app.jinja_env.filters["get_first"] = get_first
app.jinja_env.filters["url_to_id"] = url_to_id
app.jinja_env.filters["document_css_classes"] = document_css_classes
app.jinja_env.filters["page_title_from_breadcrumbs"] = page_title_from_breadcrumbs
app.jinja_env.filters["any"] = any
