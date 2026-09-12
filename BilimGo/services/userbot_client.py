from __future__ import annotations

import logging
import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class UserbotClient:
    """FastAPI/Worker va Pyrogram Userbot Relay o'rtasidagi ichki HTTP klient."""

    def __init__(self, base_url: str | None = None, secret: str | None = None) -> None:
        self._base_url = (base_url or settings.relay.internal_url).rstrip("/")
        self._secret = secret or settings.relay.internal_secret

    async def send_message(self, recipient_telegram_id: int, text: str) -> bool:
        """Userbot nomidan o'quvchi yoki mentorning shaxsiy Telegramiga xabar yuboradi."""
        url = f"{self._base_url}/send_message"
        headers = {"X-Internal-Secret": self._secret}
        payload = {
            "recipient_telegram_id": recipient_telegram_id,
            "text": text,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("success", False)
                logger.warning(
                    "Userbot /send_message xato javob qaytardi (%s): %s",
                    resp.status_code, resp.text,
                )
                return False
        except Exception as exc:
            logger.error("Userbot relay bilan bog'lanishda xato: %s", exc)
            return False
