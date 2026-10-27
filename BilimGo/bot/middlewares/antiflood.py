from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from core.config import settings


class AntiFloodMiddleware(BaseMiddleware):
    """
    Foydalanuvchilardan kelayotgan ketma-ket so'rovlarni (spam/flood) cheklovchi middleware.
    Har bir foydalanuvchi belgilangan vaqt oralig'idan (rate_limit) tezroq xabar yuborsa,
    so'rov bloklanadi va foydalanuvchiga ogohlantirish beriladi.
    """

    def __init__(
        self,
        rate_limit: float = 0.8,
        warn_user: bool = True,
        ignore_admins: bool = True,
    ) -> None:
        """
        :param rate_limit: Xabarlar orasidagi minimal vaqt oralig'i (soniyada).
        :param warn_user: Spam holatida ogohlantirish berilsinmi?
        :param ignore_admins: Adminlarga cheklov qo'llanmasinmi?
        """
        self.rate_limit = rate_limit
        self.warn_user = warn_user
        self.ignore_admins = ignore_admins
        # user_id -> oxirgi xabar vaqti (time.monotonic)
        self._last_user_time: Dict[int, float] = {}
        # user_id -> oxirgi ogohlantirish vaqti (bot spamga tushmasligi uchun)
        self._last_warned_time: Dict[int, float] = {}
        self._cleanup_counter: int = 0

    def _cleanup_old_records(self, now: float) -> None:
        """Xotirani tozalash: 10 daqiqadan oshgan eski foydalanuvchi yozuvlarini o'chiradi."""
        cutoff = now - 600.0
        self._last_user_time = {
            uid: ts for uid, ts in self._last_user_time.items() if ts > cutoff
        }
        self._last_warned_time = {
            uid: ts for uid, ts in self._last_warned_time.items() if ts > cutoff
        }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None:
            if hasattr(event, "from_user") and getattr(event, "from_user"):
                tg_user = getattr(event, "from_user")
            elif hasattr(event, "message") and getattr(event, "message") and getattr(event.message, "from_user"):
                tg_user = event.message.from_user
            elif hasattr(event, "callback_query") and getattr(event, "callback_query") and getattr(event.callback_query, "from_user"):
                tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        # Adminlar uchun antiflood cheklovini bekor qilish
        if self.ignore_admins and tg_user.id in settings.bot.admin_ids:
            return await handler(event, data)

        now = time.monotonic()
        user_id = tg_user.id

        # Har 500 ta so'rovda bir marta eski yozuvlarni tozalash (xotira sizib ketishini oldini oladi)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 500:
            self._cleanup_counter = 0
            self._cleanup_old_records(now)

        last_time = self._last_user_time.get(user_id, 0.0)
        elapsed = now - last_time

        if elapsed < self.rate_limit:
            # Foydalanuvchi juda tez so'rov yubormoqda (Flood)
            last_warned = self._last_warned_time.get(user_id, 0.0)

            # Ogohlantirish bot tomonidan har 2 soniyada ko'pi bilan 1 marta yuboriladi
            if self.warn_user and (now - last_warned) > 2.0:
                self._last_warned_time[user_id] = now
                warning_text = "⚠️ <b>Iltimos, xabarlarni juda tez yubormang!</b>\nBiroz kuting."

                try:
                    if isinstance(event, Message):
                        await event.answer(warning_text)
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "⚠️ Iltimos, tugmalarni juda tez bosmang!",
                            show_alert=False,
                        )
                    elif hasattr(event, "message") and getattr(event, "message"):
                        await event.message.answer(warning_text)
                    elif hasattr(event, "callback_query") and getattr(event, "callback_query"):
                        await event.callback_query.answer(
                            "⚠️ Iltimos, tugmalarni juda tez bosmang!",
                            show_alert=False,
                        )
                except Exception:
                    pass

            # So'rovni keyingi handlerga o'tkazmasdan bloklaymiz
            return None

        self._last_user_time[user_id] = now
        return await handler(event, data)
