from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.handlers.admin.broadcast import router as admin_broadcast_router
from bot.handlers.admin.quota import router as admin_quota_router
from bot.handlers.admin.stats import router as admin_stats_router
from bot.handlers.admin.mentor_approval import router as mentor_approval_router
from bot.handlers.common.cabinet_link import router as cabinet_link_router
from bot.handlers.common.mentor_add import router as mentor_add_router
from bot.handlers.common.profile import router as profile_router
from bot.handlers.common.start import router as registration_router
from bot.handlers.mentor.broadcast import router as mentor_broadcast_router
from bot.handlers.mentor.cabinet import router as mentor_cabinet_router
from bot.handlers.mentor.live import router as mentor_live_router
from bot.handlers.student.catalog import router as student_catalog_router
from bot.handlers.student.progress import router as student_progress_router
from bot.handlers.student.purchase import router as student_purchase_router
from bot.middlewares.antiflood import AntiFloodMiddleware
from bot.middlewares.auth import AuthMiddleware
from core.config import settings
from db.database import database

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    bot_info = await bot.get_me()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        f"🟢 <b>BilimGo Bot muvaffaqiyatli ishga tushdi!</b>\n\n"
        f"🤖 <b>Bot:</b> @{bot_info.username} (<code>{bot_info.id}</code>)\n"
        f"🌐 <b>Mini App WebApp:</b> {settings.webapp.base_url}\n"
        f"🕒 <b>Vaqt:</b> {now_str}\n"
        f"⚡️ <b>Holat:</b> Barcha servislar onlayn va xizmatga tayyor!"
    )
    
    reply_markup = None
    if settings.webapp.base_url and settings.webapp.base_url.startswith("https://"):
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Mini Appni ochish",
                        web_app=WebAppInfo(url=settings.webapp.base_url),
                    )
                ]
            ]
        )

    for admin_id in settings.bot.admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=msg, reply_markup=reply_markup)
            logger.info("Adminga startup xabari yuborildi: %s", admin_id)
        except Exception as e:
            logger.warning("Adminga startup xabari yuborishda xatolik (%s): %s", admin_id, e)


async def on_shutdown(bot: Bot) -> None:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        f"🛑 <b>BilimGo Bot to'xtatildi!</b>\n\n"
        f"🕒 <b>Vaqt:</b> {now_str}\n"
        f"⚠️ <b>Holat:</b> Servis oflayn holatga o'tdi."
    )
    for admin_id in settings.bot.admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=msg)
            logger.info("Adminga shutdown xabari yuborildi: %s", admin_id)
        except Exception as e:
            logger.warning("Adminga shutdown xabari yuborishda xatolik (%s): %s", admin_id, e)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(AntiFloodMiddleware())
    dp.update.middleware(AuthMiddleware())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(admin_stats_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(admin_quota_router)
    dp.include_router(registration_router)
    dp.include_router(mentor_add_router)
    dp.include_router(mentor_approval_router)
    dp.include_router(profile_router)
    dp.include_router(cabinet_link_router)
    dp.include_router(student_catalog_router)
    dp.include_router(student_purchase_router)
    dp.include_router(student_progress_router)
    dp.include_router(mentor_cabinet_router)
    dp.include_router(mentor_broadcast_router)
    dp.include_router(mentor_live_router)
    return dp


async def main() -> None:
    await database.connect()
    await database.run_migrations(settings.db.migrations_dir)

    bot = Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    try:
        logger.info("BilimGo bot polling boshlanmoqda...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
