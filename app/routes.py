import random
from typing import Any

from flask import current_app as app
from flask import jsonify, render_template, request

from . import airtable, celery, repositories


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

    documents = db.get_all_documents()

    return render_template(
        "pages/index.j2",
        documents=random.sample(documents, k=len(documents)),
        themes=db.get_all_themes(),
        tags=db.get_all_tags(),
    )


@app.route("/themes/<theme_name>", methods=["GET"])
def theme(theme_name: str) -> str:
    db = _get_documents_repository()

    documents = db.get_documents_for_theme(theme_name)
    tags = db.get_tags_for_theme(theme_name)
    theme = db.get_theme(theme_name)

    return render_template(
        "pages/theme.j2",
        documents=documents,
        tags=tags,
        theme=theme,
    )


@app.route("/tags/<tag>", methods=["GET"])
def tag(tag: str) -> str:
    db = _get_documents_repository()

    documents = db.get_documents_for_tag(tag)

    return render_template(
        "pages/tag.j2",
        tag=tag,
        documents=documents,
    )


@app.route("/documents/<document_id>", methods=["GET"])
def document(document_id: str) -> str:
    db = _get_documents_repository()

    document = db.get_document(document_id)
    return render_template(
        "pages/document.j2",
        document=document,
    )
