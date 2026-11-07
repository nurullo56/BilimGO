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
                KeyboardButton(text="⚡️ Server yuki va AI tokenlar"),
                KeyboardButton(text="⏳ Kurslar Waitlist (Navbat)"),
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
            [
                InlineKeyboardButton(
                    text="⚡️ Server yuki va AI tokenlar",
                    callback_data="admin_action:infra_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Kurslar Waitlist (Navbat)",
                    callback_data="admin_action:waitlist",
                )
            ],
        ]
    )


def get_admin_courses_waitlist_keyboard(courses: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in courses:
        icon = "⏳" if getattr(c, "is_waitlist", False) else "🟢"
        status_label = "Waitlist" if getattr(c, "is_waitlist", False) else "Sotuvda"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {c.title} — ({status_label})",
                callback_data=f"admin_waitlist:toggle:{c.id}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Admin Menyusiga Qaytish",
            callback_data="admin_action:back_to_menu",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_infra_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    Infratuzilma statistikasi uchun pagination klaviaturasi (⬅️ ❌ ➡️).
    """
    nav_row = []

    # ⬅️ Tugmasi
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_infra:page:{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="admin_infra:noop:first"))

    # ❌ Tugmasi (Yopish)
    nav_row.append(InlineKeyboardButton(text="❌", callback_data="admin_infra:close"))

    # ➡️ Tugmasi
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_infra:page:{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data="admin_infra:noop:last"))

    return InlineKeyboardMarkup(inline_keyboard=[nav_row])


ADMIN_MENU = get_admin_menu()
