from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from core.config import settings


def get_admin_menu(webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👑 Admin Paneli (Mini App)",
                    web_app=WebAppInfo(url=f"{url}/?view=catalog&startapp=catalog#catalog"),
                )
            ],
            [
                KeyboardButton(text="📢 Xabar yuborish"),
                KeyboardButton(text="📊 Platforma statistikasi"),
            ],
            [
                KeyboardButton(text="➕ Yangi Mentor qo'shish"),
                KeyboardButton(text="👥 Barcha Mentorlar"),
            ],
            [
                KeyboardButton(text="🎁 Mentorga limit qo'shish"),
                KeyboardButton(text="🔗 Kurslarim sotuv havolalari"),
            ],
            [
                KeyboardButton(text="🔴 Live dars belgilash"),
                KeyboardButton(text="💬 Kabinet va chat"),
            ],
            [
                KeyboardButton(text="👤 Profil va sozlamalar"),
            ],
        ],
        resize_keyboard=True,
    )


def get_admin_inline_webapp(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👑 Admin Paneli (Mini App)",
                    web_app=WebAppInfo(url=f"{url}/?view=catalog&startapp=catalog#catalog"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Xabar yuborish",
                    callback_data="admin_action:broadcast",
                )
            ],
        ]
    )


def get_admin_panel_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Admin Mini App Paneli",
                    web_app=WebAppInfo(url=f"{url}/?view=catalog&startapp=catalog#catalog"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Xabar yuborish",
                    callback_data="admin_action:broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Platforma statistikasi",
                    callback_data="admin_action:stats",
                )
            ],
        ]
    )


ADMIN_MENU = get_admin_menu()
