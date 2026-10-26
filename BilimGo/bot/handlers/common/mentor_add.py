"""
Mentor qo'shish va boshqarish handlerlari (Admin uchun).
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.common._utils import AddMentorState, _notify_super_mentors_about_mentor_activation
from bot.keyboards.admin_kb import ADMIN_MENU
from bot.keyboards.common_kb import (
    get_mentor_assignment_courses_keyboard,
    get_mentor_tariff_keyboard,
)
from bot.keyboards.mentor_kb import get_mentor_inline_webapp
from core.config import settings
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.tariff_quota_repo import TariffQuotaRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService

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
        courses = await CourseRepository(database.conn).list_published()
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
    conn = database.conn
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)

    target_user = await user_repo.get_or_create(telegram_id=target_tid)
    display_name = target_user.full_name or f"Foydalanuvchi #{target_tid}"
    courses = await course_repo.list_published()

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

    course_repo = CourseRepository(database.conn)
    course = await course_repo.get_by_id(course_id)
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

    conn = database.conn
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    target_user = await user_repo.get_or_create(telegram_id=target_tid)
    await user_repo.update_role(target_user.id, "mentor")

    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1", (target_user.id,)
    )
    node_row = await cursor.fetchone()
    if not node_row:
        cur = await conn.execute(
            "INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status) "
            "VALUES (1, ?, ?, 20.0, 'limit', 'active')",
            (target_user.id, course_id),
        )
        await conn.commit()
        node_id = cur.lastrowid
    else:
        node_id = node_row["id"]
        await conn.execute("UPDATE license_nodes SET course_id = ? WHERE id = ?", (course_id, node_id))
        await conn.commit()

    # 15 kunlik bepul limit kvotalarini shakllantirish
    await quota_repo.initialize_quotas_for_tariff(node_id, tariff_name)

    cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
    cabinet = await cabinet_service.get_or_create_for_node(node_id)
    all_courses = await course_repo.list_published()

    # Barcha kurslarga mentor uchun dostup ochish
    for c in all_courses:
        try:
            await access_grant_repo.grant_access(target_user.id, c.id, node_id)
        except Exception:
            pass

    selected_course = await course_repo.get_by_id(course_id)
    course_title = selected_course.title if selected_course else f"Kurs #{course_id}"

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

    conn = database.conn
    cursor = await conn.execute(
        """
        SELECT
            u.id as user_id, u.full_name, u.telegram_id, u.phone,
            ln.id as node_id, ln.stage,
            (SELECT COUNT(*) FROM cabinet_members cm WHERE cm.cabinet_id = cab.id AND cm.role_in_cabinet = 'student') as student_count
        FROM license_nodes ln
        JOIN users u ON u.id = ln.owner_user_id
        LEFT JOIN cabinets cab ON cab.owner_node_id = ln.id
        WHERE ln.id > 1
        ORDER BY ln.id ASC
        """
    )
    rows = await cursor.fetchall()

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
