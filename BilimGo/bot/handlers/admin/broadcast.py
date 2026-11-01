from __future__ import annotations

import logging
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.admin import (
    ADMIN_MENU,
    get_admin_panel_keyboard,
    get_broadcast_cancel_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_course_audience_keyboard,
    get_broadcast_mentor_courses_keyboard,
    get_broadcast_mentors_keyboard,
    get_broadcast_target_keyboard,
)
from bot.states.fsm_states import BroadcastStates
from core.config import settings
from db.repositories.admin_repo import AdminRepository
from services.broadcast_service import BroadcastService

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")


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
    courses, counts = await AdminRepository().get_courses_and_counts()

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
    courses, counts = await AdminRepository().get_courses_and_counts()

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
    courses, counts = await AdminRepository().get_courses_and_counts()

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

    mentors = await AdminRepository().get_mentors_list()
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

    courses, counts = await AdminRepository().get_courses_and_counts()
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
    mentor_info, courses, counts = await AdminRepository().get_mentor_courses_and_counts(mentor_id)
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


@router.callback_query(F.data.startswith("bcast_course_choose:"))
async def process_course_choose(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("Ruxsatingiz yo'q!", show_alert=True)
        return

    cid = int(callback.data.split(":", 1)[1])
    courses, counts = await AdminRepository().get_courses_and_counts()
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}
    course_title = course_map.get(cid, f"Kurs #{cid}")

    students_cnt = counts.get(f"course_students_{cid}", 0)
    all_cnt = counts.get(f"course_all_{cid}", 0)

    txt = (
        f"🎯 <b>Tanlangan Kurs:</b> {course_title}\n\n"
        f"Xabarni kimlarga yubormoqchisiz? Tanlang:\n\n"
        f"• 👥 <b>Faqat o'quvchilarga</b> — Mentorlar bu xabardan bexabar qoladi <i>(Monetizatsiya va maxsus takliflar uchun qulay)</i>\n"
        f"• 🌐 <b>Barchaga</b> — O'quvchilar va ushbu kurs ochiq bo'lgan barcha mentorlarga birdek boradi"
    )

    await callback.message.edit_text(
        txt,
        reply_markup=get_broadcast_course_audience_keyboard(cid, course_title, students_cnt, all_cnt),
        parse_mode="HTML",
    )
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
    broadcast_service = BroadcastService()
    admin_repo = AdminRepository()
    recipient_ids = await broadcast_service.resolve_audience(target)
    target_count = len(recipient_ids)

    courses, counts = await admin_repo.get_courses_and_counts()
    course_map = {c["id"]: c.get("title", f"Kurs #{c['id']}") for c in courses}

    target_label = "Auditoriya"
    if target == "all":
        target_label = "🌐 Barcha foydalanuvchilar"
    elif target == "mentors":
        target_label = "🎓 Barcha Mentorlarning O'ZIGA"
    elif target.startswith("mentor_direct_"):
        mid = int(target.replace("mentor_direct_", ""))
        m_info, _, _ = await admin_repo.get_mentor_courses_and_counts(mid)
        target_label = f"✉️ Faqat Mentor «{m_info['full_name']}»ning O'ZIGA"
    elif target.startswith("mentor_") and "_course_" in target:
        parts = target.split("_")
        mid = int(parts[1])
        cid = int(parts[3])
        m_info, _, _ = await admin_repo.get_mentor_courses_and_counts(mid)
        target_label = f"🎯 {m_info['full_name']}ning «{course_map.get(cid, cid)}» shogirdlari"
    elif target.startswith("mentor_"):
        mid = int(target.replace("mentor_", ""))
        m_info, _, _ = await admin_repo.get_mentor_courses_and_counts(mid)
        target_label = f"👨‍🏫 {m_info['full_name']}ning BARCHA shogirdlari"
    elif target.startswith("course_students_"):
        cid = int(target.replace("course_students_", ""))
        target_label = f"👥 «{course_map.get(cid, cid)}» o'quvchilari (Mentorlarsiz)"
    elif target.startswith("course_all_"):
        cid = int(target.replace("course_all_", ""))
        target_label = f"🌐 «{course_map.get(cid, cid)}» (O'quvchilar + Mentorlar)"
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

    broadcast_service = BroadcastService()
    recipient_ids = await broadcast_service.resolve_audience(target)
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

    start_time = time.time()

    async def on_progress(idx: int, total: int, sent: int, failed: int) -> None:
        percent = int((idx / total) * 100)
        try:
            await status_msg.edit_text(
                f"🚀 <b>Xabar yuborilmoqda...</b>\n\n"
                f"🎯 <b>Guruh:</b> {target_label}\n"
                f"⏳ <b>Jarayon:</b> {idx} / {total} ({percent}%)\n"
                f"🟢 Yetkazildi: {sent} | 🔴 Yetib bormadi: {failed}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    result = await broadcast_service.copy_broadcast(
        bot=bot,
        admin_id=user_id,
        target_type=target,
        user_ids=recipient_ids,
        from_chat_id=from_chat_id,
        message_id=message_id,
        progress_callback=on_progress,
    )

    elapsed = round(time.time() - start_time, 1)

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"🎯 <b>Guruh:</b> {target_label}\n"
        f"🟢 <b>Yetkazildi:</b> {result['sent']} ta\n"
        f"🔴 <b>Yetib bormadi:</b> {result['failed']} ta\n"
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
