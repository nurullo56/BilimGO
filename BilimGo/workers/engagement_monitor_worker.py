from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from core.config import settings
from db.database import Database
from db.repositories.engagement_repo import EngagementRepository, NudgeRepository
from db.repositories.user_repo import UserRepository
from services.engagement_monitor_service import EngagementMonitorService

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = int(os.getenv("ENGAGEMENT_SCAN_INTERVAL_SECONDS", str(24 * 3600)))
INACTIVITY_THRESHOLD_HOURS = int(os.getenv("ENGAGEMENT_INACTIVITY_HOURS", "24"))


async def run_forever() -> None:
    db = Database(settings.db.path)
    await db.connect()
    await db.run_migrations(settings.db.migrations_dir)

    bot = Bot(token=settings.bot.token)
    nudge_repo = NudgeRepository(db.conn)
    service = EngagementMonitorService(
        EngagementRepository(db.conn), nudge_repo
    )
    user_repo = UserRepository(db.conn)

    logger.info(
        "Engagement monitor ishga tushdi (scan_interval=%ss, threshold=%sh)",
        SCAN_INTERVAL_SECONDS, INACTIVITY_THRESHOLD_HOURS,
    )
    try:
        while True:
            to_send = await service.scan_and_advance(INACTIVITY_THRESHOLD_HOURS)
            for user_id, text in to_send:
                user = await user_repo.get_by_id(user_id)
                if user is None:
                    continue
                name_str = f", {user.full_name}" if user.full_name else ""
                formatted_text = text.format(name=name_str)
                try:
                    await bot.send_message(user.telegram_id, formatted_text)
                    logger.info("Nudge yuborildi: user_id=%s, tg_id=%s", user_id, user.telegram_id)
                except (TelegramForbiddenError, TelegramBadRequest) as tg_err:
                    logger.warning(
                        "Nudge yuborib bo'lmadi (user_id=%s, tg_id=%s): %s. Kampaniya to'xtatildi.",
                        user_id,
                        user.telegram_id,
                        tg_err,
                    )
                    await nudge_repo.stop_campaign(user_id)
                    await user_repo.set_status(user_id, "blocked")
                except Exception:
                    logger.exception("Nudge yuborishda kutilmagan xato: user_id=%s", user_id)
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(run_forever())
