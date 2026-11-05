"""
Mentorning shaxsiy kabineti va boshqaruv menyusi handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.mentor import get_mentor_card_manage_keyboard
from bot.handlers.common.profile import _resolve_bot_username
from db.repositories.user_repo import User
from services.cabinet_service import CabinetService
from services.mentor_service import MentorService

logger = logging.getLogger(__name__)
router = Router(name="mentor_cabinet")


@router.message(F.text == "👥 Mening talabalarim")
async def list_students(message: Message, user: User) -> None:
    cabinet_service = CabinetService.create_default()
    students = await cabinet_service.get_mentor_students(user.id)

    if not students:
        has_cabinets = await cabinet_service.has_owned_cabinets(user.id)
        if not has_cabinets:
            await message.answer("Sizda hali kabinet yo'q (hali birorta ham talaba xarid qilmagan).")
        else:
            await message.answer("Hozircha kabinetlaringizda talabalar yo'q.")
        return

    lines: list[str] = ["<b>👥 Sizning talabalaringiz:</b>\n"]
    for count, s in enumerate(students, 1):
        joined = s["joined_at"][:10] if s.get("joined_at") else "—"
        name = s["full_name"] or "Noma'lum"
        lines.append(f"{count}. <b>{name}</b> (ID: <code>{s['telegram_id']}</code>, sana: {joined})")

    await message.answer("\n".join(lines))


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message, user: User) -> None:
    mentor_service = MentorService()
    stats = await mentor_service.get_mentor_statistics(user.id)

    if not stats:
        await message.answer("Statistika uchun ma'lumot topilmadi.")
        return

    stage = stats["stage"]
    stage_title = (
        "⏳ 1-bosqich: Limit davri (15 kun)"
        if stage == "limit"
        else "🤝 2-bosqich: Hamkorlik davri (6 oy)"
    )
    lines: list[str] = [f"<b>📊 Mentorlik statistikasi</b>\n\n📌 <b>Holat:</b> {stage_title}"]

    # Agar Limit davrida bo'lsa, limit qoldiqlarini ko'rsatamiz
    if stage == "limit":
        quotas = stats["quotas"]
        if quotas:
            lines.append("\n🎁 <b>Tarif bo'yicha bepul dostup limitlari:</b>")
            for q in quotas:
                lines.append(
                    f"• <b>{q.course_title}:</b> {q.remaining}/{q.total_quota} ta qoldi (sotilgan: {q.used_quota})"
                )
        lines.append(
            "\n<i>ℹ️ 15 kun ichida sotilgan dostuplardan 100% daromad o'zingizda qoladi. Limit tugagach, 15 kun to'lishi kutiladi.</i>"
        )

    # AI Token va Server xarajatlari hisoboti
    ai_summary = stats["ai_summary"]
    server_summary = stats["server_summary"]

    lines.append("\n<b>💡 Shogirdlar Infratuzilma Xarajatlari:</b>")
    lines.append(
        f"• 🤖 <b>AI Tyutor:</b> {ai_summary['total_cost_sum']:,.0f} so'm ({ai_summary['total_queries']} ta savol)"
    )
    lines.append(
        f"• 🖥 <b>Server & Video:</b> {server_summary['total_cost_sum']:,.0f} so'm ({server_summary['total_video_views']} ta stream)"
    )

    # Talabalar faolligi
    students_activity = stats["students_activity"]
    if students_activity:
        lines.append("\n<b>👥 Talabalar faolligi:</b>")
        for count, a in enumerate(students_activity, 1):
            last = a["last_activity"][:16] if a.get("last_activity") else "hali faol emas"
            name = a["full_name"] or "Noma'lum"
            lines.append(
                f"{count}. <b>{name}</b>\n"
                f"   ├ Ko'rgan darslari: <b>{a['lessons_watched']} ta</b>\n"
                f"   └ Oxirgi faollik: <i>{last}</i>"
            )

    await message.answer("\n".join(lines))


@router.message(F.text == "🔗 Kurslarim sotuv havolalari")
@router.message(F.text == "🔗 Taklif havolam")
@router.message(F.text == "🔗 Taklif havolalari")
async def show_referral_link(message: Message, user: User) -> None:
    mentor_service = MentorService()
    ref_data = await mentor_service.get_mentor_referral_data(user.id)
    if not ref_data:
        await message.answer("Sizda hali faol litsenziya tuguni (kabinet) mavjud emas.")
        return

    node_id, courses = ref_data
    bot_username = await _resolve_bot_username(message.bot)

    part1_lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Havolalaringiz (1/2):</b>\n",
        "O'z shogirdlaringizga mos havolani yuboring. Talaba havola orqali kirganda <b>aynan sizning kabinetingizga</b> birikadi:\n",
        "💳 <b>1. ONLINE SOTUV HAVOLALARI (Talaba Click/Payme orqali to'laydi):</b>",
        "<i>Talabaga yuborasiz, u Mini Appda to'lov qilgach darslar ochiladi va sotuv hisobingizga yoziladi:</i>",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        part1_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{ref_link}</code>")

    part1_lines.append("\n💡 <i>Nusxalash uchun havola ustiga bir marta bosing.</i>")

    part2_lines = [
        "🎁 <b>Lichkada To'laganlar Uchun Havolalar (2/2):</b>\n",
        "<i>Agar talaba pulni kartangizga yoki naqd to'lagan bo'lsa, ushbu havolani bering. Darslar darhol ochiladi:</i>",
    ]

    for c in courses:
        open_link = f"https://t.me/{bot_username}?start=open_node_{node_id}_course_{c.id}"
        part2_lines.append(f"• <b>{c.title}</b>:\n  👉 <code>{open_link}</code>")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    part2_lines.append(f"\n🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>")
    part2_lines.append("\n💡 <i>Nusxalash uchun havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(part1_lines))
    await message.answer("\n".join(part2_lines))


@router.message(F.text == "💳 Ulangan karta (Avto-to'lov)")
async def show_mentor_card(message: Message, user: User) -> None:
    mentor_service = MentorService()
    card_status = await mentor_service.get_mentor_card_status(user.id)

    card = card_status["card"]
    node = card_status["node"]
    unsettled = card_status["unsettled"]

    status_badge = "✅ Faol"
    debt_text = ""
    if node and unsettled:
        if node.status == "suspended":
            status_badge = "⛔️ VAQTINCHA TO'XTATILGAN"
            debt_text = (
                f"\n\n🚨 <b>Diqqat! Yangi o'quvchilar qabuli to'xtatilgan!</b>\n"
                f"• To'lanmagan royalti summasi: <b>{unsettled['total_amount']:,.0f} so'm</b>\n"
                f"• O'qitilgan: <b>{unsettled['sales_count']} ta o'quvchi</b>\n\n"
                f"<i>Qabulni qayta faollashtirish uchun kartangiz hisobini to'ldiring yoki ma'muriyatga murojaat qiling.</i>"
            )
        elif unsettled["total_amount"] > 0:
            debt_text = (
                f"\n\n⏳ <b>Joriy hisoblangan royalti:</b> "
                f"{unsettled['total_amount']:,.0f} so'm ({unsettled['sales_count']}/10 ta o'quvchi)"
            )

    if card:
        text = (
            f"💳 <b>Ulangan to'lov kartangiz:</b>\n\n"
            f"• Raqami: <code>{card.card_number_masked}</code>\n"
            f"• Tizim: <b>{card.provider.upper()} Subscribe</b>\n"
            f"• Kabinet holati: <b>{status_badge}</b>\n"
            f"• Avto-to'lov: <b>Yoqilgan ✅</b>"
            f"{debt_text}\n\n"
            f"ℹ️ <i>Hamkorlik davrida har 10 ta o'quvchi xarididan so'ng hisoblangan royalti ushbu kartangizdan avtomatik yechiladi.</i>"
        )
    else:
        text = (
            f"💳 <b>To'lov kartasi ulanmagan</b>\n\n"
            f"• Kabinet holati: <b>{status_badge}</b>"
            f"{debt_text}\n\n"
            f"Hamkorlik davrida hisoblangan royalti komissiyalari o'z vaqtida va qulay to'lanishi uchun "
            f"kartangizni 1 marta ulab qo'yishingiz lozim.\n\n"
            f"Kartangiz ulanganda tizim har 10 ta o'quvchi o'qitilganda platforma ulushini avtomatik yechib oladi."
        )

    keyboard = get_mentor_card_manage_keyboard()
    await message.answer(text, reply_markup=keyboard)
