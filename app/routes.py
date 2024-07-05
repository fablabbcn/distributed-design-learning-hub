import random
from typing import Any

from flask import current_app as app
from flask import jsonify, render_template, request

from . import airtable_db, celery


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
    db = airtable_db.AirtableDocumentDatabase()

    theme = request.args.get("theme")
    tag = request.args.get("tag")

    if theme is not None:
        subtitle = f"Theme: {theme}"
        documents = db.get_documents_for_theme(theme)
    elif tag is not None:
        subtitle = f"Tag: {tag}"
        documents = db.get_documents_for_tag(tag)
    else:
        subtitle = None
        documents = db.get_all_documents()

    return render_template(
        "pages/index.j2",
        subtitle=subtitle,
        documents=random.sample(documents, k=len(documents)),
        themes=db.get_all_themes(),
        tags=db.get_all_tags(),
    )
