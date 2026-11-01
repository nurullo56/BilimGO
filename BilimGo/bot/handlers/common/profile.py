"""
Profil va kurs havolalari handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.common._utils import _ROLE_LABELS
from bot.keyboards.common import get_catalog_webapp_keyboard, get_profile_webapp_keyboard
from core.config import settings
from db.repositories.user_repo import User
from services.course_service import CourseService
from services.mentor_service import MentorService
from services.user_service import UserService

logger = logging.getLogger(__name__)
router = Router(name="common_profile")


@router.message(Command("profile"))
@router.message(F.text.in_([
    "👤 Profil va Sozlamalar", "👤 Profil va sozlamalar",
    "👤 Profil", "Profil va sozlamalar", "Profil",
]))
async def handle_profile_menu(message: Message, user: User) -> None:
    current_user = await UserService().get_by_id(user.id) or user

    phone_display = current_user.phone or "Kiritilmagan"
    role_name = _ROLE_LABELS.get(current_user.role, "Talaba")
    name_display = current_user.full_name or "Noma'lum"

    await message.answer(
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"• <b>Ism:</b> {name_display}\n"
        f"• <b>Telegram ID:</b> <code>{current_user.telegram_id}</code>\n"
        f"• <b>Telefon:</b> <code>{phone_display}</code>\n"
        f"• <b>Rolingiz:</b> {role_name}",
        reply_markup=get_profile_webapp_keyboard(),
    )


@router.message(Command("links"))
@router.message(Command("courses"))
@router.message(F.text.in_([
    "🔗 Kurs Havolalari (Referral)", "🔗 Kurs havolalari",
    "🔗 Kurslarim sotuv havolalari", "🔗 Taklif havolam", "🔗 Taklif havolalari",
]))
async def handle_course_links(message: Message, user: User, bot: Bot) -> None:
    is_mentor_or_admin = (
        user.role in ("mentor", "admin", "super_mentor")
        or message.from_user.id in settings.bot.admin_ids
    )

    node = await MentorService().get_mentor_node(user.id)

    if not is_mentor_or_admin and not node:
        await message.answer(
            "📚 <b>Kurslar katalogi</b> orqali o'zingizga qiziq kurslarni tanlab, darslarni boshlashingiz mumkin 👇",
            reply_markup=get_catalog_webapp_keyboard(),
        )
        return

    node_id = node.id if node else 1
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"

    courses = await CourseService().list_published()

    text_lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Havolalaringiz (Sizga birikadi):</b>\n",
        "O'z shogirdlaringizga mos havolani yuboring. O'quvchi havola orqali kirganida, <b>aynan sizning kabinetingizga</b> birikadi:\n",
        "💳 <b>1. ONLINE SOTUV HAVOLALARI (Talaba Click/Payme orqali to'laydi):</b>",
        "<i>Talabaga yuborasiz, u Mini Appda to'lov qilgach darslar ochiladi va sotuv hisobingizga yoziladi:</i>",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        text_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{ref_link}</code>")

    text_lines.append("\n🎁 <b>2. LICHKADA TO'LAGANLAR UCHUN (To'g'ridan-to'g'ri ochiq havola):</b>")
    text_lines.append("<i>Agar talaba pulni kartangizga yoki naqd to'lagan bo'lsa, ushbu havolani bering. Darslar darhol ochiladi:</i>")

    for c in courses:
        open_link = f"https://t.me/{bot_username}?start=open_node_{node_id}_course_{c.id}"
        text_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{open_link}</code>")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    text_lines.append(f"\n🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>")
    text_lines.append("\n💡 <i>Nusxalash uchun istalgan havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(text_lines))
