from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from core.config import settings


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Yangi yoki telefonini kiritmagan foydalanuvchilar uchun bir martalik tugma."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


PHONE_REQUEST_KEYBOARD = get_phone_request_keyboard()


def get_student_menu(webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 O'quv platformasi (Mini App)", web_app=WebAppInfo(url=f"{url}/?view=catalog&startapp=catalog#catalog"))],
            [KeyboardButton(text="📚 Kurslar katalogi"), KeyboardButton(text="🎓 Mening kurslarim")],
            [KeyboardButton(text="💬 Kabinet va chat"), KeyboardButton(text="👤 Profil va Sozlamalar")],
        ],
        resize_keyboard=True,
    )


def get_student_inline_webapp(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Darslarni boshlash (Mini App)",
                    web_app=WebAppInfo(url=f"{url}/?view=catalog&startapp=catalog#catalog"),
                )
            ]
        ]
    )


def get_course_list_keyboard(courses: list[any]) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati inline klaviaturasi."""
    rows = [
        [InlineKeyboardButton(text=f"{c.title} — {c.base_price:,.0f} so'm", callback_data=f"course:{c.id}")]
        for c in courses
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_course_detail_keyboard(course_id: int, webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari va xarid qilish (Click/Payme) inline klaviaturasi."""
    base_url = webapp_url or settings.webapp.base_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Kurs va Video Darslar (Mini App)",
                    web_app=WebAppInfo(url=f"{base_url}/course/{course_id}?view=course&course_id={course_id}&startapp=course_{course_id}#course-{course_id}"),
                )
            ],
            [
                InlineKeyboardButton(text="💳 Click orqali xarid", callback_data=f"buy:{course_id}:click"),
                InlineKeyboardButton(text="💳 Payme orqali xarid", callback_data=f"buy:{course_id}:payme"),
            ],
        ]
    )


def get_checkout_payment_keyboard(provider: str, checkout_url: str) -> InlineKeyboardMarkup:
    """To'lov havolasiga o'tish tugmasi."""
    provider_title = provider.capitalize()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 {provider_title} orqali to'lash", url=checkout_url)]
        ]
    )


def get_my_courses_progress_keyboard(rows: list[any], webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """O'quvchining faol kurslari va progress foizi inline klaviaturasi."""
    base_url = webapp_url or settings.webapp.base_url
    keyboard_buttons = []
    for row in rows:
        cid = row["id"]
        title = row["title"]
        total = row["total_lessons"] or 0
        completed = row["completed_lessons"] or 0
        percent = int((completed / total * 100)) if total > 0 else 0
        course_url = f"{base_url}/?startapp=course_{cid}#course-{cid}"
        keyboard_buttons.append(
            [InlineKeyboardButton(text=f"▶️ {title} ({percent}%)", web_app=WebAppInfo(url=course_url))]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


STUDENT_MENU = get_student_menu()
