from gevent import monkey

monkey.patch_all()

from os import environ  # noqa: E402
from typing import TYPE_CHECKING, ParamSpec, TypeVar  # noqa: E402

import celery  # noqa: E402
from celery import Celery  # noqa: E402
from flask import Flask  # noqa: E402
from jinja_markdown2 import MarkdownExtension  # noqa: E402

from . import airtable, rag, repositories  # noqa: E402
from .events import socketio  # noqa: E402

_P = ParamSpec("_P")
_R = TypeVar("_R")

# Hack to make typechecking work when inheriting from generics:
# https://stackoverflow.com/questions/45414066/mypy-how-to-define-a-generic-subclass
if TYPE_CHECKING:
    Task = celery.Task
else:

    class FakeGenericMeta(type):
        def __getitem__(self, _item):
            return self

    class Task(celery.Task, metaclass=FakeGenericMeta):
        pass


def _get_documents_repository() -> repositories.DocumentsRepository:
    return repositories.DocumentsRepository(airtable.get_db_instance())


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task[_P, _R]):
        def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=environ["CELERY_BROKER_URL"],
            result_backend=environ["CELERY_RESULT_BACKEND"],
            task_ignore_result=True,
            task_serializer="pickle",
            result_serializer="pickle",
            accept_content=["application/json", "application/x-python-serialize"],
        )
    )
    app.config.from_prefixed_env()  # type:ignore
    app.config["documents_repository"] = _get_documents_repository()
    app.config["rag_index"] = rag.get_rag_index_instance(
        app.config["documents_repository"]
    )
    celery_init_app(app)
    app.jinja_env.add_extension(MarkdownExtension)
    app.secret_key = environ["SECRET_KEY"]
    socketio.init_app(
        app,
        message_queue=environ["REDIS_URL"],
        cors_allowed_origins=[environ["HOSTNAME"]],
    )
    with app.app_context():
        from . import filters, routes  # noqa

    return app
