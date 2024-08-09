from flask import session
from flask_socketio import SocketIO, join_room

socketio = SocketIO()


@socketio.on("join_room")
def on_room() -> None:
    room = str(session["uid"])
    join_room(room)
