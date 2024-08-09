from typing import Any

from flask_socketio import SocketIO, join_room

socketio = SocketIO()


@socketio.on("join_room")
def on_room(data: dict[str, Any]) -> None:
    join_room(data["room_id"])
