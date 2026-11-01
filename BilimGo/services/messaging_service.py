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

    @classmethod
    def create_default(cls, conn=None) -> "MessagingService":
        """Yagona markazlashgan MessagingService fabrikasi."""
        from db.database import database
        from db.repositories.chat_repo import ChatRepository

        c = conn or database.conn
        return cls(chat_repo=ChatRepository(c))

    def parse_clean_id(self, raw_id: str | int) -> int:
        """Har xil prefikslarga ega (cab-1, room-1, msg-1) ID larni toza integerga aylantiradi."""
        try:
            return int(str(raw_id).replace("cab-", "").replace("room-", "").replace("msg-", ""))
        except ValueError:
            return 1

    async def resolve_room(self, raw_id: str | int, user_id: int) -> int:
        """Xona yoki kabinet ID sini to'g'ri xona ID siga yechadi va a'zolikni ta'minlaydi."""
        clean_num = self.parse_clean_id(raw_id)
        return await self._chat_repo.resolve_or_create_room(clean_num, user_id)

    async def get_room_messages(
        self, raw_id: str | int, user_id: int, user_tg_id: int, after_id: str | int = 0
    ) -> list[dict]:
        """Xonadagi barcha xabarlarni foydalanuvchilar ma'lumotlari bilan qaytaradi."""
        actual_room_id = await self.resolve_room(raw_id, user_id)
        clean_after = self.parse_clean_id(after_id) if after_id else 0

        rows = await self._chat_repo.list_messages_with_users(actual_room_id, clean_after, limit=100)
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "sender_id": r["sender_id"],
                "sender_name": r["full_name"] or "Foydalanuvchi",
                "content": r["content"],
                "sent_at": r["sent_at"],
                "is_me": (r["telegram_id"] == user_tg_id),
                "role": r["role"] or "student",
            })
        return results

    async def send_room_message(
        self,
        raw_id: str | int,
        user_id: int,
        user_name: str,
        user_role: str,
        content: str,
        reply_to: dict | None = None,
    ) -> dict:
        """Xonaga yangi xabar yozadi va formatlangan natijani qaytaradi."""
        actual_room_id = await self.resolve_room(raw_id, user_id)
        msg = await self.send_message(actual_room_id, user_id, content)

        return {
            "id": msg.id,
            "sender_id": user_id,
            "sender_name": user_name or "Men",
            "content": msg.content,
            "sent_at": msg.sent_at,
            "is_me": True,
            "role": user_role or "student",
            "reply_to": reply_to,
        }

