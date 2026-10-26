from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.admin_kb import (
    ADMIN_MENU,
    get_admin_panel_keyboard,
    get_broadcast_cancel_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_mentor_courses_keyboard,
    get_broadcast_mentors_keyboard,
    get_broadcast_target_keyboard,
)
from bot.states.fsm_states import BroadcastStates
from core.config import settings
from db.database import database

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")


async def _get_courses_and_counts() -> tuple[list[dict], dict[str, int]]:
    conn = database.conn
    
    cursor = await conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
    courses = [dict(r) for r in await cursor.fetchall()]
    
    counts: dict[str, int] = {}
    
    c_all = await conn.execute("SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE status = 'active' AND telegram_id IS NOT NULL")
    r_all = await c_all.fetchone()
    counts["all"] = r_all["cnt"] if r_all else 0
    
    c_men = await conn.execute("SELECT COUNT(DISTINCT telegram_id) as cnt FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL")
    r_men = await c_men.fetchone()
    counts["mentors"] = r_men["cnt"] if r_men else 0
    
    for c in courses:
        cid = c["id"]
        c_crs = await conn.execute(
            """
            SELECT COUNT(DISTINCT u.telegram_id) as cnt
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND u.id IN (
                SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                UNION
                SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
            )
            """,
            (cid, cid),
        )
        r_crs = await c_crs.fetchone()
        counts[f"course_{cid}"] = r_crs["cnt"] if r_crs else 0
        
    return courses, counts


async def _get_mentors_list() -> list[dict]:
    conn = database.conn
    cursor = await conn.execute(
        """
        SELECT u.id, u.telegram_id, u.full_name,
               (
                   SELECT COUNT(DISTINCT cm.user_id)
                   FROM cabinet_members cm
                   JOIN cabinets c ON c.id = cm.cabinet_id
                   JOIN license_nodes ln ON ln.id = c.owner_node_id
                   WHERE ln.owner_user_id = u.id AND cm.role_in_cabinet = 'student'
               ) as students_count
        FROM users u
        WHERE u.role = 'mentor' AND u.status = 'active'
        ORDER BY u.id ASC
        """
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def _get_mentor_courses_and_counts(mentor_id: int) -> tuple[dict, list[dict], dict[str, int]]:
    conn = database.conn
    cursor_m = await conn.execute("SELECT id, full_name, telegram_id FROM users WHERE id = ?", (mentor_id,))
    mentor_row = await cursor_m.fetchone()
    mentor_info = dict(mentor_row) if mentor_row else {"id": mentor_id, "full_name": f"Mentor #{mentor_id}"}
    
    cursor_c = await conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
    courses = [dict(r) for r in await cursor_c.fetchall()]
    
    counts: dict[str, int] = {}
    
    # All students of this mentor
    c_all = await conn.execute(
        """
        SELECT COUNT(DISTINCT u.telegram_id) as cnt
        FROM users u
        WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
            u.id IN (
                SELECT ag.user_id
                FROM access_grants ag
                JOIN license_nodes ln ON ln.id = ag.node_id
                WHERE ln.owner_user_id = ? AND ag.status = 'active'
            )
            OR u.id IN (
                SELECT cm.user_id
                FROM cabinet_members cm
                JOIN cabinets c ON c.id = cm.cabinet_id
                JOIN license_nodes ln ON ln.id = c.owner_node_id
                WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
            )
        )
        """,
        (mentor_id, mentor_id),
    )
    r_all = await c_all.fetchone()
    counts["mentor_all"] = r_all["cnt"] if r_all else 0
    
    # By course for this mentor
    for c in courses:
        cid = c["id"]
        c_crs = await conn.execute(
            """
            SELECT COUNT(DISTINCT u.telegram_id) as cnt
            FROM users u
            WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                u.id IN (
                    SELECT ag.user_id
                    FROM access_grants ag
                    JOIN license_nodes ln ON ln.id = ag.node_id
                    WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                )
                OR u.id IN (
                    SELECT cm.user_id
                    FROM cabinet_members cm
                    JOIN cabinets c ON c.id = cm.cabinet_id
                    JOIN license_nodes ln ON ln.id = c.owner_node_id
                    JOIN access_grants ag ON ag.user_id = cm.user_id AND ag.node_id = ln.id
                    WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                )
            )
            """,
            (mentor_id, cid, mentor_id, cid),
        )
        r_crs = await c_crs.fetchone()
        counts[f"mentor_course_{cid}"] = r_crs["cnt"] if r_crs else 0
        
    return mentor_info, courses, counts


async def _get_target_user_ids(target: str) -> list[int]:
    conn = database.conn
    
    if target == "all":
        cursor = await conn.execute("SELECT DISTINCT telegram_id FROM users WHERE status = 'active' AND telegram_id IS NOT NULL")
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]
        
    elif target == "mentors":
        cursor = await conn.execute("SELECT DISTINCT telegram_id FROM users WHERE role = 'mentor' AND status = 'active' AND telegram_id IS NOT NULL")
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows if r["telegram_id"]]
        
    elif target.startswith("mentor_direct_"):
        try:
            mid = int(target.replace("mentor_direct_", ""))
            cursor = await conn.execute(
                "SELECT telegram_id FROM users WHERE id = ? AND status = 'active' AND telegram_id IS NOT NULL",
                (mid,),
            )
            row = await cursor.fetchone()
            return [row["telegram_id"]] if row and row["telegram_id"] else []
        except Exception as e:
            logger.error("Target user ids (mentor direct) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("mentor_") and "_course_" in target:
        # e.g. mentor_3_course_1
        try:
            parts = target.split("_")
            mentor_id = int(parts[1])
            cid = int(parts[3])
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                    u.id IN (
                        SELECT ag.user_id
                        FROM access_grants ag
                        JOIN license_nodes ln ON ln.id = ag.node_id
                        WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                    )
                    OR u.id IN (
                        SELECT cm.user_id
                        FROM cabinet_members cm
                        JOIN cabinets c ON c.id = cm.cabinet_id
                        JOIN license_nodes ln ON ln.id = c.owner_node_id
                        JOIN access_grants ag ON ag.user_id = cm.user_id AND ag.node_id = ln.id
                        WHERE ln.owner_user_id = ? AND ag.course_id = ? AND ag.status = 'active'
                    )
                )
                """,
                (mentor_id, cid, mentor_id, cid),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids (mentor+course) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("mentor_"):
        # e.g. mentor_3
        try:
            mentor_id = int(target.replace("mentor_", ""))
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND (
                    u.id IN (
                        SELECT ag.user_id
                        FROM access_grants ag
                        JOIN license_nodes ln ON ln.id = ag.node_id
                        WHERE ln.owner_user_id = ? AND ag.status = 'active'
                    )
                    OR u.id IN (
                        SELECT cm.user_id
                        FROM cabinet_members cm
                        JOIN cabinets c ON c.id = cm.cabinet_id
                        JOIN license_nodes ln ON ln.id = c.owner_node_id
                        WHERE ln.owner_user_id = ? AND cm.role_in_cabinet = 'student'
                    )
                )
                """,
                (mentor_id, mentor_id),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids (mentor all) olishda xato (%s): %s", target, e)
            return []

    elif target.startswith("course_"):
        try:
            cid = int(target.replace("course_", ""))
            cursor = await conn.execute(
                """
                SELECT DISTINCT u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL AND u.status = 'active' AND u.id IN (
                    SELECT user_id FROM access_grants WHERE course_id = ? AND status = 'active'
                    UNION
                    SELECT user_id FROM lesson_views lv JOIN lessons l ON l.id = lv.lesson_id WHERE l.course_id = ?
                )
                """,
                (cid, cid),
            )
            rows = await cursor.fetchall()
            return [r["telegram_id"] for r in rows if r["telegram_id"]]
        except Exception as e:
            logger.error("Target user ids olishda xato (%s): %s", target, e)
            return []
            
    return []


# ==========================================
# 1. /admin BUYRUG'I
# ==========================================

@router.message(Command("admin"))
async def handle_admin_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("⚠️ Sizda ushbu buyruqdan foydalanish huquqi yo'q.")
        return
        
    await state.clear()
    courses, counts = await _get_courses_and_counts()
    
    txt = (
        "👑 <b>Admin Boshqaruv Markazi</b>\n\n"
        f"👤 <b>Admin:</b> {message.from_user.full_name}\n"
        f"🌐 <b>Jami foydalanuvchilar:</b> {counts.get('all', 0)} ta\n"
        f"🎓 <b>Jami Mentorlar:</b> {counts.get('mentors', 0)} ta\n\n"
        "Pastdagi menyu orqali kerakli bo'limni tanlang 👇"
    )
    
    await message.answer(
        txt,
        reply_markup=ADMIN_MENU,
        parse_mode="HTML",
    )


# ==========================================
# 2. XABAR YUBORISHNI BOSHLASH
# ==========================================

@router.message(Command("broadcast", "admin_send", "xabar", "send"))
@router.message(F.text.in_(["📢 Xabar yuborish", "Xabar yuborish", "📢 Xabar Yuborish (Broadcast)"]))
async def start_broadcast_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        return
        
    await state.clear()
    courses, counts = await _get_courses_and_counts()
    
    txt = (
        "📢 <b>Xabar yuborish</b>\n\n"
        "Qaysi guruhga xabar yubormoqchisiz? Tanlang:\n"
    )
    await message.answer(
        txt,
        reply_markup=get_broadcast_target_keyboard(courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_target)


@router.callback_query(F.data == "admin_action:broadcast")
async def process_admin_broadcast_action(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return
        
    await state.clear()
    courses, counts = await _get_courses_and_counts()
    
    txt = (
        "📢 <b>Xabar yuborish</b>\n\n"
        "Qaysi guruhga xabar yubormoqchisiz? Tanlang:\n"
    )
    await callback.message.edit_text(
        txt,
        reply_markup=get_broadcast_target_keyboard(courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_target)
    await callback.answer()


@router.message(F.text.in_(["📊 Platforma statistikasi", "📊 Platforma Analitikasi"]))
@router.callback_query(F.data == "admin_action:stats")
async def process_admin_stats(event: Message | CallbackQuery) -> None:
    user_id = event.from_user.id if event.from_user else 0
    if user_id not in settings.bot.admin_ids:
        if isinstance(event, CallbackQuery):
            await event.answer("Ruxsatingiz yo'q!", show_alert=True)
        return
        
    courses, counts = await _get_courses_and_counts()
    
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
        await event.message.edit_text(
            txt,
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML",
        )
        await event.answer()
    else:
        await event.answer(
            txt,
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML",
        )


# ==========================================
# 3. AUDITORIYANI TANLASH VA MENTOR FILTRLASH
# ==========================================

@router.callback_query(F.data == "bcast_target:choose_mentor")
async def process_choose_mentor_step(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return
        
    mentors = await _get_mentors_list()
    if not mentors:
        await callback.answer("⚠️ Hozircha faol mentorlar mavjud emas!", show_alert=True)
        return

    txt = (
        "👤 <b>Kerakli Mentorni tanlang:</b>\n\n"
        "Quyidagi ro'yxatdan o'quvchilariga xabar yubormoqchi bo'lgan mentorni tanlang 👇"
    )
    await callback.message.edit_text(
        txt,
        reply_markup=get_broadcast_mentors_keyboard(mentors),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_mentor)
    await callback.answer()


@router.callback_query(F.data == "bcast_back_target")
async def process_back_to_target(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    courses, counts = await _get_courses_and_counts()
    txt = (
        "📢 <b>Xabar yuborish</b>\n\n"
        "Qaysi guruhga xabar yubormoqchisiz? Tanlang:\n"
    )
    await callback.message.edit_text(
        txt,
        reply_markup=get_broadcast_target_keyboard(courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_target)
    await callback.answer()


@router.callback_query(F.data.startswith("bcast_mentor:"))
async def process_mentor_selected(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    mentor_id = int(callback.data.split(":", 1)[1])
    mentor_info, courses, counts = await _get_mentor_courses_and_counts(mentor_id)
    m_name = mentor_info.get("full_name") or f"Mentor #{mentor_id}"

    txt = (
        f"👨‍🏫 <b>Tanlangan Mentor:</b> {m_name}\n\n"
        f"Qaysi yo'nalishdagi shogirdlariga xabar yubormoqchisiz? Tanlang 👇"
    )
    await callback.message.edit_text(
        txt,
        reply_markup=get_broadcast_mentor_courses_keyboard(mentor_id, m_name, courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_mentor_course)
    await callback.answer()


@router.callback_query(F.data.startswith("bcast_target:"))
async def process_target_selection(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return
        
    target = callback.data.split(":", 1)[1]
    
    # Check if target is choose_mentor, ignore here as it has its own handler
    if target == "choose_mentor":
        return

    # Determine recipient count and title
    recipient_ids = await _get_target_user_ids(target)
    target_count = len(recipient_ids)
    
    courses, counts = await _get_courses_and_counts()
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}
    
    target_label = "Auditoriya"
    if target == "all":
        target_label = "🌐 Barcha foydalanuvchilar"
    elif target == "mentors":
        target_label = "🎓 Barcha Mentorlarning O'ZIGA"
    elif target.startswith("mentor_direct_"):
        mid = int(target.replace("mentor_direct_", ""))
        m_info, _, _ = await _get_mentor_courses_and_counts(mid)
        target_label = f"✉️ Faqat Mentor «{m_info['full_name']}»ning O'ZIGA"
    elif target.startswith("mentor_") and "_course_" in target:
        parts = target.split("_")
        mid = int(parts[1])
        cid = int(parts[3])
        m_info, _, _ = await _get_mentor_courses_and_counts(mid)
        target_label = f"🎯 {m_info['full_name']}ning «{course_map.get(cid, cid)}» shogirdlari"
    elif target.startswith("mentor_"):
        mid = int(target.replace("mentor_", ""))
        m_info, _, _ = await _get_mentor_courses_and_counts(mid)
        target_label = f"👨‍🏫 {m_info['full_name']}ning BARCHA shogirdlari"
    elif target.startswith("course_"):
        cid = int(target.replace("course_", ""))
        target_label = f"📚 «{course_map.get(cid, cid)}» kursi talabalari"
        
    if target_count == 0:
        await callback.answer(f"⚠️ Bu guruhda ({target_label}) hozircha faol foydalanuvchi yo'q!", show_alert=True)
        return
        
    await state.update_data(
        target=target,
        target_label=target_label,
        target_count=target_count,
    )
    
    await callback.message.edit_text(
        f"🎯 <b>Tanlandi:</b> {target_label} ({target_count} ta qabul qiluvchi)\n\n"
        f"✍️ <b>Yubormoqchi bo'lgan xabaringizni jo'nating:</b>\n"
        f"<i>(Matn, rasm, video, audio yoki fayl)</i>",
        reply_markup=get_broadcast_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.answer()


# ==========================================
# 4. XABARNI QABUL QILISH VA PREVIEW
# ==========================================

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        return
        
    data = await state.get_data()
    target_label = data.get("target_label", "Auditoriya")
    target_count = data.get("target_count", 0)
    
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    
    await message.answer(
        f"📋 <b>Xabarni tasdiqlash</b>:\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Qabul qiluvchilar:</b> {target_label} ({target_count} ta)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Yuqoridagi xabaringiz barchaga yetkazilsinmi?</i>",
        reply_markup=get_broadcast_confirm_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.confirming)


# ==========================================
# 5. TASDIQLASH VA YUBORISH JARAYONI
# ==========================================

@router.callback_query(F.data.startswith("bcast_confirm:"), BroadcastStates.confirming)
async def process_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return
        
    action = callback.data.split(":", 1)[1]
    
    if action == "retry":
        data = await state.get_data()
        target_label = data.get("target_label", "Auditoriya")
        await callback.message.edit_text(
            f"🎯 <b>Auditoriya:</b> {target_label}\n\n"
            f"✍️ <b>Yangi xabaringizni yuboring:</b>",
            reply_markup=get_broadcast_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(BroadcastStates.waiting_for_message)
        await callback.answer()
        return

    data = await state.get_data()
    target = data.get("target", "all")
    target_label = data.get("target_label", "Auditoriya")
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    
    recipient_ids = await _get_target_user_ids(target)
    total_recipients = len(recipient_ids)
    
    if total_recipients == 0:
        await callback.message.edit_text("⚠️ Qabul qiluvchilar topilmadi.", parse_mode="HTML")
        await state.clear()
        return
        
    status_msg = await callback.message.edit_text(
        f"🚀 <b>Xabar yuborilmoqda...</b>\n\n"
        f"🎯 <b>Guruh:</b> {target_label}\n"
        f"⏳ <b>Jarayon:</b> 0 / {total_recipients}",
        parse_mode="HTML",
    )
    
    sent_count = 0
    blocked_count = 0
    start_time = time.time()
    
    for idx, recipient_id in enumerate(recipient_ids, 1):
        try:
            await bot.copy_message(
                chat_id=recipient_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            sent_count += 1
        except TelegramForbiddenError:
            blocked_count += 1
            logger.info("Foydalanuvchi botni bloklagan: %s", recipient_id)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=recipient_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
                sent_count += 1
            except Exception:
                blocked_count += 1
        except TelegramAPIError as e:
            blocked_count += 1
            logger.warning("Broadcast xatosi (%s): %s", recipient_id, e)
        except Exception as e:
            blocked_count += 1
            logger.error("Kutilmagan broadcast xatosi (%s): %s", recipient_id, e)
            
        await asyncio.sleep(0.04)
        
        if idx % 25 == 0 or idx == total_recipients:
            percent = int((idx / total_recipients) * 100)
            try:
                await status_msg.edit_text(
                    f"🚀 <b>Xabar yuborilmoqda...</b>\n\n"
                    f"🎯 <b>Guruh:</b> {target_label}\n"
                    f"⏳ <b>Jarayon:</b> {idx} / {total_recipients} ({percent}%)\n"
                    f"🟢 Yetkazildi: {sent_count} | 🔴 Yetib bormadi: {blocked_count}",
                    parse_mode="HTML",
                )
            except Exception:
                pass
                
    elapsed = round(time.time() - start_time, 1)
    
    await status_msg.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"🎯 <b>Guruh:</b> {target_label}\n"
        f"🟢 <b>Yetkazildi:</b> {sent_count} ta\n"
        f"🔴 <b>Yetib bormadi:</b> {blocked_count} ta\n"
        f"⏱ <b>Vaqt:</b> {elapsed} soniya",
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer("Tugadi!", show_alert=False)


# ==========================================
# 6. BEKOR QILISH HANDLERI
# ==========================================

@router.callback_query(F.data == "bcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ <b>Xabar yuborish bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer("Bekor qilindi")
