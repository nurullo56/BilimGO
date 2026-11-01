"""
Mentor qo'shish va boshqarish handlerlari (Admin uchun).
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.common._utils import AddMentorState
from bot.keyboards.admin import ADMIN_MENU
from bot.keyboards.common import (
    get_mentor_assignment_courses_keyboard,
    get_mentor_tariff_keyboard,
)
from bot.keyboards.mentor import get_mentor_inline_webapp
from core.config import settings
from db.repositories.user_repo import User
from services.course_service import CourseService
from services.mentor_service import MentorService

logger = logging.getLogger(__name__)
router = Router(name="mentor_add")


@router.message(Command("newmentor"))
@router.message(Command("addmentor"))
@router.message(F.text.in_([
    "➕ Yangi Mentor qo'shish", "➕ Yangi Mentor Havolasi",
    "➕ Yangi Mentor", "➕ Mentor tayinlash", "Yangi Mentor qo'shish",
]))
async def start_add_mentor_process(message: Message, user: User, state: FSMContext) -> None:
    if user.role != "admin" and message.from_user.id not in settings.bot.admin_ids:
        await message.answer("Bu amal faqat Super Admin / Bosh Mentor uchun.")
        return

    args = message.text.split()
    if len(args) >= 2 and args[1].isdigit():
        target_tid = int(args[1])
        courses = await CourseService().list_published()
        keyboard = get_mentor_assignment_courses_keyboard(courses, target_tid)
        await message.answer(
            f"👤 <b>Yangi Mentor Telegram ID:</b> <code>{target_tid}</code>\n\n"
            "📚 <b>Mentor uchun asosiy kurs yo'nalishini tanlang:</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    await state.set_state(AddMentorState.waiting_for_tg_id)
    await message.answer(
        "✍️ <b>Mentor qilmoqchi bo'lgan shaxsning Telegram ID raqamini kiriting:</b>\n\n"
        "<i>(Masalan: <code>123456789</code> yoki forward qilingan xabar)</i>\n\n"
        "Bekor qilish uchun /cancel deb yozing.",
    )


@router.message(AddMentorState.waiting_for_tg_id)
async def process_mentor_id_input(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text in ("/cancel", "🔙 Bekor qilish"):
        await state.clear()
        await message.answer("Mentor qo'shish bekor qilindi.", reply_markup=ADMIN_MENU)
        return

    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(
            "Iltimos, faqat raqamlardan iborat Telegram ID kiriting (Masalan: <code>123456789</code>):"
        )
        return

    target_tid = int(text)
    mentor_service = MentorService()
    target_user, display_name, courses = await mentor_service.get_target_user_and_courses(target_tid)

    if not courses:
        await message.answer("Tizimda nashr qilingan kurslar mavjud emas.")
        await state.clear()
        return

    keyboard = get_mentor_assignment_courses_keyboard(courses, target_tid)
    await state.clear()
    await message.answer(
        f"👤 <b>Bo'lajak Mentor:</b> {display_name} (ID: <code>{target_tid}</code>)\n\n"
        "📚 <b>Mentor uchun asosiy kurs yo'nalishini tanlang:</b>\n"
        "<i>(Mentor ushbu yo'nalish bo'yicha shaxsiy kabinetga va limitga ega bo'ladi)</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("mentor_assign_course:"))
async def handle_mentor_assign_course(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Noto'g'ri ma'lumot", show_alert=True)
        return

    target_tid = int(parts[1])
    course_id = int(parts[2])

    course = await CourseService().get_by_id(course_id)
    course_title = course.title if course else f"Kurs #{course_id}"

    keyboard = get_mentor_tariff_keyboard(target_tid, course_id)
    await callback.message.edit_text(
        f"🎓 <b>Tanlangan Kurs:</b> {course_title}\n"
        f"👤 <b>Mentor Telegram ID:</b> <code>{target_tid}</code>\n\n"
        "🎁 <b>Mentor uchun 15 kunlik bepul sinov (limit) paketini tanlang:</b>\n"
        "<i>(Ushbu paket bo'yicha mentorga talabalar kvotasi ajratiladi)</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_set_tariff:"))
async def handle_mentor_set_tariff(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Noto'g'ri ma'lumot", show_alert=True)
        return

    target_tid = int(parts[1])
    course_id = int(parts[2])
    tariff_name = parts[3]

    await callback.message.edit_text("⏳ Mentor tayinlanmoqda va kabinet ochilmoqda...")
    await process_mentor_assignment(callback.message, target_tid, course_id, tariff_name, bot=bot)
    await callback.answer()


@router.callback_query(F.data == "mentor_assign_cancel")
async def handle_mentor_assign_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ Mentor tayinlash bekor qilindi.")
    await callback.answer("Bekor qilindi")


async def process_mentor_assignment(
    message: Message,
    target_tid: int,
    course_id: int = 1,
    tariff_name: str = "standart",
    bot: Bot | None = None,
) -> None:
    if bot is None:
        bot = message.bot

    mentor_service = MentorService()
    try:
        res = await mentor_service.assign_mentor(
            target_tid=target_tid,
            course_id=course_id,
            tariff_name=tariff_name,
        )
    except Exception as e:
        logger.exception("Mentor tayinlashda xatolik yuz berdi: %s", e)
        await message.answer("❌ Mentorni tayinlashda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
        return

    target_user = res["target_user"]
    node_id = res["node_id"]
    cabinet = res["cabinet"]
    all_courses = res["all_courses"]
    course_title = res["course_title"]

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"
    mentor_start_link = f"https://t.me/{bot_username}?start=mentor_{target_tid}"

    await message.answer(
        f"👑 <b>Yangi Mentor muvaffaqiyatli tayinlandi!</b>\n\n"
        f"• <b>Telegram ID:</b> <code>{target_tid}</code>\n"
        f"• <b>Asosiy Kurs:</b> {course_title}\n"
        f"• <b>Tarif:</b> {tariff_name.capitalize()} (15 kunlik bepul kvota berildi)\n"
        f"• <b>Litsenziya:</b> Node #{node_id}\n"
        f"• <b>Kabinet:</b> {cabinet.display_name}\n"
        f"• <b>Kurslar:</b> Barcha {len(all_courses)} ta kurs mentorga to'liq ochildi! ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <b>Quyidagi xabarni nusxalab bo'lajak mentorga yuborishingiz mumkin:</b>\n\n"
        f"<i>Assalomu alaykum! Siz «BilimGo» platformasida rasmiy <b>Mentor</b> sifatida tayinlandingiz.</i>\n\n"
        f"<i>Barcha kurslarni to'liq ko'rish va o'z shogirdlaringiz uchun shaxsiy sotuv havolalaringizni olish uchun quyidagi havola orqali botga kiring:</i>\n\n"
        f"👉 <code>{mentor_start_link}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=ADMIN_MENU,
        parse_mode="HTML",
    )

    try:
        await bot.send_message(
            chat_id=target_tid,
            text=(
                f"🎉 <b>Assalomu alaykum, {target_user.full_name or 'Hurmatli Mentor'}!</b> 🎓\n\n"
                f"Siz «BilimGo» platformasida <b>{course_title}</b> kursi bo'yicha rasmiy <b>Mentor</b> sifatida tayinlandingiz!\n\n"
                "• Barcha kurslar siz uchun to'liq ochildi ✅\n"
                "• Shaxsiy o'quv kabinetingiz yaratildi 👥\n"
                f"• {tariff_name.capitalize()} tarifi bo'yicha 15 kunlik bepul limit davri ajratildi 🎁\n\n"
                "Quyidagi tugma orqali kabinetingizni ochishingiz mumkin 👇"
            ),
            reply_markup=get_mentor_inline_webapp(settings.webapp.base_url),
            parse_mode="HTML",
        )
        logger.info("Yangi tayinlangan mentor %s ga to'g'ridan-to'g'ri xabar yuborildi.", target_tid)
    except Exception as e:
        logger.warning("Yangi mentor %s ga to'g'ridan-to'g'ri xabar yetkazilmadi: %s", target_tid, e)


@router.message(Command("mentors"))
@router.message(F.text.in_(["👥 Barcha Mentorlar", "👥 Barcha mentorlar", "Barcha Mentorlar"]))
async def handle_list_all_mentors(message: Message, user: User) -> None:
    if user.role != "admin" and message.from_user.id not in settings.bot.admin_ids:
        await message.answer("Bu buyruq faqat Super Admin uchun.")
        return

    mentor_service = MentorService()
    rows = await mentor_service.list_all_submentors_overview()

    if not rows:
        await message.answer(
            "Hozircha tizimda quyi mentorlar yo'q.\n\n"
            "Yangi mentor tayinlash uchun <b>«➕ Yangi Mentor qo'shish»</b> tugmasidan foydalaning."
        )
        return

    lines = ["👑 <b>Platformadagi barcha Mentorlar ro'yxati:</b>\n"]
    for i, r in enumerate(rows, 1):
        name = r["full_name"] or f"Mentor #{r['user_id']}"
        phone = r["phone"] or "Telefon yo'q"
        stage_str = "Limit (15 kun)" if r["stage"] == "limit" else "Hamkorlik"
        students = r["student_count"] or 0
        lines.append(
            f"<b>{i}. {name}</b> (ID: <code>{r['telegram_id']}</code>)\n"
            f"   ├ 📱 Tel: <code>{phone}</code>\n"
            f"   ├ 🔑 Litsenziya: Node #{r['node_id']}\n"
            f"   ├ 📊 Holat: {stage_str}\n"
            f"   └ 👥 Shogirdlar: <b>{students} ta</b>\n"
        )
    await message.answer("\n".join(lines))
