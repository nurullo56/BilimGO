from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_broadcast_target_keyboard(courses: list[dict], counts: dict[str, int]) -> InlineKeyboardMarkup:
    keyboard = []

    # 1. Barcha foydalanuvchilar
    all_count = counts.get("all", 0)
    keyboard.append([
        InlineKeyboardButton(
            text=f"🌐 Barcha foydalanuvchilarga ({all_count} ta)",
            callback_data="bcast_target:all",
        )
    ])

    # 2. Barcha Mentorlarning O'ZIGA
    mentors_count = counts.get("mentors", 0)
    keyboard.append([
        InlineKeyboardButton(
            text=f"🎓 Barcha Mentorlarga (Faqat mentorlar o'ziga) ({mentors_count} ta)",
            callback_data="bcast_target:mentors",
        )
    ])

    # 3. Muayyan Mentor yoki uning shogirdlariga saralash
    keyboard.append([
        InlineKeyboardButton(
            text="👤 Alohida Mentor tanlash (o'ziga yoki shogirdlariga)...",
            callback_data="bcast_target:choose_mentor",
        )
    ])

    # 4. Kurslar bo'yicha alohida
    course_icons = {
        1: "🚛",
        2: "📢",
        3: "🎁",
        4: "💻",
        5: "🇨🇳",
    }
    for c in courses:
        cid = c["id"]
        c_title = c.get("title", f"Kurs #{cid}")
        cnt = counts.get(f"course_{cid}", 0)
        icon = course_icons.get(cid, "📚")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {c_title} ({cnt} ta)",
                callback_data=f"bcast_target:course_{cid}",
            )
        ])

    # Bekor qilish
    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast_cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_mentors_keyboard(mentors: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []
    all_mentors_cnt = len(mentors)

    # 1. Barcha mentorlarga bir vaqtda xabar
    keyboard.append([
        InlineKeyboardButton(
            text=f"🎓 BARCHA Mentorlarning o'ziga yuborish ({all_mentors_cnt} ta)",
            callback_data="bcast_target:mentors",
        )
    ])

    # 2. Alohida mentorlar
    for m in mentors:
        m_id = m["id"]
        m_name = m.get("full_name") or f"Mentor #{m_id}"
        cnt = m.get("students_count", 0)
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🏫 {m_name} ({cnt} ta shogirdi bor)",
                callback_data=f"bcast_mentor:{m_id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bcast_back_target"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_mentor_courses_keyboard(
    mentor_id: int, mentor_name: str, courses: list[dict], counts: dict[str, int]
) -> InlineKeyboardMarkup:
    keyboard = []
    all_cnt = counts.get("mentor_all", 0)

    # 1. Faqat shu mentorning O'ZIGA xabar yuborish
    keyboard.append([
        InlineKeyboardButton(
            text=f"✉️ Faqat {mentor_name}ning O'ZIGA xabar (1 ta)",
            callback_data=f"bcast_target:mentor_direct_{mentor_id}",
        )
    ])

    # 2. Mentorning BARCHA shogirdlariga
    keyboard.append([
        InlineKeyboardButton(
            text=f"👥 {mentor_name}ning BARCHA shogirdlariga ({all_cnt} ta)",
            callback_data=f"bcast_target:mentor_{mentor_id}",
        )
    ])

    # 3. Muayyan kurs bo'yicha shogirdlariga
    course_icons = {1: "🚛", 2: "📢", 3: "🎁", 4: "💻", 5: "🇨🇳"}
    for c in courses:
        cid = c["id"]
        c_title = c.get("title", f"Kurs #{cid}")
        cnt = counts.get(f"mentor_course_{cid}", 0)
        icon = course_icons.get(cid, "📚")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} Faqat «{c_title}» shogirdlariga ({cnt} ta)",
                callback_data=f"bcast_target:mentor_{mentor_id}_course_{cid}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Mentorlar ro'yxatiga", callback_data="bcast_target:choose_mentor"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, yuborilsin!", callback_data="bcast_confirm:yes"),
                InlineKeyboardButton(text="✏️ Qayta yozish", callback_data="bcast_confirm:retry"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast_cancel")
            ]
        ]
    )


def get_broadcast_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcast_cancel")]
        ]
    )
