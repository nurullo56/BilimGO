from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def get_live_course_select_keyboard(courses: list[any]) -> InlineKeyboardMarkup:
    """Jonli dars (Live) belgilash uchun kurs tanlash inline klaviaturasi."""
    buttons = []
    for c in courses:
        cid = getattr(c, "id", None) or c["id"]
        title = getattr(c, "title", None) or c["title"]
        buttons.append([InlineKeyboardButton(text=f"📚 {title}", callback_data=f"live_course:{cid}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="live_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_live_session_scheduled_keyboard(session_id: str, webapp_url: str) -> InlineKeyboardMarkup:
    """Belgilangan live session uchun boshqaruv tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎥 Live efirni boshlash",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Talabalarga xabar yuborish",
                    callback_data=f"live_notify:{session_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"live_cancel_session:{session_id}",
                )
            ],
        ]
    )
