from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
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


def get_mentor_broadcast_target_keyboard(courses: list[dict], counts: dict[str, int]) -> InlineKeyboardMarkup:
    keyboard = []
    
    # 1. Barcha shogirdlarga
    all_cnt = counts.get("all", 0)
    keyboard.append([
        InlineKeyboardButton(
            text=f"👥 Barcha shogirdlarimga ({all_cnt} ta)",
            callback_data="mentor_bcast_target:all",
        )
    ])
    
    # 2. Muayyan kurs bo'yicha
    course_icons = {1: "🚛", 2: "📢", 3: "🎁", 4: "💻", 5: "🇨🇳"}
    for c in courses:
        cid = c["id"]
        c_title = c.get("title", f"Kurs #{cid}")
        cnt = counts.get(f"course_{cid}", 0)
        icon = course_icons.get(cid, "📚")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} Faqat «{c_title}» ({cnt} ta)",
                callback_data=f"mentor_bcast_target:course_{cid}",
            )
        ])
        
    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="mentor_bcast_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mentor_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, barchaga yuborilsin!", callback_data="mentor_bcast_confirm:yes"),
                InlineKeyboardButton(text="✏️ Qayta yozish", callback_data="mentor_bcast_confirm:retry"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="mentor_bcast_cancel")
            ]
        ]
    )


def get_mentor_broadcast_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="mentor_bcast_cancel")]
        ]
    )


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


MENTOR_MENU = get_mentor_menu()
