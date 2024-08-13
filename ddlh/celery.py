from ddlh import create_app, tasks  # noqa: F401

flask_app = create_app()
celery_app = flask_app.extensions["celery"]
