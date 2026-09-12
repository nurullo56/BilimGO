from __future__ import annotations

from core.exceptions import AccessDeniedError
from db.repositories.chat_repo import ChatMessage, ChatRepository


class MessagingService:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._chat_repo = chat_repo

    async def send_message(self, room_id: int, sender_id: int, content: str) -> ChatMessage:
        if not content.strip():
            raise ValueError("Xabar matni bo'sh bo'lishi mumkin emas")

        is_member = await self._chat_repo.is_room_member(room_id, sender_id)
        if not is_member:
            raise AccessDeniedError(
                f"Foydalanuvchi {sender_id} {room_id}-xona a'zosi emas"
            )
        return await self._chat_repo.send_message(room_id, sender_id, content.strip())

    async def poll_new_messages(
        self, room_id: int, user_id: int, after_id: int
    ) -> list[ChatMessage]:
        is_member = await self._chat_repo.is_room_member(room_id, user_id)
        if not is_member:
            raise AccessDeniedError(
                f"Foydalanuvchi {user_id} {room_id}-xona a'zosi emas"
            )

        messages = await self._chat_repo.list_messages_after(room_id, after_id)
        if messages:
            await self._chat_repo.update_last_read(room_id, user_id, messages[-1].id)
        return messages
