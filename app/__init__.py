from flask import Flask, jsonify, request, render_template
from . import celery, airtable_db

app = Flask(__name__)
db = airtable_db.AirtableDocumentDatabase()


@app.route("/index", methods=["POST"])
def index():
    url = request.json.get("url")
    celery.dispatch(url)
    return jsonify({ "result": "OK", "code": 200, "details": "URL %s Queued for indexing" % url })

@app.route("/", methods=["GET"])
def homepage():
    theme = request.args.get("theme")
    tag = request.args.get("tag")

    if theme is not None:
        subtitle=f"Theme: {theme}"
        documents=db.get_documents_for_theme(theme);
    elif tag is not None:
        subtitle=f"Tag: {tag}"
        documents=db.get_documents_for_tag(tag);
    else:
        subtitle=None
        documents=db.get_all_documents();

    return render_template("index.html", subtitle=subtitle, documents=documents, themes=db.get_all_themes(), tags=db.get_all_tags())
