from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.exceptions import AccessDeniedError
from db.database import database
from db.repositories.chat_repo import ChatRepository
from services.messaging_service import MessagingService
from db.repositories.user_repo import UserRepository
from web.dependencies.auth import get_current_telegram_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatReplyInfo(BaseModel):
    message_id: str | int | None = None
    sender_name: str | None = None
    content: str | None = None


class SendMessageRequest(BaseModel):
    content: str
    reply_to: ChatReplyInfo | None = None


class MessageOut(BaseModel):
    id: str | int
    sender_id: int
    sender_name: str | None = "Foydalanuvchi"
    content: str
    sent_at: str
    is_me: bool = False
    role: str = "student"
    reply_to: ChatReplyInfo | None = None


async def _resolve_room_id(raw_id: str | int, user_id: int) -> int:
    conn = database.conn
    try:
        clean_num = int(str(raw_id).replace("cab-", "").replace("room-", "").replace("msg-", ""))
    except ValueError:
        clean_num = 1

    # 1. Check if room with id = clean_num exists
    cursor = await conn.execute("SELECT id FROM chat_rooms WHERE id = ?", (clean_num,))
    row = await cursor.fetchone()
    if row:
        room_id = row["id"]
    else:
        # 2. Check if room for cabinet_id = clean_num exists
        cursor2 = await conn.execute("SELECT id FROM chat_rooms WHERE cabinet_id = ? LIMIT 1", (clean_num,))
        row2 = await cursor2.fetchone()
        if row2:
            room_id = row2["id"]
        else:
            # 3. Create room for this cabinet
            cursor3 = await conn.execute(
                "INSERT INTO chat_rooms (cabinet_id, course_id) VALUES (?, 1)",
                (clean_num,),
            )
            await conn.commit()
            room_id = cursor3.lastrowid

    # Auto ensure user is in chat_room_members
    await conn.execute(
        "INSERT INTO chat_room_members (room_id, user_id) VALUES (?, ?) ON CONFLICT(room_id, user_id) DO NOTHING",
        (room_id, user_id),
    )
    await conn.commit()
    return room_id


@router.post("/rooms/{room_id}/messages", response_model=MessageOut)
async def send_message(
    room_id: str | int,
    body: SendMessageRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> MessageOut:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    actual_room_id = await _resolve_room_id(room_id, user.id)

    if not body.content.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Xabar matni bo'sh bo'lishi mumkin emas")

    messaging_service = MessagingService(ChatRepository(conn))
    msg = await messaging_service.send_message(actual_room_id, user.id, body.content.strip())

    return MessageOut(
        id=msg.id,
        sender_id=user.id,
        sender_name=user.full_name or "Men",
        content=msg.content,
        sent_at=msg.sent_at,
        is_me=True,
        role=user.role or "student",
        reply_to=body.reply_to,
    )


@router.get("/rooms/{room_id}/messages", response_model=list[MessageOut])
async def poll_messages(
    room_id: str | int,
    after_id: str | int = 0,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[MessageOut]:
    conn = database.conn
    user = await UserRepository(conn).get_or_create(telegram_id=telegram_id)
    actual_room_id = await _resolve_room_id(room_id, user.id)

    try:
        clean_after = int(str(after_id).replace("msg-", ""))
    except ValueError:
        clean_after = 0

    cursor = await conn.execute(
        """
        SELECT m.id, m.sender_id, m.content, m.sent_at,
               u.full_name, u.role, u.telegram_id
        FROM chat_messages m
        JOIN users u ON u.id = m.sender_id
        WHERE m.room_id = ? AND m.id > ?
        ORDER BY m.id ASC
        LIMIT 100
        """,
        (actual_room_id, clean_after),
    )
    rows = await cursor.fetchall()

    results = []
    for r in rows:
        results.append(
            MessageOut(
                id=r["id"],
                sender_id=r["sender_id"],
                sender_name=r["full_name"] or "Foydalanuvchi",
                content=r["content"],
                sent_at=r["sent_at"],
                is_me=(r["telegram_id"] == telegram_id),
                role=r["role"] or "student",
            )
        )
    return results
