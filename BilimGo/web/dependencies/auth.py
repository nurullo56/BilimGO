from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)


def _compute_hash(init_data: str, bot_token: str) -> tuple[str, dict[str, str]]:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", "")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(pairs.items())
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=bot_token.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        key=secret_key, msg=data_check_string.encode("utf-8"), digestmod=hashlib.sha256
    ).hexdigest()
    return computed_hash, {"received_hash": received_hash, **pairs}


async def get_current_telegram_id(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_telegram_user_id: str | None = Header(default=None, alias="X-Telegram-User-Id"),
) -> int:
    """FastAPI dependency — WebApp initData yoki foydalanuvchi ID sini xavfsiz aniqlaydi."""

    # 1. If Telegram InitData is passed (Production and MiniApp standard)
    if x_telegram_init_data:
        try:
            computed_hash, parsed = _compute_hash(x_telegram_init_data, settings.bot.token)
            received_hash = parsed.get("received_hash", "")
            is_valid = bool(received_hash and hmac.compare_digest(computed_hash, received_hash))

            user_raw = parsed.get("user")
            if user_raw:
                user_data = json.loads(user_raw)
                if "id" in user_data:
                    user_id = int(user_data["id"])
                    if is_valid or settings.debug:
                        if not is_valid and settings.debug:
                            logger.warning(
                                "DEBUG: Telegram initData imzosi mos kelmadi, lekin DEBUG rejimida user_id=%s qabul qilindi",
                                user_id,
                            )
                        return user_id
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Telegram initData imzosi haqiqiy emas",
                    )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Telegram initData tahlilida xatolik: %s", exc)
            if not settings.debug:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Telegram initData noto'g'ri formatda",
                )

    # 2. If explicit X-Telegram-User-Id header is passed (Faqat DEBUG rejimida)
    if x_telegram_user_id and settings.debug:
        try:
            return int(x_telegram_user_id)
        except (ValueError, TypeError):
            pass

    # 3. Fallback: Faqat DEBUG rejimida test user ID qaytariladi
    if settings.debug:
        fallback_id = settings.bot.admin_ids[0] if settings.bot.admin_ids else 1467675358
        logger.debug("DEBUG: Auth header berilmadi, fallback user_id=%s ishlatilmoqda", fallback_id)
        return fallback_id

    # 4. Production rejimida ruxsatsiz so'rovlarni qat'iy to'xtatish (401)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autentifikatsiya talab qilinadi (Telegram WebApp initData topilmadi)",
    )
