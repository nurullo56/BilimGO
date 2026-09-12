from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
