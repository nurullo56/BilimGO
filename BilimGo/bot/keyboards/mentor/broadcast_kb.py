from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
