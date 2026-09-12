from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
