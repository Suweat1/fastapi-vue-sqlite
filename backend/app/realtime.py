from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._connections: dict[int, dict[int, WebSocket]] = defaultdict(dict)
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        with self._lock:
            self._connections[user_id][id(websocket)] = websocket

    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        with self._lock:
            connections = self._connections.get(user_id)
            if not connections:
                return
            connections.pop(id(websocket), None)
            if not connections:
                self._connections.pop(user_id, None)

    async def _send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        with self._lock:
            sockets = list(self._connections.get(user_id, {}).values())

        dead_sockets: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead_sockets.append(websocket)

        if dead_sockets:
            with self._lock:
                connections = self._connections.get(user_id)
                if not connections:
                    return
                for websocket in dead_sockets:
                    connections.pop(id(websocket), None)
                if not connections:
                    self._connections.pop(user_id, None)

    def broadcast(self, user_id: int, payload: dict[str, Any]) -> None:
        loop = self._loop
        if not loop or not loop.is_running():
            return
        asyncio.run_coroutine_threadsafe(self._send_to_user(user_id, payload), loop)

    async def shutdown(self) -> None:
        with self._lock:
            sockets = [(user_id, websocket) for user_id, connections in self._connections.items() for websocket in connections.values()]
            self._connections.clear()

        for _, websocket in sockets:
            try:
                await websocket.close(code=1001)
            except Exception:
                pass


realtime_manager = RealtimeManager()

