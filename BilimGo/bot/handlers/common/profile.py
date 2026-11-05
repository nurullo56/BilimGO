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

_CACHED_BOT_USERNAME: str | None = None


async def _resolve_bot_username(bot: Bot) -> str:
    global _CACHED_BOT_USERNAME
    if _CACHED_BOT_USERNAME:
        return _CACHED_BOT_USERNAME
    try:
        bot_info = await bot.get_me()
        if bot_info and bot_info.username:
            _CACHED_BOT_USERNAME = bot_info.username
            return _CACHED_BOT_USERNAME
    except Exception as exc:
        logger.warning("bot.get_me() chaqiruvida tarmoq xatosi: %s, zaxira nom ishlatiladi", exc)
    fallback = getattr(getattr(bot, "_me", None), "username", None)
    if fallback:
        _CACHED_BOT_USERNAME = fallback
        return fallback
    return "BilimGoUz_Bot"


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
    bot_username = await _resolve_bot_username(bot)

    courses = await CourseService().list_published()

    part1_lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Havolalaringiz (1/2):</b>\n",
        "O'z shogirdlaringizga mos havolani yuboring. O'quvchi havola orqali kirganida, <b>aynan sizning kabinetingizga</b> birikadi:\n",
        "💳 <b>1. ONLINE SOTUV HAVOLALARI (Talaba Click/Payme orqali to'laydi):</b>",
        "<i>Talabaga yuborasiz, u Mini Appda to'lov qilgach darslar ochiladi va sotuv hisobingizga yoziladi:</i>",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        part1_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{ref_link}</code>")

    part1_lines.append("\n💡 <i>Nusxalash uchun havola ustiga bir marta bosing.</i>")

    part2_lines = [
        "🎁 <b>Lichkada To'laganlar Uchun Havolalar (2/2):</b>\n",
        "<i>Agar talaba to'lovni kartangizga yoki naqd to'lagan bo'lsa, ushbu havolani bering. Darslar darhol ochiladi:</i>",
    ]

    for c in courses:
        open_link = f"https://t.me/{bot_username}?start=open_node_{node_id}_course_{c.id}"
        part2_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{open_link}</code>")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    part2_lines.append(f"\n🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>")
    part2_lines.append("\n💡 <i>Nusxalash uchun havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(part1_lines))
    await message.answer("\n".join(part2_lines))
