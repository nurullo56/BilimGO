from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.config import settings


def get_direct_course_keyboard(course_id: int, webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Yangi o'quvchi taklif havolasi bilan kirganda to'g'ridan-to'g'ri kursga o'tish tugmasi."""
    base_url = webapp_url or settings.webapp.base_url
    url = f"{base_url}/?startapp=course_{course_id}#course-{course_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Darslarni boshlash (Mini App)",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )
