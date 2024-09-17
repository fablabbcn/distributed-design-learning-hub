from typing import cast

from flask import current_app as app
from flask import render_template, request, url_for

from . import tasks, utils
from .formatters import format_search_result
from .models import Document, Theme
from .repositories import DocumentsRepository


@app.route("/", methods=["GET"])
def homepage() -> str:
    db = DocumentsRepository(app.config["airtable_instance"])

    documents = db.get_featured_documents()
    themes = db.get_all_themes()
    tags = db.get_all_tags()
    stats = db.get_stats()

    return render_template(
        "pages/index.j2",
        breadcrumbs=[],
        documents=documents,
        themes=themes,
        tags=tags,
        stats=stats,
    )


@app.route("/themes/<theme_name>", methods=["GET"])
def theme(theme_name: str) -> str:
    db = DocumentsRepository(app.config["airtable_instance"])

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
    db = DocumentsRepository(app.config["airtable_instance"])

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


@app.route("/formats/<format>", methods=["GET"])
def format(format: str) -> str:
    FORMAT_NAMES = {
        "text": "Publications, papers & reports",
        "tool": "Toolkits, methods & frameworks",
        "audiovisual": "Masterclasses, documentaries & podcasts",
        "course": "Interactive learning resources",
    }

    db = DocumentsRepository(app.config["airtable_instance"])

    documents = db.get_documents_for_format_type(format)

    format_name = FORMAT_NAMES[format]

    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Formats"},
        {"title": format_name, "url": url_for("format", format=format)},
    )
    return render_template(
        "pages/format.j2",
        breadcrumbs=breadcrumbs,
        format=format,
        format_name=format_name,
        documents=documents,
    )


@app.route("/documents/<document_id>", methods=["GET"])
def document(document_id: str) -> str:
    db = DocumentsRepository(app.config["airtable_instance"])
    rag_index = app.config["rag_index"]

    document = cast(Document, db.get_document(document_id))
    related_documents = rag_index.get_related_documents(document, limit=5)

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
        related_documents=related_documents,
    )


@app.route("/query", methods=["GET"])
def query() -> str:
    rag_index = app.config["rag_index"]
    query = request.args["query"]
    breadcrumbs = utils.get_breadcrumbs(
        {"title": "Themes"},
        {
            "title": query,
            "url": url_for("query", query=theme),
        },
    )
    documents = rag_index.get_documents_for_query(query)
    tags = utils.tags_for_document_collection(documents)
    query_response = rag_index.get_cached_query_response(query)
    if query_response:
        summary = format_search_result(query_response)
        task_id = None
        wait_message = False
    else:
        task = tasks.query.delay(query)
        task_id = task.task_id
        summary = None
        wait_message = True
    return render_template(
        "pages/theme.j2",
        breadcrumbs=breadcrumbs,
        documents=documents,
        tags=tags,
        theme={"name": query},
        query_task_id=task_id,
        query_summary=summary,
        wait_message=wait_message,
    )


@app.route("/about-our-use-of-llms", methods={"GET"})
def about_llms() -> str:
    breadcrumbs = utils.get_breadcrumbs(
        {
            "title": "About our use of Large Language Models",
            "url": url_for("about_llms"),
        },
    )
    return render_template(
        "pages/about_llms.j2",
        breadcrumbs=breadcrumbs,
    )
