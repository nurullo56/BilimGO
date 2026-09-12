from __future__ import annotations

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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


PHONE_REQUEST_KEYBOARD = get_phone_request_keyboard()
STUDENT_MENU = get_student_menu()
