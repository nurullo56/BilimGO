from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from db.database import database
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import User

router = Router(name="mentor_cabinet")


async def _get_owned_cabinet_ids(user_id: int) -> list[int]:
    cursor = await database.conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ?", (user_id,)
    )
    node_ids = [r["id"] for r in await cursor.fetchall()]
    if not node_ids:
        return []

    placeholders = ",".join("?" * len(node_ids))
    cursor = await database.conn.execute(
        f"SELECT id FROM cabinets WHERE owner_node_id IN ({placeholders})", node_ids
    )
    return [r["id"] for r in await cursor.fetchall()]


@router.message(F.text == "👥 Mening talabalarim")
async def list_students(message: Message, user: User) -> None:
    cabinet_repo = CabinetRepository(database.conn)
    cabinet_ids = await _get_owned_cabinet_ids(user.id)

    if not cabinet_ids:
        await message.answer("Sizda hali kabinet yo'q (hali birorta ham talaba xarid qilmagan).")
        return

    lines: list[str] = ["<b>👥 Sizning talabalaringiz:</b>\n"]
    count = 0
    for cabinet_id in cabinet_ids:
        students = await cabinet_repo.list_students(cabinet_id)
        for s in students:
            count += 1
            joined = s["joined_at"][:10] if s.get("joined_at") else "—"
            name = s["full_name"] or "Noma'lum"
            lines.append(f"{count}. <b>{name}</b> (ID: <code>{s['telegram_id']}</code>, sana: {joined})")

    if count == 0:
        await message.answer("Hozircha kabinetlaringizda talabalar yo'q.")
        return

    await message.answer("\n".join(lines))


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message, user: User) -> None:
    from db.repositories.tariff_quota_repo import TariffQuotaRepository

    lv_repo = LessonViewRepository(database.conn)
    node_repo = LicenseNodeRepository(database.conn)
    quota_repo = TariffQuotaRepository(database.conn)

    cursor = await database.conn.execute(
        "SELECT * FROM license_nodes WHERE owner_user_id = ? ORDER BY id DESC LIMIT 1",
        (user.id,),
    )
    node_row = await cursor.fetchone()

    if not node_row:
        await message.answer("Statistika uchun ma'lumot topilmadi.")
        return

    node_id = node_row["id"]
    stage = node_row["stage"]
    stage_started = node_row["stage_started_at"]

    stage_title = "⏳ 1-bosqich: Limit davri (15 kun)" if stage == "limit" else "🤝 2-bosqich: Hamkorlik davri (6 oy)"
    lines: list[str] = [f"<b>📊 Mentorlik statistikasi</b>\n\n📌 <b>Holat:</b> {stage_title}"]

    # Agar Limit davrida bo'lsa, limit qoldiqlarini ko'rsatamiz
    if stage == "limit":
        quotas = await quota_repo.list_by_node(node_id)
        if quotas:
            lines.append("\n🎁 <b>Tarif bo'yicha bepul dostup limitlari:</b>")
            for q in quotas:
                lines.append(f"• <b>{q.course_title}:</b> {q.remaining}/{q.total_quota} ta qoldi (sotilgan: {q.used_quota})")
        lines.append("\n<i>ℹ️ 15 kun ichida sotilgan dostuplardan 100% daromad o'zingizda qoladi. Limit tugagach, 15 kun to'lishi kutiladi.</i>")

    # AI Token va Server xarajatlari hisoboti
    from db.repositories.ai_token_repo import AITokenRepository
    from db.repositories.server_expense_repo import ServerExpenseRepository

    ai_repo = AITokenRepository(database.conn)
    server_repo = ServerExpenseRepository(database.conn)

    ai_summary = await ai_repo.get_mentor_summary(user.id)
    server_summary = await server_repo.get_mentor_summary(user.id)

    lines.append("\n<b>💡 Shogirdlar Infratuzilma Xarajatlari:</b>")
    lines.append(f"• 🤖 <b>AI Tyutor:</b> {ai_summary['total_cost_sum']:,.0f} so'm ({ai_summary['total_queries']} ta savol)")
    lines.append(f"• 🖥 <b>Server & Video:</b> {server_summary['total_cost_sum']:,.0f} so'm ({server_summary['total_video_views']} ta stream)")

    # Talabalar faolligi
    cabinet_ids = await _get_owned_cabinet_ids(user.id)
    if cabinet_ids:
        lines.append("\n<b>👥 Talabalar faolligi:</b>")
        count = 0
        for cabinet_id in cabinet_ids:
            activity = await lv_repo.mentor_students_activity(cabinet_id)
            for a in activity:
                count += 1
                last = a["last_activity"][:16] if a.get("last_activity") else "hali faol emas"
                name = a["full_name"] or "Noma'lum"
                lines.append(f"{count}. <b>{name}</b>\n   ├ Ko'rgan darslari: <b>{a['lessons_watched']} ta</b>\n   └ Oxirgi faollik: <i>{last}</i>")

    await message.answer("\n".join(lines))


@router.message(F.text == "🔗 Kurslarim sotuv havolalari")
@router.message(F.text == "🔗 Taklif havolam")
@router.message(F.text == "🔗 Taklif havolalari")
async def show_referral_link(message: Message, user: User) -> None:
    from db.repositories.course_repo import CourseRepository

    cursor = await database.conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? ORDER BY id DESC LIMIT 1",
        (user.id,),
    )
    row = await cursor.fetchone()
    if not row:
        await message.answer("Sizda hali faol litsenziya tuguni (kabinet) mavjud emas.")
        return

    node_id = row["id"]
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"

    course_repo = CourseRepository(database.conn)
    courses = await course_repo.list_published()

    lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Sotuv Havolalaringiz:</b>\n",
        "O'z shogirdlaringiz yoki mijozlaringizga qaysi kursni sotmoqchi bo'lsangiz, aynan o'sha kursning havolasini yuboring. O'quvchi havola orqali kirganida, <b>aynan sizning kabinetingizga</b> birikadi va sotuv sizning hisobingizga yoziladi:\n",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        lines.append(f"📌 <b>{c.title}</b>:")
        lines.append(f"👉 <code>{ref_link}</code>\n")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    lines.append(f"🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>\n")
    lines.append("💡 <i>Nusxalash uchun istalgan havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(lines))


@router.message(F.text == "💳 Ulangan karta (Avto-to'lov)")
async def show_mentor_card(message: Message, user: User) -> None:
    from db.repositories.mentor_card_repo import MentorCardRepository
    from db.repositories.license_node_repo import LicenseNodeRepository
    from db.repositories.royalty_repo import RoyaltyLedgerRepository

    card_repo = MentorCardRepository(database.conn)
    node_repo = LicenseNodeRepository(database.conn)
    royalty_repo = RoyaltyLedgerRepository(database.conn)

    card = await card_repo.get_active_card(user.id)
    node = await node_repo.get_by_owner_id(user.id)

    status_badge = "✅ Faol"
    debt_text = ""
    if node:
        unsettled = await royalty_repo.unsettled_info_for_child_node(node.id)
        if node.status == "suspended":
            status_badge = "⛔️ VAQTINCHA TO'XTATILGAN"
            debt_text = (
                f"\n\n🚨 <b>Diqqat! Yangi o'quvchilar qabuli to'xtatilgan!</b>\n"
                f"• To'lanmagan royalti summasi: <b>{unsettled['total_amount']:,.0f} so'm</b>\n"
                f"• O'qitilgan: <b>{unsettled['sales_count']} ta o'quvchi</b>\n\n"
                f"<i>Qabulni qayta faollashtirish uchun kartangiz hisobini to'ldiring yoki ma'muriyatga murojaat qiling.</i>"
            )
        elif unsettled["total_amount"] > 0:
            debt_text = f"\n\n⏳ <b>Joriy hisoblangan royalti:</b> {unsettled['total_amount']:,.0f} so'm ({unsettled['sales_count']}/10 ta o'quvchi)"

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

    from bot.keyboards.mentor import get_mentor_card_manage_keyboard

    keyboard = get_mentor_card_manage_keyboard()
    await message.answer(text, reply_markup=keyboard)
