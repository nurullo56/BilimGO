from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from db.repositories.broadcast_repo import BroadcastRepository

logger = logging.getLogger(__name__)


class BroadcastService:
    """Xabarnoma (broadcast) tarqatish servisi."""

    def __init__(self, broadcast_repo: Optional[BroadcastRepository] = None) -> None:
        self.repo = broadcast_repo or BroadcastRepository()

    async def execute_broadcast(
        self,
        bot: Bot,
        admin_id: int,
        target_type: str,
        user_ids: List[int],
        text: Optional[str] = None,
        photo_id: Optional[str] = None,
        reply_markup: Any = None,
        progress_callback: Optional[Callable[[int, int, int], Any]] = None,
    ) -> dict[str, int]:
        """Matn yoki rasm xabarlarini foydalanuvchilar ro'yxatiga yuboradi."""
        total = len(user_ids)
        sent = 0
        failed = 0
        broadcast_id = await self.repo.create_broadcast(admin_id, target_type, total)

        for idx, uid in enumerate(user_ids, 1):
            try:
                if photo_id:
                    await bot.send_photo(chat_id=uid, photo=photo_id, caption=text, reply_markup=reply_markup)
                elif text:
                    await bot.send_message(chat_id=uid, text=text, reply_markup=reply_markup)
                sent += 1
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    if photo_id:
                        await bot.send_photo(chat_id=uid, photo=photo_id, caption=text, reply_markup=reply_markup)
                    elif text:
                        await bot.send_message(chat_id=uid, text=text, reply_markup=reply_markup)
                    sent += 1
                except Exception:
                    failed += 1
            except (TelegramForbiddenError, TelegramAPIError, Exception) as exc:
                logger.debug("Xabar yuborishda xatolik uid=%s: %s", uid, exc)
                failed += 1

            if progress_callback and (idx % 25 == 0 or idx == total):
                try:
                    await progress_callback(idx, total, sent)
                except Exception:
                    pass

        await self.repo.update_broadcast_status(broadcast_id, sent, failed, "completed")
        return {"total": total, "sent": sent, "failed": failed}

    async def copy_broadcast(
        self,
        bot: Bot,
        admin_id: int,
        target_type: str,
        user_ids: List[int],
        from_chat_id: int,
        message_id: int,
        progress_callback: Optional[Callable[[int, int, int], Any]] = None,
    ) -> dict[str, int]:
        """Har qanday turdagi (video, audio, fayl, text) xabarni nusxalab barchaga yuboradi."""
        total = len(user_ids)
        sent = 0
        failed = 0
        broadcast_id = await self.repo.create_broadcast(admin_id, target_type, total)

        for idx, uid in enumerate(user_ids, 1):
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
                sent += 1
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    await bot.copy_message(
                        chat_id=uid,
                        from_chat_id=from_chat_id,
                        message_id=message_id,
                    )
                    sent += 1
                except Exception:
                    failed += 1
            except (TelegramForbiddenError, TelegramAPIError, Exception) as exc:
                logger.debug("Broadcast copy xatolik uid=%s: %s", uid, exc)
                failed += 1

            if progress_callback and (idx % 25 == 0 or idx == total):
                try:
                    await progress_callback(idx, total, sent)
                except Exception:
                    pass

        await self.repo.update_broadcast_status(broadcast_id, sent, failed, "completed")
        return {"total": total, "sent": sent, "failed": failed}
