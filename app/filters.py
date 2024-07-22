from typing import Optional, TypeVar, Union

from flask import current_app as app

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


app.jinja_env.filters["get_first"] = get_first
app.jinja_env.filters["url_to_id"] = url_to_id
