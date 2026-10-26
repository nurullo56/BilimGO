from __future__ import annotations
import logging
from typing import Optional
from aiogram import Bot
from core.config import settings

logger = logging.getLogger(__name__)

class AdminNotifier:
    def __init__(self, bot: Optional[Bot] = None) -> None:
        self.bot = bot

    async def send_alert(self, message: str) -> None:
        if not self.bot:
            return
        for admin_id in settings.bot.admin_ids:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message)
            except Exception as e:
                logger.warning("Admin xabarnoma yuborishda xatolik (admin_id=%s): %s", admin_id, e)
