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


# ----------------- QUOTA MANAGEMENT KEYBOARDS -----------------

def get_quota_mentors_keyboard(mentors: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []
    for m in mentors:
        node_id = m["node_id"]
        m_name = m.get("full_name") or f"Mentor #{m.get('user_id', node_id)}"
        cnt = m.get("student_count", 0)
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🏫 {m_name} (Node #{node_id} • {cnt} ta shogird)",
                callback_data=f"quota_mentor:{node_id}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="quota_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quota_courses_keyboard(
    node_id: int,
    courses: list[dict],
    quotas_map: dict[str, any],
) -> InlineKeyboardMarkup:
    course_icons = {1: "🚛", 2: "📢", 3: "🎁", 4: "💻", 5: "🇨🇳"}
    keyboard = []

    for c in courses:
        cid = c["id"]
        c_title = c.get("title", f"Kurs #{cid}")
        icon = course_icons.get(cid, "📚")

        # Find matching quota
        q_info = ""
        for key, q in quotas_map.items():
            if key.lower() in c_title.lower() or c_title.lower() in key.lower():
                q_info = f" ({q.remaining}/{q.total_quota} ta qoldi)"
                break

        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {c_title}{q_info}",
                callback_data=f"quota_course:{node_id}:{cid}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Mentorlarga qaytish", callback_data="quota_back_mentors"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="quota_cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quota_amount_keyboard(node_id: int, course_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ +5 ta", callback_data=f"quota_add:{node_id}:{course_id}:5"),
                InlineKeyboardButton(text="➕ +10 ta", callback_data=f"quota_add:{node_id}:{course_id}:10"),
                InlineKeyboardButton(text="➕ +20 ta", callback_data=f"quota_add:{node_id}:{course_id}:20"),
            ],
            [
                InlineKeyboardButton(text="➕ +50 ta", callback_data=f"quota_add:{node_id}:{course_id}:50"),
                InlineKeyboardButton(text="➕ +100 ta", callback_data=f"quota_add:{node_id}:{course_id}:100"),
            ],
            [
                InlineKeyboardButton(text="✏️ Boshqa miqdor kiritish", callback_data=f"quota_custom:{node_id}:{course_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Kurslarga qaytish", callback_data=f"quota_mentor:{node_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="quota_cancel"),
            ],
        ]
    )


ADMIN_MENU = get_admin_menu()
