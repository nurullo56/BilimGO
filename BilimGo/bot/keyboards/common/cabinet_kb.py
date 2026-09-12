from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.config import settings


def get_cabinets_keyboard(cabinets: list[dict], webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Foydalanuvchining shaxsiy kabinetlari ro'yxati inline klaviaturasi."""
    base_url = webapp_url or settings.webapp.base_url
    if not cabinets:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Mini App Kabinetiga o'tish",
                        web_app=WebAppInfo(url=f"{base_url}/cabinet?view=cabinet&startapp=cabinet#cabinet"),
                    )
                ]
            ]
        )

    _azo = "a\u2019zo"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💬 {c['display_name']} ({c.get('role_in_cabinet') or _azo})",
                    web_app=WebAppInfo(
                        url=f"{base_url}/cabinet/{c['id']}?view=cabinet&cabinet_id={c['id']}&startapp=cabinet_{c['id']}#cabinet-{c['id']}"
                    ),
                )
            ]
            for c in cabinets
        ]
    )
