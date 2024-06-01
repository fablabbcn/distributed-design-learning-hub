from flask import Flask, jsonify, request
from . import celery

app = Flask(__name__)

@app.route("/index", methods=["POST"])
def index():
    url = request.json.get("url")
    celery.dispatch(url)
    return jsonify({ "result": "OK", "code": 200, "details": "URL %s Queued for indexing" % url })
