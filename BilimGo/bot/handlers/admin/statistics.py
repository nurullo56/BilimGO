"""
Admin statistika va /admin buyrug'i handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.repositories.admin_repo import AdminRepository
from bot.keyboards.admin import (
    ADMIN_MENU,
    get_admin_panel_keyboard,
    get_infra_pagination_keyboard,
)
from core.config import settings
from services.mentor_service import MentorService

logger = logging.getLogger(__name__)
router = Router(name="admin_stats")


@router.message(Command("admin"))
async def handle_admin_command(message: Message, state: FSMContext) -> None:
    logger.info("Admin buyrug'i chaqirildi: tg_id=%s", message.from_user.id if message.from_user else 0)
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("Sizda ushbu buyruqdan foydalanish huquqi yo'q.")
        return

    await state.clear()
    courses, counts = await AdminRepository().get_courses_and_counts()

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
    logger.info("Admin statistika so'radi: tg_id=%s", event.from_user.id if event.from_user else 0)
    logger.info("Admin platforma statistikasini so'radi: from_user=%s", event.from_user.id if event.from_user else 0)
    user_id = event.from_user.id if event.from_user else 0
    if user_id not in settings.bot.admin_ids:
        if isinstance(event, CallbackQuery):
            await event.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    courses, counts = await AdminRepository().get_courses_and_counts()

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


PAGE_SIZE = 5


def _build_infra_stats_page(infra_data: dict, page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """
    Infratuzilma statistikasi sahifasi matni va pagination klaviaturasini (⬅️ ❌ ➡️) tuzadi.
    """
    grand = infra_data.get("grand_total", {})
    all_mentors = infra_data.get("mentors", [])

    total_mentors = len(all_mentors)
    total_pages = max(1, (total_mentors + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_mentors = all_mentors[start_idx:end_idx]

    lines: list[str] = [
        "⚡️ <b>Mentorlar Bo'yicha AI Token va Server Yuki Hisoboti</b>\n",
        "🌐 <b>Platforma Bo'yicha Jami:</b>",
        f"• 🤖 <b>AI Tyutor:</b> {grand.get('ai_queries', 0):,} ta savol ({grand.get('ai_tokens', 0):,} token) — {grand.get('ai_cost', 0):,.0f} so'm",
        f"• 🖥 <b>Video & Stream:</b> {grand.get('video_views', 0):,} ta ko'rish — {grand.get('server_cost', 0):,.0f} so'm",
        f"• 💰 <b>Jami Infratuzilma Xarajati:</b> <b>{grand.get('total_infra_cost', 0):,.0f} so'm</b>",
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n<b>👥 Mentorlar Kesimida (Sahifa: {current_page}/{total_pages}, Jami: {total_mentors} ta):</b>",
    ]

    if not page_mentors:
        lines.append("\n<i>Hozircha mentorlar ma'lumotlari topilmadi.</i>")
    else:
        for i, m in enumerate(page_mentors, start=start_idx + 1):
            name = m.get("full_name") or f"Mentor #{m.get('user_id')}"
            tid = m.get("telegram_id") or "—"
            node_id = m.get("node_id") or "—"
            students = m.get("student_count", 0)

            ai_q = m.get("ai_queries", 0)
            ai_tok = m.get("ai_tokens", 0)
            ai_cost = m.get("ai_cost", 0.0)

            views = m.get("video_views", 0)
            srv_cost = m.get("server_cost", 0.0)
            total_cost = m.get("total_infra_cost", 0.0)

            lines.append(
                f"\n<b>{i}. 👤 {name}</b> (TG ID: <code>{tid}</code>, Node #{node_id})\n"
                f"   ├ 👥 Shogirdlar soni: <b>{students} ta</b>\n"
                f"   ├ 🤖 AI Tyutor: <b>{ai_q:,} ta savol</b> ({ai_tok:,} token) — {ai_cost:,.0f} so'm\n"
                f"   ├ 🖥 Video Stream: <b>{views:,} ta ko'rish</b> — {srv_cost:,.0f} so'm\n"
                f"   └ 💵 Jami yuk: <b>{total_cost:,.0f} so'm</b>"
            )

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━")
    txt = "\n".join(lines)
    keyboard = get_infra_pagination_keyboard(current_page, total_pages)
    return txt, keyboard


@router.message(Command("infra_stats"))
@router.message(F.text.in_(["⚡️ Server yuki va AI tokenlar", "🖥 Server yuki va AI tokenlar"]))
@router.callback_query(F.data == "admin_action:infra_stats")
async def process_admin_infra_stats(event: Message | CallbackQuery) -> None:
    """Super Admin uchun barcha mentorlar va shogirdlarining AI token va server yuki hisoboti."""
    user_id = event.from_user.id if event.from_user else 0
    if user_id not in settings.bot.admin_ids:
        if isinstance(event, CallbackQuery):
            await event.answer("Ruxsatingiz yo'q!", show_alert=True)
        else:
            await event.answer("Sizda ushbu ma'lumotni ko'rish huquqi yo'q.")
        return

    mentor_service = MentorService()
    infra_data = await mentor_service.get_mentors_infrastructure_usage()
    txt, keyboard = _build_infra_stats_page(infra_data, page=1)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(txt, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(txt, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("admin_infra:page:"))
async def handle_infra_page(callback: CallbackQuery) -> None:
    """Oldingi/Keyingi sahifaga o'tish handleri (⬅️ ➡️)."""
    user_id = callback.from_user.id if callback.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    parts = callback.data.split(":")
    try:
        page = int(parts[-1])
    except ValueError:
        page = 1

    mentor_service = MentorService()
    infra_data = await mentor_service.get_mentors_infrastructure_usage()
    txt, keyboard = _build_infra_stats_page(infra_data, page=page)

    try:
        await callback.message.edit_text(txt, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.debug("Infra stats xabari o'zgarmadi: %s", e)

    await callback.answer()


@router.callback_query(F.data.startswith("admin_infra:noop:"))
async def handle_infra_noop(callback: CallbackQuery) -> None:
    """Chekka sahifalarda noop bildirishnomasi."""
    reason = callback.data.split(":")[-1]
    if reason == "first":
        await callback.answer("Birinchi sahifadasiz ⬅️", show_alert=False)
    elif reason == "last":
        await callback.answer("Oxirgi sahifadasiz ➡️", show_alert=False)
    else:
        await callback.answer()


@router.callback_query(F.data == "admin_infra:close")
async def handle_infra_close(callback: CallbackQuery) -> None:
    """Hisobotni yopish (❌)."""
    user_id = callback.from_user.id if callback.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_text("❌ Hisobot yopildi.")
    await callback.answer("Hisobot yopildi")
