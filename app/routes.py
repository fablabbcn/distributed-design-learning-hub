from typing import Any, cast

from flask import current_app as app
from flask import jsonify, render_template, request, url_for

from . import airtable, celery, repositories, utils
from .models import Document, Theme


def _get_documents_repository() -> repositories.DocumentsRepository:
    return repositories.DocumentsRepository(airtable.get_db_instance())


@app.route("/index", methods=["POST"])
def index() -> Any:
    url = request.json.get("url")
    celery.dispatch(url)
    return jsonify(
        {
            "result": "OK",
            "code": 200,
            "details": f"URL {url} Queued for indexing",
        }
    )


@app.route("/", methods=["GET"])
def homepage() -> str:
    db = _get_documents_repository()

    documents = db.get_featured_documents()
    themes = db.get_all_themes()
    tags = db.get_all_tags()
    stats = db.get_stats()

    return render_template(
        "pages/index.j2",
        documents=documents,
        themes=themes,
        tags=tags,
        stats=stats,
    )


@app.route("/themes/<theme_name>", methods=["GET"])
def theme(theme_name: str) -> str:
    db = _get_documents_repository()

    documents = db.get_documents_for_theme(theme_name)
    tags = db.get_tags_for_theme(theme_name)
    theme = cast(Theme, db.get_theme(theme_name))

    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Themes"},
        {
            "title": theme.name,
            "url": url_for("theme", theme_name=theme.name),
        },
    )

    return render_template(
        "pages/theme.j2",
        breadcrumbs=breadcrumbs,
        documents=documents,
        tags=tags,
        theme=theme,
    )


@app.route("/tags/<tag>", methods=["GET"])
def tag(tag: str) -> str:
    db = _get_documents_repository()

    documents = db.get_documents_for_tag(tag)

    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Tags"}, {"title": tag, "url": url_for("tag", tag=tag)}
    )
    return render_template(
        "pages/tag.j2",
        breadcrumbs=breadcrumbs,
        tag=tag,
        documents=documents,
    )


@app.route("/documents/<document_id>", methods=["GET"])
def document(document_id: str) -> str:
    db = _get_documents_repository()

    document = cast(Document, db.get_document(document_id))

    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Documents"},
        {
            "title": document.title,
            "url": url_for(
                "document", document_id=utils.url_to_id(document.link)
            ),
        },
    )
    return render_template(
        "pages/document.j2",
        breadcrumbs=breadcrumbs,
        document=document,
    )
