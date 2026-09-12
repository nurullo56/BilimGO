from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.mentor_kb import (
    get_mentor_broadcast_cancel_keyboard,
    get_mentor_broadcast_confirm_keyboard,
    get_mentor_broadcast_target_keyboard,
)
from bot.states.fsm_states import MentorBroadcastStates
from core.config import settings
from db.database import database
from db.repositories.user_repo import User

logger = logging.getLogger(__name__)
router = Router(name="mentor_broadcast")


async def _get_mentor_courses_and_counts(mentor_id: int) -> tuple[list[dict], dict[str, int]]:
    conn = database.conn
    cursor_c = await conn.execute("SELECT id, title FROM courses ORDER BY id ASC")
    courses = [dict(r) for r in await cursor_c.fetchall()]
    
    counts: dict[str, int] = {}
    
    # 1. Barcha shogirdlar
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
    counts["all"] = r_all["cnt"] if r_all else 0
    
    # 2. Kurslar bo'yicha
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
        counts[f"course_{cid}"] = r_crs["cnt"] if r_crs else 0
        
    return courses, counts


async def _get_mentor_recipient_ids(mentor_id: int, target: str) -> list[int]:
    conn = database.conn
    
    if target == "all":
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
        
    elif target.startswith("course_"):
        try:
            cid = int(target.replace("course_", ""))
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
            logger.error("Mentor target ids olishda xato (%s): %s", target, e)
            return []
            
    return []


# ==========================================
# 1. SHOGIRDLARGA XABAR YUBORISHNI BOSHLASH
# ==========================================

@router.message(Command("mentor_broadcast", "shogirdlarga_xabar"))
@router.message(F.text.in_(["📢 Shogirdlarimga xabar", "📢 Shogirdlarimga xabar yuborish", "Shogirdlarimga xabar"]))
async def start_mentor_broadcast(message: Message, user: User, state: FSMContext) -> None:
    if user.role != "mentor" and user.telegram_id not in settings.bot.admin_ids:
        await message.answer("Ushbu funksiya faqat mentorlar uchun mo'ljallangan.")
        return

    await state.clear()
    courses, counts = await _get_mentor_courses_and_counts(user.id)
    all_count = counts.get("all", 0)

    if all_count == 0:
        await message.answer(
            "⚠️ <b>Sizda hali birorta ham birikkan shogird yo'q.</b>\n\n"
            "Taklif havolangiz orqali birinchi o'quvchi ro'yxatdan o'tganidan so'ng ushbu bo'lim orqali ularga xabar yuborishingiz mumkin.",
            parse_mode="HTML",
        )
        return

    txt = (
        "📢 <b>Shogirdlaringizga xabar yuborish</b>\n\n"
        f"Sizga jami <b>{all_count} ta</b> talaba birikkan.\n"
        "Qaysi guruhga xabar yubormoqchisiz? Tanlang 👇"
    )
    await message.answer(
        txt,
        reply_markup=get_mentor_broadcast_target_keyboard(courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(MentorBroadcastStates.choosing_target)


# ==========================================
# 2. AUDITORIYANI TANLASH
# ==========================================

@router.callback_query(F.data.startswith("mentor_bcast_target:"), MentorBroadcastStates.choosing_target)
async def process_mentor_target_selection(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    target = callback.data.split(":", 1)[1]
    courses, counts = await _get_mentor_courses_and_counts(user.id)
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}

    target_count = counts.get(target, 0)
    target_label = "Barcha shogirdlarim" if target == "all" else f"«{course_map.get(int(target.replace('course_', '')), target)}» kursi shogirdlari"

    if target_count == 0:
        await callback.answer(f"⚠️ Ushbu guruhda ({target_label}) hozircha shogird yo'q!", show_alert=True)
        return

    await state.update_data(
        target=target,
        target_label=target_label,
        target_count=target_count,
        mentor_id=user.id,
    )

    await callback.message.edit_text(
        f"🎯 <b>Tanlandi:</b> {target_label} ({target_count} ta o'quvchi)\n\n"
        f"✍️ <b>Shogirdlaringizga yubormoqchi bo'lgan xabaringizni jo'nating:</b>\n"
        f"<i>(Matn, rasm, video, audio, ovozli xabar yoki fayl)</i>",
        reply_markup=get_mentor_broadcast_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(MentorBroadcastStates.waiting_for_message)
    await callback.answer()


# ==========================================
# 3. XABARNI QABUL QILISH VA TASDIQLASH
# ==========================================

@router.message(MentorBroadcastStates.waiting_for_message)
async def process_mentor_broadcast_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target_label = data.get("target_label", "Shogirdlar")
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
        f"<i>Ushbu xabaringiz tanlangan barcha shogirdlaringizga yetkazilsinmi?</i>",
        reply_markup=get_mentor_broadcast_confirm_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(MentorBroadcastStates.confirming)


# ==========================================
# 4. YUBORISH JARAYONI
# ==========================================

@router.callback_query(F.data.startswith("mentor_bcast_confirm:"), MentorBroadcastStates.confirming)
async def process_mentor_broadcast_confirm(callback: CallbackQuery, user: User, state: FSMContext, bot: Bot) -> None:
    action = callback.data.split(":", 1)[1]

    if action == "retry":
        data = await state.get_data()
        target_label = data.get("target_label", "Shogirdlar")
        await callback.message.edit_text(
            f"🎯 <b>Auditoriya:</b> {target_label}\n\n"
            f"✍️ <b>Yangi xabaringizni yuboring:</b>",
            reply_markup=get_mentor_broadcast_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(MentorBroadcastStates.waiting_for_message)
        await callback.answer()
        return

    data = await state.get_data()
    target = data.get("target", "all")
    target_label = data.get("target_label", "Shogirdlar")
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    mentor_id = data.get("mentor_id", user.id)

    recipient_ids = await _get_mentor_recipient_ids(mentor_id, target)
    total_recipients = len(recipient_ids)

    if total_recipients == 0:
        await callback.message.edit_text("⚠️ Qabul qiluvchilar topilmadi.", parse_mode="HTML")
        await state.clear()
        return

    status_msg = await callback.message.edit_text(
        f"🚀 <b>Xabar shogirdlaringizga yuborilmoqda...</b>\n\n"
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
            logger.warning("Mentor broadcast xatosi (%s): %s", recipient_id, e)
        except Exception as e:
            blocked_count += 1
            logger.error("Kutilmagan mentor broadcast xatosi (%s): %s", recipient_id, e)

        await asyncio.sleep(0.04)

        if idx % 20 == 0 or idx == total_recipients:
            percent = int((idx / total_recipients) * 100)
            try:
                await status_msg.edit_text(
                    f"🚀 <b>Xabar shogirdlaringizga yuborilmoqda...</b>\n\n"
                    f"🎯 <b>Guruh:</b> {target_label}\n"
                    f"⏳ <b>Jarayon:</b> {idx} / {total_recipients} ({percent}%)\n"
                    f"🟢 Yetkazildi: {sent_count} | 🔴 Yetib bormadi: {blocked_count}",
                    parse_mode="HTML",
                )
            except Exception as exc:
                import logging
                logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    elapsed = round(time.time() - start_time, 1)

    await status_msg.edit_text(
        f"✅ <b>Xabaringiz shogirdlaringizga muvaffaqiyatli yetkazildi!</b>\n\n"
        f"🎯 <b>Guruh:</b> {target_label}\n"
        f"🟢 <b>Yetkazildi:</b> {sent_count} ta\n"
        f"🔴 <b>Yetib bormadi:</b> {blocked_count} ta\n"
        f"⏱ <b>Vaqt:</b> {elapsed} soniya",
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer("Yakunlandi!")


# ==========================================
# 5. BEKOR QILISH HANDLERI
# ==========================================

@router.callback_query(F.data == "mentor_bcast_cancel")
async def cancel_mentor_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ <b>Xabar yuborish bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer("Bekor qilindi")
