from functools import partial
from operator import is_not
from typing import Callable, Optional, TypeGuard, TypeVar, Union, cast

from flask import current_app as app

from .models import Document
from .utils import url_to_id

U = TypeVar("U")


def get_first(
    items: list[U], n: Optional[int] = None
) -> Optional[Union[U, list[U]]]:
    if items is not None:
        if n is not None:
            return items[0:n]
        elif len(items) > 0:
            return items[0]
        else:
            return None


def document_css_classes(document: Document) -> str:
    not_none = cast(
        Callable[[str | None], TypeGuard[str]], partial(is_not, None)
    )
    return " ".join(
        filter(
            not_none,
            [
                document.get("format_type"),
                (
                    "with-image"
                    if document.get("image_url") is not None
                    else None
                ),
            ],
        )
    )


app.jinja_env.filters["get_first"] = get_first
app.jinja_env.filters["url_to_id"] = url_to_id
app.jinja_env.filters["document_css_classes"] = document_css_classes
