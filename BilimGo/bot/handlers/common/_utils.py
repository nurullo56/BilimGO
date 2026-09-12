"""
Common handlers uchun ichki yordamchi funksiyalar va umumiy konstantalar.
start.py, mentor_add.py va profile.py tomonidan ishlatiladi.
"""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.fsm.state import State, StatesGroup

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

_ROLE_LABELS = {
    "student": "👨‍🎓 Talaba (O'quvchi)",
    "mentor": "👨‍🏫 Mentor (Kurator)",
    "admin": "👑 Super Admin / Bosh Mentor",
}


class AddMentorState(StatesGroup):
    waiting_for_tg_id = State()


def _parse_payload(payload: str | None) -> tuple[int | None, int | None, bool, int | None]:
    """Payload'dan course_id, node_id, is_mentor_invite va mentor_target_id ni aniqlaydi."""
    if not payload:
        return None, None, False, None

    p_lower = payload.lower().strip()
    course_id: int | None = None
    node_id: int | None = None
    is_mentor_invite: bool = "mentor" in p_lower or "kurator" in p_lower
    mentor_target_id: int | None = None

    if is_mentor_invite:
        parts = p_lower.split("mentor_")
        if len(parts) > 1 and parts[1].split("_")[0].isdigit():
            mentor_target_id = int(parts[1].split("_")[0])

    if "course_" in p_lower:
        part = p_lower.split("course_")[1].split("_")[0]
        if part.isdigit():
            course_id = int(part)
    elif "course-" in p_lower:
        part = p_lower.split("course-")[1].split("_")[0]
        if part.isdigit():
            course_id = int(part)
    elif "kurs_" in p_lower:
        part = p_lower.split("kurs_")[1].split("_")[0]
        if part.isdigit():
            course_id = int(part)
    elif "logist" in p_lower:
        course_id = 1
    elif "tgads" in p_lower or "telegram" in p_lower:
        course_id = 2
    elif "konkurs" in p_lower or "aksiya" in p_lower:
        course_id = 3
    elif "sayt" in p_lower or "web" in p_lower:
        course_id = 4
    elif "xitoy" in p_lower or "import" in p_lower:
        course_id = 5
    elif p_lower.startswith("c") and p_lower[1:].isdigit():
        course_id = int(p_lower[1:])
    elif p_lower.isdigit() and int(p_lower) <= 10:
        course_id = int(p_lower)

    if "node_" in p_lower:
        n_part = p_lower.split("node_")[1].split("_")[0]
        if n_part.isdigit():
            node_id = int(n_part)
    elif "ref_" in p_lower:
        n_part = p_lower.split("ref_")[1].split("_")[0]
        if n_part.isdigit():
            node_id = int(n_part)
    elif p_lower.isdigit() and int(p_lower) > 10:
        node_id = int(p_lower)

    return course_id, node_id, is_mentor_invite, mentor_target_id


async def _handle_student_mentor_binding(
    bot: Bot,
    student: User,
    payload: str | None,
    from_tg_user: any = None,
) -> tuple[str, any]:
    """Talabani mentor kabinetiga biriktirish, kurs dostupini berish va mentorga bildirishnoma yuborish."""
    if not payload:
        return "", None

    course_id, node_id, is_mentor_invite, mentor_target_id = _parse_payload(payload)
    conn = database.conn
    course_repo = CourseRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    user_repo = UserRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    target_course = await course_repo.get_by_id(course_id) if course_id else None
    mentor_info = ""

    node = None
    if node_id:
        node = await license_node_repo.get_by_id(node_id)
    elif mentor_target_id:
        mentor_user_temp = await user_repo.get_by_telegram_id(mentor_target_id)
        if mentor_user_temp:
            cursor = await conn.execute(
                "SELECT id FROM license_nodes WHERE owner_user_id = ? ORDER BY id DESC LIMIT 1",
                (mentor_user_temp.id,),
            )
            node_row = await cursor.fetchone()
            if node_row:
                node = await license_node_repo.get_by_id(node_row["id"])

    if node:
        if node.id > 1 and node.status in ("suspended", "terminated"):
            logger.warning(
                "Talaba %s to'xtatilgan node #%s ga ulanmoqchi bo'ldi. Bosh kabinetga yo'naltirilmoqda.",
                student.id, node.id,
            )
            mentor_user = await user_repo.get_by_id(node.owner_user_id)
            mentor_name = mentor_user.full_name if mentor_user else "Mentor"
            mentor_info = (
                f"\n\nℹ️ <i>Hurmatli o'quvchi, <b>{mentor_name}</b> ning yangi shogirdlarni qabul qilish jarayoni "
                f"vaqtincha to'xtatilganligi sababli, siz to'g'ridan-to'g'ri «BilimGo» rasmiy ta'lim kabinetiga yo'naltirildingiz.</i>"
            )
            node = await license_node_repo.get_by_id(1)

    if node:
        if not target_course and node.course_id:
            target_course = await course_repo.get_by_id(node.course_id)

        cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
        cabinet = await cabinet_service.get_or_create_for_node(node.id)
        is_already_member = await cabinet_repo.is_member(cabinet.id, student.id)

        if not is_already_member and student.id != node.owner_user_id:
            await cabinet_repo.add_member(cabinet.id, student.id, role="student")
            mentor_user = await user_repo.get_by_id(node.owner_user_id)
            mentor_name = mentor_user.full_name if mentor_user else "Mentor"
            if not mentor_info:
                mentor_info = f"\n\n👨‍🏫 Siz mentoringiz <b>{mentor_name}</b> ning shaxsiy kabinetiga biriktirildingiz! 🎉"

            if mentor_user and mentor_user.telegram_id:
                try:
                    course_title = target_course.title if target_course else "Umumiy ta'lim"
                    tg_uname = getattr(from_tg_user, "username", None) if from_tg_user else None
                    username_str = f"@{tg_uname}" if tg_uname else "Mavjud emas"
                    phone_str = student.phone or "Kiritilmagan"
                    student_display = student.full_name or (from_tg_user.full_name if from_tg_user else "Yangi talaba")

                    notify_text = (
                        f"🔔 <b>Yangi o'quvchi ro'yxatdan o'tdi va o'qishni boshladi!</b> 🎓\n\n"
                        f"👤 <b>O'quvchi:</b> <b>{student_display}</b>\n"
                        f"📱 <b>Telefon:</b> <code>{phone_str}</code>\n"
                        f"💬 <b>Telegram:</b> {username_str} (ID: <code>{student.telegram_id}</code>)\n"
                        f"📚 <b>Kurs:</b> «{course_title}»\n"
                        f"🏢 <b>Kabinet:</b> {cabinet.display_name}\n\n"
                        f"👏 <i>O'quvchi sizning taklif havolangiz orqali platformaga kirdi.</i>"
                    )
                    await bot.send_message(
                        chat_id=mentor_user.telegram_id, text=notify_text, parse_mode="HTML"
                    )
                    logger.info("Mentor %s ga yangi o'quvchi (%s) xabari yuborildi.", mentor_user.telegram_id, student.id)
                except Exception as e:
                    logger.warning("Mentorga xabar yuborishda xatolik (%s): %s", mentor_user.telegram_id, e)

    if target_course:
        await access_grant_repo.grant_course_access(
            user_id=student.id, course_id=target_course.id, granted_via_sale_id=0,
        )

    return mentor_info, target_course


async def _notify_super_mentors_about_mentor_activation(
    bot: Bot, mentor: User, node_id: int, cabinet_name: str, from_tg_user=None
) -> None:
    tg_uname = getattr(from_tg_user, "username", None) if from_tg_user else None
    username_str = f"@{tg_uname}" if tg_uname else (f"@{mentor.username}" if mentor.username else "Mavjud emas")
    phone_str = mentor.phone or "Kiritilmagan"
    name_display = mentor.full_name or (from_tg_user.full_name if from_tg_user else "Mentor")

    notify_text = (
        f"👑 <b>Yangi Mentor ro'yxatdan o'tdi / botni faollashtirdi!</b> 👨‍🏫\n\n"
        f"👤 <b>Mentor:</b> <b>{name_display}</b>\n"
        f"📱 <b>Telefon:</b> <code>{phone_str}</code>\n"
        f"💬 <b>Telegram:</b> {username_str} (ID: <code>{mentor.telegram_id}</code>)\n"
        f"🔑 <b>Litsenziya:</b> Node #{node_id} (Limit davri: 15 kun)\n"
        f"🏢 <b>Kabinet:</b> {cabinet_name}\n"
        f"📊 <b>Holat:</b> Barcha kurslar mentorga ochildi! ✅"
    )

    for admin_id in settings.bot.admin_ids:
        if admin_id != mentor.telegram_id:
            try:
                await bot.send_message(chat_id=admin_id, text=notify_text, parse_mode="HTML")
                logger.info("Super mentor %s ga yangi mentor (%s) xabari yuborildi.", admin_id, mentor.telegram_id)
            except Exception as e:
                logger.warning("Super mentor %s ga xabar yuborishda xatolik: %s", admin_id, e)
