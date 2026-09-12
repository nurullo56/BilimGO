"""
Admin statistika va /admin buyrug'i handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.admin._admin_db import get_courses_and_counts
from bot.keyboards.admin_kb import ADMIN_MENU, get_admin_panel_keyboard
from core.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_stats")


@router.message(Command("admin"))
async def handle_admin_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("Sizda ushbu buyruqdan foydalanish huquqi yo'q.")
        return

    await state.clear()
    courses, counts = await get_courses_and_counts()

    txt = (
        "👑 <b>Admin Boshqaruv Markazi</b>\n\n"
        f"👤 <b>Admin:</b> {message.from_user.full_name}\n"
        f"🌐 <b>Jami foydalanuvchilar:</b> {counts.get('all', 0)} ta\n"
        f"🎓 <b>Jami Mentorlar:</b> {counts.get('mentors', 0)} ta\n\n"
        "Pastdagi menyu orqali kerakli bo'limni tanlang 👇"
    )
    await message.answer(txt, reply_markup=ADMIN_MENU, parse_mode="HTML")


@router.message(F.text.in_(["📊 Platforma statistikasi", "📊 Platforma Analitikasi"]))
@router.callback_query(F.data == "admin_action:stats")
async def process_admin_stats(event: Message | CallbackQuery) -> None:
    user_id = event.from_user.id if event.from_user else 0
    if user_id not in settings.bot.admin_ids:
        if isinstance(event, CallbackQuery):
            await event.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    courses, counts = await get_courses_and_counts()

    txt = (
        "📊 <b>Platforma Statistikasi:</b>\n\n"
        f"🌐 <b>Jami foydalanuvchilar:</b> {counts.get('all', 0)} ta\n"
        f"🎓 <b>Jami Mentorlar:</b> {counts.get('mentors', 0)} ta\n\n"
        "<b>Kurslar bo'yicha:</b>\n"
    )
    course_icons = {1: "🚛", 2: "📢", 3: "🎁", 4: "💻", 5: "🇨🇳"}
    for c in courses:
        cid = c["id"]
        icon = course_icons.get(cid, "📚")
        txt += f"• {icon} <b>{c.get('title')}:</b> {counts.get(f'course_{cid}', 0)} ta\n"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(txt, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(txt, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")
