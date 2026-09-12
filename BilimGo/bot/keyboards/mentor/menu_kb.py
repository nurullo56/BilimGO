from __future__ import annotations

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from core.config import settings


def get_mentor_menu(webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👥 Mentor Kabineti (Mini App)",
                    web_app=WebAppInfo(url=f"{url}/cabinet?view=cabinet&startapp=cabinet#cabinet"),
                )
            ],
            [
                KeyboardButton(text="📢 Shogirdlarimga xabar"),
                KeyboardButton(text="👥 Mening talabalarim"),
            ],
            [
                KeyboardButton(text="🔗 Kurslarim sotuv havolalari"),
                KeyboardButton(text="📊 Statistika"),
            ],
            [KeyboardButton(text="🔴 Live dars belgilash"), KeyboardButton(text="💬 Kabinet va chat")],
            [KeyboardButton(text="👤 Profil va Sozlamalar"), KeyboardButton(text="💳 Ulangan karta (Avto-to'lov)")],
        ],
        resize_keyboard=True,
    )


def get_mentor_inline_webapp(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Mentor Kabineti & Chat (Mini App)",
                    web_app=WebAppInfo(url=f"{url}/cabinet?view=cabinet&startapp=cabinet#cabinet"),
                )
            ]
        ]
    )


MENTOR_MENU = get_mentor_menu()
