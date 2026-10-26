from __future__ import annotations
import asyncio
import logging
from typing import Any, List, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from db.repositories.broadcast_repo import BroadcastRepository

logger = logging.getLogger(__name__)

class BroadcastService:
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
    ) -> dict[str, int]:
        total = len(user_ids)
        sent = 0
        failed = 0
        broadcast_id = await self.repo.create_broadcast(admin_id, target_type, total)

        for uid in user_ids:
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

        await self.repo.update_broadcast_status(broadcast_id, sent, failed, "completed")
        return {"total": total, "sent": sent, "failed": failed}
