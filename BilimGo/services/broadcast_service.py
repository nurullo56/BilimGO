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

    async def resolve_audience(self, target: str) -> List[int]:
        """Broadcast yuboriladigan foydalanuvchilarning telegram_id ro'yxatini aniqlash."""
        if target == "all":
            return await self.repo.get_active_user_telegram_ids()

        elif target == "mentors":
            return await self.repo.get_active_mentor_telegram_ids()

        elif target.startswith("mentor_direct_"):
            try:
                mid = int(target.replace("mentor_direct_", ""))
                return await self.repo.get_user_telegram_id_by_id(mid)
            except Exception as e:
                logger.error("Target user ids (mentor direct) olishda xato (%s): %s", target, e)
                return []

        elif target.startswith("mentor_") and "_course_" in target:
            try:
                parts = target.split("_")
                mentor_id = int(parts[1])
                cid = int(parts[3])
                return await self.repo.get_mentor_course_audience_telegram_ids(mentor_id, cid)
            except Exception as e:
                logger.error("Target user ids (mentor+course) olishda xato (%s): %s", target, e)
                return []

        elif target.startswith("mentor_"):
            try:
                mentor_id = int(target.replace("mentor_", ""))
                return await self.repo.get_mentor_all_audience_telegram_ids(mentor_id)
            except Exception as e:
                logger.error("Target user ids (mentor all) olishda xato (%s): %s", target, e)
                return []

        elif target.startswith("course_students_"):
            try:
                cid = int(target.replace("course_students_", ""))
                return await self.repo.get_course_students_telegram_ids(cid)
            except Exception as e:
                logger.error("Target user ids (course students) olishda xato (%s): %s", target, e)
                return []

        elif target.startswith("course_all_") or target.startswith("course_"):
            try:
                raw = target.replace("course_all_", "").replace("course_", "")
                cid = int(raw)
                return await self.repo.get_course_all_users_telegram_ids(cid)
            except Exception as e:
                logger.error("Target user ids olishda xato (%s): %s", target, e)
                return []

        return []

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
                    res = progress_callback(idx, total, sent, failed)
                    if asyncio.iscoroutine(res):
                        await res
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
                    res = progress_callback(idx, total, sent, failed)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    pass

        await self.repo.update_broadcast_status(broadcast_id, sent, failed, "completed")
        return {"total": total, "sent": sent, "failed": failed}
