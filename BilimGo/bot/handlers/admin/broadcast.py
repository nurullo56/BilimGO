"""
Admin broadcast handlerlari.
DB helper funksiyalar _admin_db.py da, statistika stats.py da.
"""
from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.admin._admin_db import (
    get_courses_and_counts,
    get_mentors_list,
    get_mentor_courses_and_counts,
    get_target_user_ids,
)
from bot.keyboards.admin_kb import (
    ADMIN_MENU,
    get_broadcast_cancel_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_mentor_courses_keyboard,
    get_broadcast_mentors_keyboard,
    get_broadcast_target_keyboard,
)
from bot.states.fsm_states import BroadcastStates
from core.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")


# ==========================================
# 1. XABAR YUBORISHNI BOSHLASH
# ==========================================

@router.message(Command("broadcast", "admin_send", "xabar", "send"))
@router.message(F.text.in_(["📢 Xabar yuborish", "Xabar yuborish", "📢 Xabar Yuborish (Broadcast)"]))
async def start_broadcast_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        return

    await state.clear()
    courses, counts = await get_courses_and_counts()

    await message.answer(
        "📢 <b>Xabar yuborish</b>\n\nQaysi guruhga xabar yubormoqchisiz? Tanlang:\n",
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
    courses, counts = await get_courses_and_counts()

    await callback.message.edit_text(
        "📢 <b>Xabar yuborish</b>\n\nQaysi guruhga xabar yubormoqchisiz? Tanlang:\n",
        reply_markup=get_broadcast_target_keyboard(courses, counts),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.choosing_target)
    await callback.answer()


# ==========================================
# 2. AUDITORIYANI TANLASH VA MENTOR FILTRLASH
# ==========================================

@router.callback_query(F.data == "bcast_target:choose_mentor")
async def process_choose_mentor_step(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    mentors = await get_mentors_list()
    if not mentors:
        await callback.answer("Hozircha faol mentorlar mavjud emas!", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 <b>Kerakli Mentorni tanlang:</b>\n\n"
        "Quyidagi ro'yxatdan o'quvchilariga xabar yubormoqchi bo'lgan mentorni tanlang 👇",
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

    courses, counts = await get_courses_and_counts()
    await callback.message.edit_text(
        "📢 <b>Xabar yuborish</b>\n\nQaysi guruhga xabar yubormoqchisiz? Tanlang:\n",
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
    mentor_info, courses, counts = await get_mentor_courses_and_counts(mentor_id)
    m_name = mentor_info.get("full_name") or f"Mentor #{mentor_id}"

    await callback.message.edit_text(
        f"👨‍🏫 <b>Tanlangan Mentor:</b> {m_name}\n\n"
        "Qaysi yo'nalishdagi shogirdlariga xabar yubormoqchisiz? Tanlang 👇",
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
    if target == "choose_mentor":
        return

    recipient_ids = await get_target_user_ids(target)
    target_count = len(recipient_ids)

    courses, counts = await get_courses_and_counts()
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}

    target_label = "Auditoriya"
    if target == "all":
        target_label = "🌐 Barcha foydalanuvchilar"
    elif target == "mentors":
        target_label = "🎓 Barcha Mentorlarning O'ZIGA"
    elif target.startswith("mentor_direct_"):
        mid = int(target.replace("mentor_direct_", ""))
        m_info, _, _ = await get_mentor_courses_and_counts(mid)
        target_label = f"✉️ Faqat Mentor «{m_info['full_name']}»ning O'ZIGA"
    elif target.startswith("mentor_") and "_course_" in target:
        parts = target.split("_")
        mid = int(parts[1])
        cid = int(parts[3])
        m_info, _, _ = await get_mentor_courses_and_counts(mid)
        target_label = f"🎯 {m_info['full_name']}ning «{course_map.get(cid, cid)}» shogirdlari"
    elif target.startswith("mentor_"):
        mid = int(target.replace("mentor_", ""))
        m_info, _, _ = await get_mentor_courses_and_counts(mid)
        target_label = f"👨‍🏫 {m_info['full_name']}ning BARCHA shogirdlari"
    elif target.startswith("course_"):
        cid = int(target.replace("course_", ""))
        target_label = f"📚 «{course_map.get(cid, cid)}» kursi talabalari"

    if target_count == 0:
        await callback.answer(
            f"Bu guruhda ({target_label}) hozircha faol foydalanuvchi yo'q!",
            show_alert=True,
        )
        return

    await state.update_data(target=target, target_label=target_label, target_count=target_count)
    await callback.message.edit_text(
        f"🎯 <b>Tanlandi:</b> {target_label} ({target_count} ta qabul qiluvchi)\n\n"
        "✍️ <b>Yubormoqchi bo'lgan xabaringizni jo'nating:</b>\n"
        "<i>(Matn, rasm, video, audio yoki fayl)</i>",
        reply_markup=get_broadcast_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.answer()


# ==========================================
# 3. XABARNI QABUL QILISH VA PREVIEW
# ==========================================

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        return

    data = await state.get_data()
    target_label = data.get("target_label", "Auditoriya")
    target_count = data.get("target_count", 0)

    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)

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
# 4. TASDIQLASH VA YUBORISH
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
            f"🎯 <b>Auditoriya:</b> {target_label}\n\n✍️ <b>Yangi xabaringizni yuboring:</b>",
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

    recipient_ids = await get_target_user_ids(target)
    total_recipients = len(recipient_ids)

    if total_recipients == 0:
        await callback.message.edit_text("Qabul qiluvchilar topilmadi.", parse_mode="HTML")
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
                chat_id=recipient_id, from_chat_id=from_chat_id, message_id=message_id
            )
            sent_count += 1
        except TelegramForbiddenError:
            blocked_count += 1
            logger.info("Foydalanuvchi botni bloklagan: %s", recipient_id)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=recipient_id, from_chat_id=from_chat_id, message_id=message_id
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
            except Exception as exc:
                import logging
                logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

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
# 5. BEKOR QILISH
# ==========================================

@router.callback_query(F.data == "bcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ <b>Xabar yuborish bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer("Bekor qilindi")
