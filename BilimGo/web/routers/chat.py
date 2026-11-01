from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.database import database
from db.repositories.user_repo import UserRepository
from services.messaging_service import MessagingService
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


def _get_messaging_service() -> MessagingService:
    return MessagingService.create_default(database.conn)


@router.post("/rooms/{room_id}/messages", response_model=MessageOut)
async def send_message(
    room_id: str | int,
    body: SendMessageRequest,
    telegram_id: int = Depends(get_current_telegram_id),
    service: MessagingService = Depends(_get_messaging_service),
) -> MessageOut:
    if not body.content.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Xabar matni bo'sh bo'lishi mumkin emas")

    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    res = await service.send_room_message(
        raw_id=room_id,
        user_id=user.id,
        user_name=user.full_name or "Men",
        user_role=user.role or "student",
        content=body.content.strip(),
        reply_to=body.reply_to,
    )
    return MessageOut(**res)


@router.get("/rooms/{room_id}/messages", response_model=list[MessageOut])
async def poll_messages(
    room_id: str | int,
    after_id: str | int = 0,
    telegram_id: int = Depends(get_current_telegram_id),
    service: MessagingService = Depends(_get_messaging_service),
) -> list[MessageOut]:
    user = await UserRepository(database.conn).get_or_create(telegram_id=telegram_id)
    messages = await service.get_room_messages(
        raw_id=room_id,
        user_id=user.id,
        user_tg_id=telegram_id,
        after_id=after_id,
    )
    return [MessageOut(**m) for m in messages]
