from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from core.config import settings
from db.database import database
from db.repositories.user_repo import UserRepository


class AuthMiddleware(BaseMiddleware):
    """Har bir update uchun users jadvalidan mos yozuvni topadi/yaratadi
    va handlerga `data["user"]` orqali uzatadi. ADMIN_IDS ro'yxatidagi
    telegram_id'lar avtomatik 'admin' roliga ko'tariladi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        repo = UserRepository(database.conn)
        user = await repo.get_or_create(
            telegram_id=tg_user.id,
            full_name=tg_user.full_name,
        )

        if tg_user.id in settings.bot.admin_ids and user.role != "admin":
            await repo.update_role(user.id, "admin")
            user = await repo.get_by_telegram_id(tg_user.id)
            assert user is not None

        data["user"] = user
        return await handler(event, data)