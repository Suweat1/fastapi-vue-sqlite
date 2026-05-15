from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import User
from ..realtime import realtime_manager
from ..security import decode_access_token


router = APIRouter(prefix="/ws", tags=["realtime"])


def _authenticate_user(token: str) -> User | None:
    db: Session = SessionLocal()
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        user = db.get(User, user_id)
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None
    finally:
        db.close()


@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket, token: str | None = Query(default=None)):
    if not token:
        await websocket.close(code=1008)
        return

    user = _authenticate_user(token)
    if not user:
        await websocket.close(code=1008)
        return

    realtime_manager.set_loop(asyncio.get_running_loop())
    await realtime_manager.connect(websocket, user.id)
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
    finally:
        await realtime_manager.disconnect(websocket, user.id)

