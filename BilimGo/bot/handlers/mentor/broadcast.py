from __future__ import annotations

import logging
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.mentor import (
    get_mentor_broadcast_cancel_keyboard,
    get_mentor_broadcast_confirm_keyboard,
    get_mentor_broadcast_target_keyboard,
)
from bot.states.fsm_states import MentorBroadcastStates
from core.config import settings
from db.repositories.admin_repo import AdminRepository
from db.repositories.user_repo import User
from services.broadcast_service import BroadcastService

logger = logging.getLogger(__name__)
router = Router(name="mentor_broadcast")


async def _get_mentor_target_ids(mentor_id: int, target: str) -> list[int]:
    target_key = f"mentor_{mentor_id}" if target == "all" else f"mentor_{mentor_id}_{target}"
    return await BroadcastService().resolve_audience(target_key)


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
    _, courses, counts = await AdminRepository().get_mentor_courses_and_counts(user.id)
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
    _, courses, counts = await AdminRepository().get_mentor_courses_and_counts(user.id)
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}

    target_count = counts.get(target, 0)
    target_label = (
        "Barcha shogirdlarim"
        if target == "all"
        else f"«{course_map.get(int(target.replace('course_', '')), target)}» kursi shogirdlari"
    )

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

    recipient_ids = await _get_mentor_target_ids(mentor_id, target)
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

    start_time = time.time()

    async def on_progress(idx: int, total: int, sent: int, failed: int) -> None:
        percent = int((idx / total) * 100)
        try:
            await status_msg.edit_text(
                f"🚀 <b>Xabar shogirdlaringizga yuborilmoqda...</b>\n\n"
                f"🎯 <b>Guruh:</b> {target_label}\n"
                f"⏳ <b>Jarayon:</b> {idx} / {total} ({percent}%)\n"
                f"🟢 Yetkazildi: {sent} | 🔴 Yetib bormadi: {failed}",
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Status message edit xatosi: %s", exc)

    broadcast_service = BroadcastService()
    result = await broadcast_service.copy_broadcast(
        bot=bot,
        admin_id=user.id,
        target_type=f"mentor_{mentor_id}_{target}",
        user_ids=recipient_ids,
        from_chat_id=from_chat_id,
        message_id=message_id,
        progress_callback=on_progress,
    )

    elapsed = round(time.time() - start_time, 1)

    await status_msg.edit_text(
        f"✅ <b>Xabaringiz shogirdlaringizga muvaffaqiyatli yetkazildi!</b>\n\n"
        f"🎯 <b>Guruh:</b> {target_label}\n"
        f"🟢 <b>Yetkazildi:</b> {result['sent']} ta\n"
        f"🔴 <b>Yetib bormadi:</b> {result['failed']} ta\n"
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
