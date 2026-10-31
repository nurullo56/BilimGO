from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.mentor import (
    get_live_course_select_keyboard,
    get_live_session_scheduled_keyboard,
)
from bot.states.fsm_states import ScheduleLiveStates
from core.config import settings
from db.database import database
from db.repositories.course_repo import CourseRepository
from db.repositories.user_repo import User
from services.live_stream_service import live_manager

logger = logging.getLogger(__name__)

router = Router(name="mentor_live")


async def _get_mentor_courses(mentor_id: int) -> list[any]:
    admin_ids = getattr(settings.bot, "admin_ids", [])
    if mentor_id in admin_ids or mentor_id == 1:
        return await CourseRepository(database.conn).list_published()

    cursor = await database.conn.execute(
        """
        SELECT c.id, c.title
        FROM courses c
        JOIN license_nodes ln ON ln.course_id = c.id OR ln.parent_id IS NULL
        WHERE ln.owner_user_id = ?
        GROUP BY c.id
        """,
        (mentor_id,),
    )
    rows = await cursor.fetchall()
    if not rows:
        # Fallback to list published courses if admin or direct mentor
        rows = await CourseRepository(database.conn).list_published()
    return rows


@router.message(F.text == "🔴 Live dars belgilash")
async def start_scheduling(message: Message, user: User, state: FSMContext) -> None:
    """Live dars belgilash"""
    courses = await _get_mentor_courses(user.id)
    if not courses:
        await message.answer("❌ Sizga tegishli kurslar topilmadi.")
        return

    keyboard = get_live_course_select_keyboard(courses)
    await message.answer(
        "🎥 <b>Yangi Live dars belgilash</b>\n\n"
        "Qaysi kurs uchun jonli efir o'tkazmoqchisiz?",
        reply_markup=keyboard,
    )
    await state.set_state(ScheduleLiveStates.choosing_course)


@router.callback_query(ScheduleLiveStates.choosing_course, F.data.startswith("live_course:"))
async def choose_course(callback: CallbackQuery, state: FSMContext) -> None:
    """Kurs tanlash"""
    course_id = int(callback.data.split(":")[1])
    await state.update_data(course_id=course_id)

    await callback.message.answer(
        "📅 <b>Sana va vaqtni kiriting:</b>\n\n"
        "Format: <code>2026-08-28 18:00</code>\n\n"
        "Masalan: <code>2026-08-29 20:00</code>\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await state.set_state(ScheduleLiveStates.entering_datetime)
    await callback.answer()


@router.callback_query(F.data == "live_cancel")
async def cancel_live_choice(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Live dars belgilash bekor qilindi.")
    await callback.answer()


@router.message(ScheduleLiveStates.entering_datetime)
async def enter_datetime(message: Message, user: User, state: FSMContext, bot: Bot) -> None:
    """Sana va vaqt kiritish"""
    if message.text in ("/cancel", "Bekor qilish"):
        await state.clear()
        await message.answer("Live dars belgilash bekor qilindi.")
        return

    try:
        scheduled_at = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "Format namunasi: <code>2026-08-28 18:00</code>"
        )
        return

    data = await state.get_data()
    course_id = data.get("course_id", 1)

    course = await CourseRepository(database.conn).get_by_id(course_id)
    course_title = course.title if course else f"Kurs #{course_id}"

    try:
        # Live session yaratish
        session = await live_manager.create_session(
            course_id=course_id,
            mentor_id=user.id,
            title=f"{course_title} bo'yicha jonli efir",
            scheduled_at=scheduled_at,
        )

        await state.clear()

        webapp_url = f"{settings.webapp.base_url}/live/{session['id']}"
        keyboard = get_live_session_scheduled_keyboard(session["id"], webapp_url)

        await message.answer(
            f"✅ <b>Live dars muvaffaqiyatli belgilandi!</b> 🎉\n\n"
            f"📺 <b>Sessiya ID:</b> <code>{session['id']}</code>\n"
            f"📚 <b>Kurs:</b> {course_title}\n"
            f"📅 <b>Vaqt:</b> {scheduled_at.strftime('%d-%m-%Y %H:%M')}\n"
            f"🔗 <b>Havola:</b> {webapp_url}\n\n"
            f"<i>Efir boshlanganda «📢 Talabalarga xabar yuborish» orqali ularni xabardor qilishingiz mumkin.</i>",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.exception("Live dars belgilashda xatolik yuz berdi: %s", e)
        await message.answer(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"Live darsni saqlashda xatolik yuz berdi: <code>{str(e)}</code>\n"
            f"Iltimos, qaytadan urinib ko'ring yoki /cancel deb yozing."
        )


@router.callback_query(F.data.startswith("live_notify:"))
async def notify_students(callback: CallbackQuery, bot: Bot) -> None:
    """Talabalarga live haqida xabar yuborish"""
    session_id = callback.data.split(":")[1]
    session = await live_manager.get_session_info(session_id)
    if not session:
        await callback.answer("❌ Sessiya topilmadi!", show_alert=True)
        return

    conn = database.conn
    cursor = await conn.execute(
        """
        SELECT DISTINCT u.telegram_id, u.full_name
        FROM access_grants ag
        JOIN users u ON u.id = ag.user_id
        WHERE ag.course_id = ? AND ag.status = 'active'
        """,
        (session.get("course_id"),),
    )
    students = await cursor.fetchall()

    if not students:
        # Fallback to cabinet members
        cursor2 = await conn.execute(
            """
            SELECT DISTINCT u.telegram_id, u.full_name
            FROM cabinet_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.role_in_cabinet = 'student'
            """
        )
        students = await cursor2.fetchall()

    if not students:
        await callback.answer("⚠️ Talabalar topilmadi!", show_alert=True)
        return

    live_url = f"{settings.webapp.base_url}/live/{session_id}"
    msg_text = (
        f"🔴 <b>Jonli efir boshlanmoqda!</b>\n\n"
        f"📚 <b>Mavzu:</b> {session.get('title', 'Jonli efir')}\n"
        f"⏰ <b>Vaqt:</b> {session.get('scheduled_at', 'Hozir')}\n\n"
        f"<i>Savollaringizni jonli efirda berishingiz va mentor bilan to'g'ridan-to'g'ri muloqot qilishingiz mumkin!</i>\n\n"
        f"👉 <a href='{live_url}'>Efirga qo'shilish uchun bosing</a>"
    )

    sent_count = 0
    for s in students:
        try:
            await bot.send_message(
                chat_id=s["telegram_id"],
                text=msg_text,
                parse_mode="HTML",
            )
            sent_count += 1
        except Exception as e:
            logger.debug(f"Live notify to {s['telegram_id']} failed: {e}")

    await callback.answer(f"✅ {sent_count} ta talabaga xabar yuborildi!", show_alert=True)


@router.callback_query(F.data.startswith("live_cancel_session:"))
async def cancel_session(callback: CallbackQuery) -> None:
    """Live sessiyani bekor qilish"""
    session_id = callback.data.split(":")[1]
    try:
        await live_manager.end_session(session_id)
    except Exception as exc:
        import logging
        logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    await callback.message.edit_text("❌ <b>Live dars bekor qilindi.</b>")
    await callback.answer("Bekor qilindi!")
