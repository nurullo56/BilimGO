"""
Admin quota (limit) boshqaruvi handlerlari.
DB helper funksiyalar _admin_db.py da.
"""
from __future__ import annotations

import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.admin._admin_db import get_quota_mentors_list
from bot.keyboards.admin_kb import (
    ADMIN_MENU,
    get_quota_amount_keyboard,
    get_quota_courses_keyboard,
    get_quota_mentors_keyboard,
)
from bot.keyboards.mentor_kb import get_mentor_inline_webapp
from bot.states.fsm_states import AddQuotaStates
from core.config import settings
from db.database import database
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.tariff_quota_repo import TariffQuotaRepository
from db.repositories.user_repo import User, UserRepository

logger = logging.getLogger(__name__)
router = Router(name="admin_quota")


# ─────────────────────────────────────────────
# Quota qo'shish yordamchi funksiyasi
# ─────────────────────────────────────────────

async def _apply_quota_addition(
    callback: CallbackQuery,
    bot: Bot,
    node_id: int,
    course_id: int,
    add_amount: int,
) -> None:
    conn = database.conn
    course_repo = CourseRepository(conn)
    node_repo = LicenseNodeRepository(conn)
    user_repo = UserRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    course = await course_repo.get_by_id(course_id)
    node = await node_repo.get_by_id(node_id)
    mentor = await user_repo.get_by_id(node.owner_user_id) if node else None

    if not course or not node or not mentor:
        await callback.answer("Mentor yoki kurs topilmadi.", show_alert=True)
        return

    updated_quota = await quota_repo.add_quota_amount(
        node_id=node.id,
        course_title=course.title,
        add_amount=add_amount,
        tariff_name="standart",
        course_id=course.id,
    )

    mentor_name = html.escape(mentor.full_name or f"Mentor #{node.id}")
    course_title = html.escape(course.title)

    await callback.message.edit_text(
        f"✅ <b>Limit muvaffaqiyatli qo'shildi!</b> 🎉\n\n"
        f"👤 <b>Mentor:</b> <b>{mentor_name}</b> (ID: <code>{mentor.telegram_id}</code>)\n"
        f"📚 <b>Kurs:</b> «{course_title}»\n"
        f"➕ <b>Qo'shilgan dostuplar:</b> <b>+{add_amount} ta</b>\n"
        f"📊 <b>Yangi jami limit:</b> <b>{updated_quota.remaining}/{updated_quota.total_quota} ta qoldi</b> "
        f"(ishlatilgan: {updated_quota.used_quota} ta)",
        parse_mode="HTML",
    )
    await callback.answer(f"+{add_amount} ta dostup qo'shildi!", show_alert=True)

    mentor_notify_msg = (
        f"🎉 <b>Sizga yangi bepul dostup limiti qo'shildi!</b> 🎁\n\n"
        f"Hurmatli <b>{mentor_name}</b>, Bosh Mentor (Super Admin) tomonidan 15 kunlik ta'lim davringiz uchun "
        f"<b>«{course_title}»</b> kursi bo'yicha <b>+{add_amount} ta</b> qo'shimcha dostup ajratildi!\n\n"
        f"📊 <b>Joriy limitingiz:</b> <b>{updated_quota.remaining}/{updated_quota.total_quota} ta qoldi</b> "
        f"(ishlatilgan: {updated_quota.used_quota} ta)\n\n"
        f"💰 <i>Eslatma: 15 kunlik limit davrida o'quvchilaringizga sotilgan barcha kurslardan 100% daromad to'liq o'zingizda qoladi!</i>\n\n"
        f"🚀 <i>Shaxsiy sotuv havolalaringizni olish uchun botdagi «🔗 Kurslarim sotuv havolalari» tugmasidan foydalaning.</i>"
    )
    if mentor.telegram_id:
        try:
            await bot.send_message(
                chat_id=mentor.telegram_id,
                text=mentor_notify_msg,
                reply_markup=get_mentor_inline_webapp(settings.webapp.base_url),
                parse_mode="HTML",
            )
            logger.info("Mentor %s ga +%s quota qo'shilganligi haqida xabar yuborildi.", mentor.telegram_id, add_amount)
        except Exception as e:
            logger.warning("Mentor %s ga bildirishnoma yuborishda xatolik: %s", mentor.telegram_id, e)


# ─────────────────────────────────────────────
# HANDLERLAR
# ─────────────────────────────────────────────

@router.message(Command("addquota"))
@router.message(Command("limit"))
@router.message(Command("quotas"))
@router.message(F.text.in_(["🎁 Mentorga limit qo'shish", "🎁 Mentor limitlari", "🎁 Limit qo'shish"]))
async def start_quota_management(message: Message, user: User, state: FSMContext) -> None:
    if user.role != "admin" and message.from_user.id not in settings.bot.admin_ids:
        await message.answer("Bu amal faqat Bosh Mentor (Super Admin) uchun ruxsat etilgan.")
        return

    await state.clear()
    mentors = await get_quota_mentors_list()
    if not mentors:
        await message.answer(
            "Hozircha tizimda quyi mentorlar mavjud emas.\n\n"
            "Avval «➕ Yangi Mentor qo'shish» tugmasi orqali yangi mentor tayinlang.",
            reply_markup=ADMIN_MENU,
        )
        return

    await message.answer(
        "🎁 <b>Mentorlarga Bepul Dostup Limitini Qo'shish</b> (15 kunlik limit davri)\n\n"
        "Qaysi mentorga qo'shimcha dostup limiti ajratmoqchisiz? Quyidagi ro'yxatdan tanlang 👇",
        reply_markup=get_quota_mentors_keyboard(mentors),
    )


@router.callback_query(F.data.startswith("quota_mentor:"))
async def handle_choose_mentor_quota(callback: CallbackQuery, state: FSMContext) -> None:
    node_id = int(callback.data.split(":")[1])
    await state.clear()

    conn = database.conn
    node_repo = LicenseNodeRepository(conn)
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    node = await node_repo.get_by_id(node_id)
    if not node:
        await callback.answer("Mentor litsenziya tuguni topilmadi.", show_alert=True)
        return

    mentor_user = await user_repo.get_by_id(node.owner_user_id)
    mentor_name = mentor_user.full_name if mentor_user else f"Mentor #{node.id}"

    courses = await course_repo.list_published()
    quotas_list = await quota_repo.list_by_node(node.id)
    quotas_map = {q.course_title: q for q in quotas_list}

    stage_title = "⏳ 15 kunlik Limit davri (100% mentorga)" if node.stage == "limit" else "🤝 Hamkorlik davri (Royalti)"
    status_str = "✅ Faol" if node.status == "active" else "⛔️ To'xtatilgan"

    lines = [
        f"👨‍🏫 <b>Mentor:</b> <b>{mentor_name}</b> (Node #{node.id})",
        f"📌 <b>Bosqich:</b> {stage_title}",
        f"📊 <b>Karta holati:</b> {status_str}\n",
        "📋 <b>Joriy bepul dostup limitlari:</b>",
    ]
    if quotas_list:
        for q in quotas_list:
            lines.append(f"• <b>{q.course_title}:</b> {q.remaining}/{q.total_quota} ta qoldi (ishlatilgan: {q.used_quota} ta)")
    else:
        lines.append("<i>Hozircha kurslar bo'yicha limitlar ochilmagan.</i>")
    lines.append("\n👇 <b>Qaysi kurs yo'nalishiga limit qo'shmoqchisiz?</b>")

    kb = get_quota_courses_keyboard(
        node_id=node.id,
        courses=[{"id": c.id, "title": c.title} for c in courses],
        quotas_map=quotas_map,
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("quota_course:"))
async def handle_choose_course_quota(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    node_id = int(parts[1])
    course_id = int(parts[2])

    conn = database.conn
    course_repo = CourseRepository(conn)
    user_repo = UserRepository(conn)
    node_repo = LicenseNodeRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    course = await course_repo.get_by_id(course_id)
    node = await node_repo.get_by_id(node_id)
    mentor = await user_repo.get_by_id(node.owner_user_id) if node else None

    if not course or not node or not mentor:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    quota = await quota_repo.get_quota_for_course(node.id, course.title)
    remaining_info = f" (Hozirda: {quota.remaining}/{quota.total_quota} ta qolgan)" if quota else " (Hali limit belgilanmagan)"
    mentor_name = mentor.full_name or f"Mentor #{node.id}"

    text = (
        f"🎁 <b>Limit qo'shish</b>\n\n"
        f"👤 <b>Mentor:</b> {mentor_name}\n"
        f"📚 <b>Kurs:</b> «{course.title}»{remaining_info}\n\n"
        f"Ushbu mentorga <b>«{course.title}»</b> yo'nalishi bo'yicha nechta qo'shimcha bepul dostup qo'shmoqchisiz?\n\n"
        f"👇 Quyidagi tugmalardan birini tanlang yoki o'zingiz yozing:"
    )
    await callback.message.edit_text(
        text, reply_markup=get_quota_amount_keyboard(node_id=node.id, course_id=course.id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quota_add:"))
async def handle_add_preset_quota(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    node_id, course_id, amount = int(parts[1]), int(parts[2]), int(parts[3])
    await state.clear()
    await _apply_quota_addition(callback=callback, bot=bot, node_id=node_id, course_id=course_id, add_amount=amount)


@router.callback_query(F.data.startswith("quota_custom:"))
async def handle_custom_quota_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    node_id, course_id = int(parts[1]), int(parts[2])
    await state.set_state(AddQuotaStates.entering_amount)
    await state.update_data(node_id=node_id, course_id=course_id)
    await callback.message.edit_text(
        "✍️ <b>Qo'shmoqchi bo'lgan dostup miqdorini raqamda kiriting:</b>\n\n"
        "<i>(Masalan: <code>15</code> yoki <code>25</code>)</i>\n\n"
        "Bekor qilish uchun /cancel deb yozing.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddQuotaStates.entering_amount)
async def process_custom_quota_input(message: Message, bot: Bot, state: FSMContext) -> None:
    if message.text in ("/cancel", "🔙 Bekor qilish"):
        await state.clear()
        await message.answer("Limit qo'shish bekor qilindi.", reply_markup=ADMIN_MENU)
        return

    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, 0 dan katta butun son kiriting (Masalan: <code>15</code>):")
        return

    amount = int(text)
    data = await state.get_data()
    node_id = data.get("node_id")
    course_id = data.get("course_id")
    await state.clear()

    if not node_id or not course_id:
        await message.answer("Xatolik yuz berdi. Iltimos qaytadan boshlang.", reply_markup=ADMIN_MENU)
        return

    conn = database.conn
    course_repo = CourseRepository(conn)
    node_repo = LicenseNodeRepository(conn)
    user_repo = UserRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    course = await course_repo.get_by_id(course_id)
    node = await node_repo.get_by_id(node_id)
    mentor = await user_repo.get_by_id(node.owner_user_id) if node else None

    if not course or not node or not mentor:
        await message.answer("Mentor yoki kurs topilmadi.", reply_markup=ADMIN_MENU)
        return

    updated_quota = await quota_repo.add_quota_amount(
        node_id=node.id, course_title=course.title,
        add_amount=amount, tariff_name="standart", course_id=course.id,
    )

    mentor_name = html.escape(mentor.full_name or f"Mentor #{node.id}")
    course_title = html.escape(course.title)

    await message.answer(
        f"✅ <b>Limit muvaffaqiyatli qo'shildi!</b> 🎉\n\n"
        f"👤 <b>Mentor:</b> <b>{mentor_name}</b> (ID: <code>{mentor.telegram_id}</code>)\n"
        f"📚 <b>Kurs:</b> «{course_title}»\n"
        f"➕ <b>Qo'shilgan dostuplar:</b> <b>+{amount} ta</b>\n"
        f"📊 <b>Yangi jami limit:</b> <b>{updated_quota.remaining}/{updated_quota.total_quota} ta qoldi</b> "
        f"(ishlatilgan: {updated_quota.used_quota} ta)",
        reply_markup=ADMIN_MENU, parse_mode="HTML",
    )

    mentor_notify_msg = (
        f"🎉 <b>Sizga yangi bepul dostup limiti qo'shildi!</b> 🎁\n\n"
        f"Hurmatli <b>{mentor_name}</b>, Bosh Mentor (Super Admin) tomonidan 15 kunlik ta'lim davringiz uchun "
        f"<b>«{course_title}»</b> kursi bo'yicha <b>+{amount} ta</b> qo'shimcha dostup ajratildi!\n\n"
        f"📊 <b>Joriy limitingiz:</b> <b>{updated_quota.remaining}/{updated_quota.total_quota} ta qoldi</b> "
        f"(ishlatilgan: {updated_quota.used_quota} ta)\n\n"
        f"💰 <i>15 kunlik limit davrida 100% daromad to'liq o'zingizda!</i>"
    )
    if mentor.telegram_id:
        try:
            await bot.send_message(
                chat_id=mentor.telegram_id, text=mentor_notify_msg,
                reply_markup=get_mentor_inline_webapp(settings.webapp.base_url), parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Mentor %s ga bildirishnoma yuborishda xatolik: %s", mentor.telegram_id, e)


@router.callback_query(F.data == "quota_back_mentors")
async def handle_quota_back_to_mentors(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    mentors = await get_quota_mentors_list()
    await callback.message.edit_text(
        "🎁 <b>Mentorlarga Bepul Dostup Limitini Qo'shish</b> (15 kunlik limit davri)\n\n"
        "Qaysi mentorga qo'shimcha dostup limiti ajratmoqchisiz? Quyidagi ro'yxatdan tanlang 👇",
        reply_markup=get_quota_mentors_keyboard(mentors),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "quota_cancel")
async def handle_quota_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ <b>Limit boshqaruvi bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer()
