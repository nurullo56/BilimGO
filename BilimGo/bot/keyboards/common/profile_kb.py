from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.config import settings


def get_profile_webapp_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Profil menyusi uchun WebApp tugmalari."""
    base_url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Profilni WebApp da ochish",
                    web_app=WebAppInfo(url=f"{base_url}/?view=profile&startapp=profile#profile"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 O'quv platformasi",
                    web_app=WebAppInfo(url=f"{base_url}/?view=catalog&startapp=catalog#catalog"),
                )
            ],
        ]
    )


def get_catalog_webapp_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Katalog WebApp tugmasi."""
    base_url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Kurslar katalogi (Mini App)",
                    web_app=WebAppInfo(url=f"{base_url}/?view=catalog&startapp=catalog#catalog"),
                )
            ]
        ]
    )
