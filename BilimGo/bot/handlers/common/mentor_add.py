"""
Mentor qo'shish va boshqarish handlerlari (Admin uchun).
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.common._utils import AddMentorState, _notify_super_mentors_about_mentor_activation
from bot.keyboards.admin_kb import ADMIN_MENU
from bot.keyboards.mentor_kb import get_mentor_inline_webapp
from core.config import settings
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
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
        await process_mentor_assignment(message, int(args[1]), bot=message.bot)
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
    await state.clear()
    await process_mentor_assignment(message, target_tid, bot=bot)


async def process_mentor_assignment(message: Message, target_tid: int, bot: Bot) -> None:
    conn = database.conn
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    target_user = await user_repo.get_or_create(telegram_id=target_tid)
    await user_repo.update_role(target_user.id, "mentor")

    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1", (target_user.id,)
    )
    node_row = await cursor.fetchone()
    if not node_row:
        cur = await conn.execute(
            "INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status) "
            "VALUES (1, ?, 1, 20.0, 'limit', 'active')",
            (target_user.id,),
        )
        await conn.commit()
        node_id = cur.lastrowid
    else:
        node_id = node_row["id"]

    cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
    cabinet = await cabinet_service.get_or_create_for_node(node_id)
    all_courses = await course_repo.list_published()

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"
    mentor_start_link = f"https://t.me/{bot_username}?start=mentor_{target_tid}"

    await message.answer(
        f"👑 <b>Yangi Mentor muvaffaqiyatli tayinlandi!</b>\n\n"
        f"• <b>Telegram ID:</b> <code>{target_tid}</code>\n"
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
    )

    try:
        await bot.send_message(
            chat_id=target_tid,
            text=(
                f"🎉 <b>Assalomu alaykum, {target_user.full_name or 'Hurmatli Mentor'}!</b> 🎓\n\n"
                "Siz «BilimGo» platformasida rasmiy <b>Mentor</b> sifatida tayinlandingiz!\n\n"
                "• Barcha kurslar siz uchun to'liq ochildi ✅\n"
                "• Shaxsiy o'quv kabinetingiz yaratildi 👥\n"
                "• 15 kunlik bepul limit davri ajratildi 🎁\n\n"
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
