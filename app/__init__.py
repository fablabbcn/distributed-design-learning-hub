from flask import Flask
from jinja_markdown2 import MarkdownExtension


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.add_extension(MarkdownExtension)

    with app.app_context():
        from . import filters, routes  # noqa

    return app
