from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from aiogram import Bot
from core.config import settings

logger = logging.getLogger(__name__)


class AdminNotifier:
    """Administratorlar va Telegram Forum Supergroup (topics) uchun yagona xabarnoma servisi."""

    def __init__(self, bot: Optional[Bot] = None) -> None:
        self.bot = bot

    async def _send_via_httpx(
        self,
        chat_id: int,
        text: str,
        message_thread_id: Optional[int] = None,
        reply_markup: Any = None,
        photo_id: Optional[str] = None,
    ) -> bool:
        """Bot instansi bo'lmaganda (masalan, FastAPI routerlarida) to'g'ridan-to'g'ri Telegram API orqali xabar yuborish."""
        token = settings.bot.token
        if not token:
            logger.warning("AdminNotifier: BOT_TOKEN topilmadi.")
            return False

        try:
            markup_dict = None
            if reply_markup is not None:
                if hasattr(reply_markup, "model_dump"):
                    markup_dict = reply_markup.model_dump(exclude_none=True)
                elif hasattr(reply_markup, "dict"):
                    markup_dict = reply_markup.dict(exclude_none=True)
                elif isinstance(reply_markup, dict):
                    markup_dict = reply_markup

            async with httpx.AsyncClient(timeout=10.0) as client:
                if photo_id:
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    payload: dict[str, Any] = {
                        "chat_id": chat_id,
                        "photo": photo_id,
                        "caption": text,
                        "parse_mode": "HTML",
                    }
                else:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                    }

                if message_thread_id:
                    payload["message_thread_id"] = message_thread_id
                if markup_dict:
                    payload["reply_markup"] = markup_dict

                resp = await client.post(url, json=payload)
                return resp.status_code == 200
        except Exception as ex:
            logger.warning("AdminNotifier HTTPX orqali yuborishda xatolik (%s): %s", chat_id, ex)
            return False

    async def send_to_topic(
        self,
        topic_id: int,
        text: str,
        reply_markup: Any = None,
        photo_id: Optional[str] = None,
    ) -> bool:
        """Guruhdagi muayyan mavzuga (topic) xabar yuborish, agar xatolik bo'lsa adminga to'g'ridan-to'g'ri DM orqali yuborish."""
        group_id = settings.bot.group_id
        sent = False

        if group_id:
            try:
                if self.bot:
                    if photo_id:
                        await self.bot.send_photo(
                            chat_id=group_id,
                            photo=photo_id,
                            caption=text,
                            message_thread_id=topic_id,
                            reply_markup=reply_markup,
                            parse_mode="HTML",
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=group_id,
                            text=text,
                            message_thread_id=topic_id,
                            reply_markup=reply_markup,
                            parse_mode="HTML",
                        )
                    sent = True
                    logger.info("Xabarnoma Supermentor guruhiga (Topic %s) yuborildi.", topic_id)
                else:
                    sent = await self._send_via_httpx(
                        chat_id=group_id,
                        text=text,
                        message_thread_id=topic_id,
                        reply_markup=reply_markup,
                        photo_id=photo_id,
                    )
            except Exception as e:
                logger.warning("Supermentor guruhiga (Topic %s) xabar yuborishda xatolik: %s", topic_id, e)

        # Agar guruhga yuborilmasa yoki guruh sozlanmagan bo'lsa, zaxira sifatida adminlarning shaxsiyiga yuboriladi
        if not sent:
            for admin_id in settings.bot.admin_ids:
                try:
                    if self.bot:
                        if photo_id:
                            await self.bot.send_photo(
                                chat_id=admin_id,
                                photo=photo_id,
                                caption=text,
                                reply_markup=reply_markup,
                                parse_mode="HTML",
                            )
                        else:
                            await self.bot.send_message(
                                chat_id=admin_id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode="HTML",
                            )
                    else:
                        await self._send_via_httpx(
                            chat_id=admin_id,
                            text=text,
                            reply_markup=reply_markup,
                            photo_id=photo_id,
                        )
                    logger.info("Adminga zaxira xabarnoma yuborildi: %s", admin_id)
                except Exception as ex:
                    logger.warning("Adminga xabarnoma yuborishda xatolik (%s): %s", admin_id, ex)

        return sent

    # ========== KATEGORIYALANGAN MAVZULAR (TOPICS) ==========

    async def send_mentor_application(self, text: str, reply_markup: Any = None) -> bool:
        """1. Mentorlik arizalari (Topic 2)."""
        topic_id = settings.bot.topic_mentor_apps
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_payment_receipt(
        self, photo_id: str, caption: str, reply_markup: Any = None
    ) -> bool:
        """2. To'lov cheklari va kvitansiyalari (Topic 4)."""
        topic_id = settings.bot.topic_payment_receipts
        return await self.send_to_topic(topic_id, caption, reply_markup=reply_markup, photo_id=photo_id)

    async def send_payment_alert(self, text: str, reply_markup: Any = None) -> bool:
        """3. Avtomatik to'lovlar (Click / Payme / Sotuvlar) (Topic 4)."""
        topic_id = settings.bot.topic_payment_receipts
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_statistics_alert(self, text: str, reply_markup: Any = None) -> bool:
        """4. Statistika va daromad hisobotlari (Topic 6)."""
        topic_id = settings.bot.topic_statistics
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_user_alert(self, text: str, reply_markup: Any = None) -> bool:
        """5. Mentorlar va o'quvchilar / Yangi ro'yxatdan o'tganlar (Topic 8)."""
        topic_id = settings.bot.topic_users
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_waitlist_alert(self, text: str, reply_markup: Any = None) -> bool:
        """6. Kutish ro'yxati (Waitlist) arizalari (Topic 8)."""
        topic_id = settings.bot.topic_users
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_feedback_alert(self, text: str, reply_markup: Any = None) -> bool:
        """7. Fikr-mulohazalar va takliflar (Topic 8)."""
        topic_id = settings.bot.topic_users
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_system_alert(self, text: str, reply_markup: Any = None) -> bool:
        """8. Tizim xatolari va ogohlantirishlar (Topic 10)."""
        topic_id = settings.bot.topic_system_alerts
        return await self.send_to_topic(topic_id, text, reply_markup=reply_markup)

    async def send_alert(
        self, message: str, reply_markup: Any = None, topic_id: Optional[int] = None
    ) -> None:
        """Umumiy xabarnoma (standart holatda Topic 10 yoki barcha adminlarga)."""
        target_topic = topic_id or settings.bot.topic_system_alerts
        await self.send_to_topic(target_topic, message, reply_markup=reply_markup)


admin_notifier = AdminNotifier()
