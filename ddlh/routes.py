from typing import cast

from flask import current_app as app
from flask import render_template, request, url_for

from . import airtable, rag, repositories, tasks, utils
from .formatters import format_summary
from .models import Document, Theme


def _get_documents_repository() -> repositories.DocumentsRepository:
    return repositories.DocumentsRepository(airtable.get_db_instance())


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
            "url": url_for("document", document_id=utils.url_to_id(document.link)),
        },
    )
    return render_template(
        "pages/document.j2",
        breadcrumbs=breadcrumbs,
        document=document,
    )


@app.route("/query", methods=["GET"])
def query() -> str:
    query = request.args["query"]
    tags: list[str] = []
    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Themes"},
        {
            "title": query,
            "url": url_for("query", query=theme),
        },
    )
    rag_index = rag.get_rag_index_instance()
    documents = rag_index.get_documents_for_query(query)
    query_response = rag_index.get_cached_query_response(query)
    if query_response and query_response.summary:
        summary = format_summary(query_response.summary)
        task_id = None
    else:
        task = tasks.query.delay(query)
        task_id = task.task_id
        summary = None
    return render_template(
        "pages/theme.j2",
        breadcrumbs=breadcrumbs,
        documents=documents,
        tags=tags,
        theme={"name": query},
        query_task_id=task_id,
        query_summary=summary,
    )
