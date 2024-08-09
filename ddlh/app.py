from gevent.pywsgi import WSGIServer

from ddlh import create_app

app = create_app()


def serve() -> None:
    http_server = WSGIServer(("0.0.0.0", 5000), app)
    http_server.serve_forever()


if __name__ == "__main__":
    serve()
