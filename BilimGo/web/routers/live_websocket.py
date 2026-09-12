from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.config import settings
from db.database import database
from db.repositories.user_repo import UserRepository
from services.live_stream_service import live_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/live", tags=["live_ws"])


@router.websocket("/ws/{session_id}")
async def live_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """Live WebSocket endpoint"""
    try:
        # Query parameterdan telegram_id olish
        telegram_id_raw = websocket.query_params.get("user_id", "0")
        try:
            telegram_id = int(telegram_id_raw)
        except ValueError:
            telegram_id = 0

        if not telegram_id:
            await websocket.close(code=4001, reason="Authentication required")
            return

        user_repo = UserRepository(database.conn)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            user = await user_repo.get_or_create(telegram_id=telegram_id)

        # Session ma'lumotlarini tekshirish
        session = await live_manager.get_session_info(session_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Connect
        await live_manager.connect(session_id, websocket, user.id)

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await live_manager.handle_message(
                        session_id,
                        websocket,
                        user.id,
                        message,
                    )
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                    }))

        except WebSocketDisconnect:
            await live_manager.disconnect(session_id, websocket, user.id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as exc:
            import logging
            logging.exception("Jim xatolik (Swallowed Exception): %s", exc)
