from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
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


def get_mentor_assignment_courses_keyboard(courses: list[any], target_mentor_id: int) -> InlineKeyboardMarkup:
    """Yangi mentor tayinlashda kursni tanlash inline klaviaturasi."""
    keyboard = []
    course_icons = {1: "🚛", 2: "📢", 3: "🎁", 4: "💻", 5: "🇨🇳"}
    for c in courses:
        cid = getattr(c, "id", None) or c.get("id")
        title = getattr(c, "title", None) or c.get("title", f"Kurs #{cid}")
        icon = course_icons.get(cid, "📚")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {title}",
                callback_data=f"mentor_assign_course:{target_mentor_id}:{cid}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="mentor_assign_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mentor_tariff_keyboard(target_mentor_id: int, course_id: int) -> InlineKeyboardMarkup:
    """Mentorga 15 kunlik bepul tarif paketini tanlash inline klaviaturasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🥉 Standart (Logistika: 20, TgAds: 6, Konkurs: 5, Sayt: 3, Xitoy: 7)",
                    callback_data=f"mentor_set_tariff:{target_mentor_id}:{course_id}:standart",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥈 Pro (Logistika: 45, TgAds: 15, Konkurs: 12, Sayt: 8, Xitoy: 15)",
                    callback_data=f"mentor_set_tariff:{target_mentor_id}:{course_id}:pro",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥇 VIP (Logistika: 100, TgAds: 35, Konkurs: 30, Sayt: 20, Xitoy: 28)",
                    callback_data=f"mentor_set_tariff:{target_mentor_id}:{course_id}:vip",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Kursni qayta tanlash",
                    callback_data="mentor_assign_cancel",
                )
            ],
        ]
    )


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

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💬 {c['display_name']} ({c.get('role_in_cabinet') or 'a’zo'})",
                    web_app=WebAppInfo(
                        url=f"{base_url}/cabinet/{c['id']}?view=cabinet&cabinet_id={c['id']}&startapp=cabinet_{c['id']}#cabinet-{c['id']}"
                    ),
                )
            ]
            for c in cabinets
        ]
    )
