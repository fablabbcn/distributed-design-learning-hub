from gevent import monkey

monkey.patch_all()

from os import environ  # noqa: E402

from flask import Flask  # noqa: E402
from jinja_markdown2 import MarkdownExtension  # noqa: E402

from .events import socketio  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.add_extension(MarkdownExtension)
    app.secret_key = environ["SECRET_KEY"]
    socketio.init_app(app, message_queue=environ["REDIS_URL"])
    with app.app_context():
        from . import filters, routes  # noqa

    return app
