from __future__ import annotations

import logging
from core.exceptions import AccessDeniedError
from db.repositories.chat_repo import ChatMessage, ChatRepository

logger = logging.getLogger(__name__)


class MessagingService:
    """Kabinet ichki chat xabarlarini boshqarish servisi."""

    def __init__(self, chat_repo: ChatRepository) -> None:
        self._chat_repo = chat_repo

    async def send_message(self, room_id: int, sender_id: int, content: str) -> ChatMessage:
        """Xona a'zosidan yangi xabar yuborish."""
        cleaned_content = content.strip()
        if not cleaned_content:
            raise ValueError("Xabar matni bo'sh bo'lishi mumkin emas")

        is_member = await self._chat_repo.is_room_member(room_id, sender_id)
        if not is_member:
            await self._chat_repo.add_room_member(room_id, sender_id)

        return await self._chat_repo.send_message(room_id, sender_id, cleaned_content)

    async def poll_new_messages(
        self, room_id: int, user_id: int, after_id: int = 0, limit: int = 100
    ) -> list[ChatMessage]:
        """Oxirgi o'qilgan xabardan keyingi yangi xabarlarni olish va last_read ni yangilash."""
        is_member = await self._chat_repo.is_room_member(room_id, user_id)
        if not is_member:
            await self._chat_repo.add_room_member(room_id, user_id)

        messages = await self._chat_repo.list_messages_after(room_id, after_id, limit=limit)
        if messages:
            await self._chat_repo.update_last_read(room_id, user_id, messages[-1].id)
        return messages
