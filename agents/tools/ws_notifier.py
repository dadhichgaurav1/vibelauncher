"""WebSocket notifier — broadcasts state updates to the frontend."""

from __future__ import annotations
import json
from typing import TYPE_CHECKING

# Global registry of active WebSocket connections: launch_id -> websocket
_connections: dict[str, object] = {}


def register_connection(launch_id: str, websocket) -> None:
    _connections[launch_id] = websocket


def unregister_connection(launch_id: str) -> None:
    _connections.pop(launch_id, None)


async def notify(channel: str, msg_type: str, data) -> None:
    """Send a message to the WebSocket connection for a launch session."""
    ws = _connections.get(channel)
    if not ws:
        return
    try:
        await ws.send_text(json.dumps({"type": msg_type, "data": data}))
    except Exception:
        pass
