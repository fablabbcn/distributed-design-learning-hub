from functools import partial
from hashlib import sha256
from operator import is_not
from typing import Callable, Optional, TypedDict, TypeGuard, TypeVar, cast

from flask import url_for

T = TypeVar("T")

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


def compact(lst: list[Optional[T]]) -> list[T]:
    """
    Remove 'None's from a list
    """
    not_none = cast(Callable[[T | None], TypeGuard[T]], partial(is_not, None))
    return list(filter(not_none, lst))


def downcase_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else ""
