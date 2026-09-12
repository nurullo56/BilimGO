"""
Profil va kurs havolalari handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.common._utils import _ROLE_LABELS
from bot.keyboards.common_kb import get_catalog_webapp_keyboard, get_profile_webapp_keyboard
from core.config import settings
from db.database import database
from db.repositories.course_repo import CourseRepository
from db.repositories.user_repo import User, UserRepository

logger = logging.getLogger(__name__)
router = Router(name="common_profile")


@router.message(Command("profile"))
@router.message(F.text.in_([
    "👤 Profil va Sozlamalar", "👤 Profil va sozlamalar",
    "👤 Profil", "Profil va sozlamalar", "Profil",
]))
async def handle_profile_menu(message: Message, user: User) -> None:
    conn = database.conn
    user_repo = UserRepository(conn)
    current_user = await user_repo.get_by_id(user.id) or user

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
    conn = database.conn
    is_mentor_or_admin = (
        user.role in ("mentor", "admin", "super_mentor")
        or message.from_user.id in settings.bot.admin_ids
    )

    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? ORDER BY id ASC LIMIT 1",
        (user.id,),
    )
    node_row = await cursor.fetchone()

    if not is_mentor_or_admin and not node_row:
        await message.answer(
            "📚 <b>Kurslar katalogi</b> orqali o'zingizga qiziq kurslarni tanlab, darslarni boshlashingiz mumkin 👇",
            reply_markup=get_catalog_webapp_keyboard(),
        )
        return

    node_id = node_row["id"] if node_row else 1
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"

    course_repo = CourseRepository(conn)
    courses = await course_repo.list_published()

    text_lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Sotuv Havolalaringiz (Sizga birikadi):</b>\n",
        "O'quvchi ushbu havolalar orqali kirganida, <b>aynan sizning kabinetingizga shogird bo'lib birikadi</b> "
        "va unga faqat tanlangan kurs ochiladi:\n",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        text_lines.append(f"📌 <b>{c.title}</b>:")
        text_lines.append(f"👉 <code>{ref_link}</code>\n")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    text_lines.append(f"🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>\n")
    text_lines.append("💡 <i>Nusxalash uchun istalgan havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(text_lines))
