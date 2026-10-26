from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

from bot.keyboards.admin_kb import ADMIN_MENU, get_admin_inline_webapp
from bot.keyboards.common_kb import (
    get_catalog_webapp_keyboard,
    get_direct_course_keyboard,
    get_profile_webapp_keyboard,
)
from bot.keyboards.mentor_kb import MENTOR_MENU, get_mentor_inline_webapp
from bot.keyboards.student_kb import (
    PHONE_REQUEST_KEYBOARD,
    STUDENT_MENU,
    get_student_inline_webapp,
)
from core.config import settings
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService
from services.userbot_client import UserbotClient

router = Router(name="registration")

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

    # Check if direct mentor telegram id is in payload (e.g., mentor_123456789)
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


import logging

logger = logging.getLogger(__name__)


async def _handle_student_mentor_binding(
    bot: Bot,
    student: User,
    payload: str | None,
    from_tg_user: any = None,
) -> tuple[str, any]:
    """Talabani mentor kabinetiga biriktirish, kurs dostupini berish va mentorga bot orqali bildirishnoma yuborish."""
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
        # Agar mentor litsenziyasi to'xtatilgan (suspended) bo'lsa, o'quvchini qabul qilmaymiz va bosh kabinetga yo'naltiramiz
        if node.id > 1 and node.status in ("suspended", "terminated"):
            logger.warning("Talaba %s to'xtatilgan node #%s ga ulanmoqchi bo'ldi. Bosh kabinetga yo'naltirilmoqda.", student.id, node.id)
            mentor_user = await user_repo.get_by_id(node.owner_user_id)
            mentor_name = mentor_user.full_name if mentor_user else "Mentor"
            mentor_info = (
                f"\n\nℹ️ <i>Hurmatli o'quvchi, <b>{mentor_name}</b> ning yangi shogirdlarni qabul qilish jarayoni vaqtincha to'xtatilganligi sababli, "
                f"siz to'g'ridan-to'g'ri «BilimGo» rasmiy ta'lim kabinetiga yo'naltirildingiz.</i>"
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

            # 🔔 MENTORGA TO'G'RIDAN-TO'G'RI BOTDAN BILDIRISHNOMA YUBORISH
            if mentor_user and mentor_user.telegram_id:
                try:
                    course_title = target_course.title if target_course else "Umumiy ta'lim"
                    
                    # Username handling
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
                        f"👏 <i>O'quvchi sizning taklif havolangiz orqali platformaga kirdi va darslarni boshladi. Guruh chatida u bilan muloqot qilishingiz mumkin!</i>"
                    )
                    await bot.send_message(chat_id=mentor_user.telegram_id, text=notify_text, parse_mode="HTML")
                    logger.info("Mentor %s ga yangi o'quvchi (%s) xabari yuborildi.", mentor_user.telegram_id, student.id)
                except Exception as e:
                    logger.warning("Mentorga xabar yuborishda xatolik (%s): %s", mentor_user.telegram_id, e)

    # Kurs dostupini ochish
    if target_course:
        await access_grant_repo.grant_course_access(
            user_id=student.id,
            course_id=target_course.id,
            granted_via_sale_id=0,
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
        f"📊 <b>Holat:</b> Barcha kurslar mentorga ochildi va shaxsiy sotuv havolalari yaratildi! ✅"
    )

    for admin_id in settings.bot.admin_ids:
        if admin_id != mentor.telegram_id:
            try:
                await bot.send_message(chat_id=admin_id, text=notify_text, parse_mode="HTML")
                logger.info("Super mentor %s ga yangi mentor (%s) faollashuvi xabari yuborildi.", admin_id, mentor.telegram_id)
            except Exception as e:
                logger.warning("Super mentor %s ga xabar yuborishda xatolik: %s", admin_id, e)


@router.message(CommandStart())
async def handle_start(message: Message, user: User, command: CommandObject, bot: Bot, state: FSMContext) -> None:
    display_name = user.full_name or "do'stim"

    # Set Telegram Menu Button (Bottom-left native WebApp button)
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="📱 BilimGo App",
                web_app=WebAppInfo(url=settings.webapp.base_url),
            ),
        )
    except Exception:
        pass

    conn = database.conn
    course_repo = CourseRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    user_repo = UserRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    all_courses = await course_repo.list_published()

    payload = command.args

    # 1. Agar foydalanuvchi hali telefon raqamini yubormagan bo'lsa, payloadni saqlab raqam so'raymiz
    if not user.phone:
        if payload:
            await state.update_data(referral_payload=payload)
        
        await message.answer(
            f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
            f"🎓 <b>BilimGo</b> adaptiv ta'lim platformasiga xush kelibsiz.\n\n"
            f"Platformadagi barcha darslar, video player, guruh chatlari va AI Ustozdan to'liq foydalanish uchun, "
            f"iltimos, pastdagi <b>«📱 Telefon raqamni yuborish»</b> tugmasini bosing 👇",
            reply_markup=PHONE_REQUEST_KEYBOARD,
        )
        return

    # 2. If phone is verified, resolve payload
    course_id, node_id, is_mentor_invite, mentor_target_id = _parse_payload(payload)
    mentor_info = ""

    # 3. Handle Special Mentor Onboarding Link
    if (is_mentor_invite or user.role == "mentor") and user.role != "admin":
        await user_repo.update_role(user.id, "mentor")
        user = await user_repo.get_by_id(user.id) or user

        # Check if license node exists for this mentor
        cursor = await conn.execute(
            "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1",
            (user.id,),
        )
        existing_node = await cursor.fetchone()
        assigned_node_id = existing_node["id"] if existing_node else None

        if not assigned_node_id:
            target_cid = course_id or 1
            cur = await conn.execute(
                """
                INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status)
                VALUES (1, ?, ?, 20.0, 'limit', 'active')
                """,
                (user.id, target_cid),
            )
            await conn.commit()
            assigned_node_id = cur.lastrowid

        # Create/Get Cabinet for new mentor
        cabinet_name = "Mentor Kabineti"
        if assigned_node_id:
            cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
            cab = await cabinet_service.get_or_create_for_node(assigned_node_id)
            cabinet_name = cab.display_name

        # 🔔 Super Mentor / Adminga bildirishnoma yuborish
        await _notify_super_mentors_about_mentor_activation(
            bot=bot,
            mentor=user,
            node_id=assigned_node_id or 1,
            cabinet_name=cabinet_name,
            from_tg_user=message.from_user,
        )

        mentor_welcome_kb = get_mentor_inline_webapp()
        await message.answer(
            f"👨‍🏫 <b>Xush kelibsiz, hurmatli Mentorimiz {display_name}!</b> 🎉\n\n"
            f"Siz muvaffaqiyatli <b>Mentor</b> sifatida faollashtirildingiz.\n\n"
            f"🔓 <b>Imtiyozlaringiz:</b>\n"
            f"• Platformadagi barcha <b>{len(all_courses)} ta kurs</b> siz uchun 100% ochildi!\n"
            f"• Shaxsiy kabinetingiz va guruh chatingiz faol.\n"
            f"• Har bir kursni shogirdlaringizga sotish uchun shaxsiy havolalaringiz tayyor.\n\n"
            f"O'z shaxsiy kabinetingizga kirish uchun pastdagi tugmani bosing:",
            reply_markup=mentor_welcome_kb,
        )
        await message.answer(
            "Boshqaruv menyusi faollashtirildi 👇\n"
            "O'z sotuv havolalaringizni olish uchun <b>«🔗 Kurslarim sotuv havolalari»</b> tugmasini bosing.",
            reply_markup=MENTOR_MENU,
        )
        return

    # 4. Handle Student to Mentor Cabinet binding & Course Access
    mentor_info, target_course = await _handle_student_mentor_binding(bot, user, payload, from_tg_user=message.from_user)

    # Select role keyboard
    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
        inline_kb = get_admin_inline_webapp()
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
        inline_kb = get_mentor_inline_webapp()
    else:
        keyboard = STUDENT_MENU
        inline_kb = get_student_inline_webapp()

    # If course is specified in payload, grant access & show direct button
    if target_course:
        direct_course_kb = get_direct_course_keyboard(target_course.id)

        await message.answer(
            f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
            f"🎉 <b>Tabriklaymiz!</b> Siz <b>«{target_course.title}»</b> kursiga muvaffaqiyatli qabul qilindingiz.\n\n"
            f"🔓 Ushbu kursning barcha darslari, audio/video materiallari va AI tyutori siz uchun <b>to'liq ochildi!</b>\n"
            f"{mentor_info}\n"
            f"Darslarni hoziroq boshlash uchun quyidagi tugmani bosing 👇",
            reply_markup=direct_course_kb,
        )
        await message.answer(
            "Quyidagi menyu orqali tezkor boshqarishingiz mumkin 👇",
            reply_markup=keyboard,
        )
        return

    # Standard welcome message
    await message.answer(
        f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
        f"🎓 <b>BilimGo</b> adaptiv ta'lim platformasiga xush kelibsiz.\n\n"
        f"👤 <b>Tizimdagi rolingiz:</b> {_ROLE_LABELS.get(user.role, 'Talaba')}\n"
        f"📱 <b>Telefon:</b> <code>{user.phone}</code>"
        f"{mentor_info}\n\n"
        f"Barcha darslar, video player, AI yordamchi va guruh chatlariga kirish uchun quyidagi <b>«Mini App»</b> tugmasini bosing:",
        reply_markup=inline_kb,
    )

    await message.answer(
        "Boshqaruv menyusi 👇",
        reply_markup=keyboard,
    )


@router.message(F.contact)
async def handle_contact(message: Message, user: User, bot: Bot, state: FSMContext) -> None:
    contact = message.contact
    if not contact:
        return

    phone_number = contact.phone_number.strip()
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    conn = database.conn
    user_repo = UserRepository(conn)

    full_name = None
    if contact.first_name:
        parts = [contact.first_name]
        if contact.last_name:
            parts.append(contact.last_name)
        full_name = " ".join(parts)

    await user_repo.update_profile(user_id=user.id, full_name=full_name, phone=phone_number)
    user = await user_repo.get_by_id(user.id) or user

    # Retrieve saved referral payload from state if any
    data = await state.get_data()
    referral_payload = data.get("referral_payload")
    await state.clear()

    mentor_info, target_course = await _handle_student_mentor_binding(bot, user, referral_payload, from_tg_user=message.from_user)

    # If mentor sent contact, notify super mentors
    if user.role == "mentor":
        cursor = await conn.execute(
            "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1",
            (user.id,),
        )
        node_row = await cursor.fetchone()
        node_id = node_row["id"] if node_row else 1
        cab_repo = CabinetRepository(conn)
        ch_repo = ChatRepository(conn)
        ln_repo = LicenseNodeRepository(conn)
        cabinet_service = CabinetService(cab_repo, ch_repo, ln_repo, user_repo)
        cab = await cabinet_service.get_or_create_for_node(node_id)

        await _notify_super_mentors_about_mentor_activation(
            bot=bot,
            mentor=user,
            node_id=node_id,
            cabinet_name=cab.display_name,
            from_tg_user=message.from_user,
        )

    # Select role menu
    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
    else:
        keyboard = STUDENT_MENU

    if target_course:
        kb = get_direct_course_keyboard(target_course.id)
        await message.answer(
            f"✅ <b>Telefon raqamingiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Raqam: <code>{phone_number}</code>\n"
            f"🎉 <b>Tabriklaymiz!</b> Siz <b>«{target_course.title}»</b> kursiga muvaffaqiyatli qabul qilindingiz.\n\n"
            f"🔓 Ushbu kursning barcha darslari, audio/video materiallari va AI tyutori siz uchun <b>to'liq ochildi!</b>\n"
            f"{mentor_info}\n"
            f"Darslarni hoziroq boshlash uchun quyidagi tugmani bosing 👇",
            reply_markup=kb,
        )
    else:
        kb = get_profile_webapp_keyboard()
        await message.answer(
            f"✅ <b>Telefon raqamingiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Raqam: <code>{phone_number}</code>\n"
            f"🔗 Ushbu raqam <b>BilimGo WebApp</b> profilingizga to'liq biriktirildi!\n"
            f"{mentor_info}\n"
            f"Endi platformaning barcha imkoniyatlaridan to'liq foydalanishingiz mumkin 👇",
            reply_markup=kb,
        )

    await message.answer(
        "Boshqaruv menyusi ochildi 👇",
        reply_markup=keyboard,
    )


# ----------------- ADMIN TOOLS: MENTOR TAYINLASH VA HAVOLA BERISH -----------------

# ----------------- ADMIN TOOLS: MENTOR TAYINLASH VA HAVOLA BERISH -----------------

@router.message(Command("newmentor"))
@router.message(Command("addmentor"))
@router.message(F.text.in_(["➕ Yangi Mentor qo'shish", "➕ Yangi Mentor Havolasi", "➕ Yangi Mentor", "➕ Mentor tayinlash", "Yangi Mentor qo'shish"]))
async def start_add_mentor_process(message: Message, user: User, state: FSMContext) -> None:
    if user.role != "admin" and message.from_user.id not in settings.bot.admin_ids:
        await message.answer("Bu amal faqat Super Admin / Bosh Mentor uchun.")
        return

    args = message.text.split()
    if len(args) >= 2 and args[1].isdigit():
        # Direct command with ID: /addmentor 123456789
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
        await message.answer("Iltimos, faqat raqamlardan iborat Telegram ID kiriting (Masalan: <code>123456789</code>):")
        return

    target_tid = int(text)
    await state.clear()
    await process_mentor_assignment(message, target_tid, bot=bot)


async def process_mentor_assignment(message: Message, target_tid: int, bot: Bot) -> None:
    conn = database.conn
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    # 1. Get or create user as mentor
    target_user = await user_repo.get_or_create(telegram_id=target_tid)
    await user_repo.update_role(target_user.id, "mentor")

    # 2. Create/find license node
    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1",
        (target_user.id,),
    )
    node_row = await cursor.fetchone()
    if not node_row:
        cur = await conn.execute(
            """
            INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status)
            VALUES (1, ?, 1, 20.0, 'limit', 'active')
            """,
            (target_user.id,),
        )
        await conn.commit()
        node_id = cur.lastrowid
    else:
        node_id = node_row["id"]

    # 3. Create Cabinet for mentor
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

    # Mentorga to'g'ridan-to'g'ri bildirishnoma
    try:
        await bot.send_message(
            chat_id=target_tid,
            text=(
                f"🎉 <b>Assalomu alaykum, {target_user.full_name or 'Hurmatli Mentor'}!</b> 🎓\n\n"
                f"Siz «BilimGo» platformasida rasmiy <b>Mentor</b> sifatida tayinlandingiz!\n\n"
                f"• Barcha kurslar siz uchun to'liq ochildi ✅\n"
                f"• Shaxsiy o'quv kabinetingiz yaratildi 👥\n"
                f"• 15 kunlik bepul limit davri ajratildi (ushbu davrda sotilgan kurslardan 100% daromad to'liq o'zingizda qoladi) 🎁\n\n"
                f"Quyidagi tugma orqali kabinetingizni ochishingiz va darslarni boshlashingiz mumkin 👇"
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
            u.id as user_id,
            u.full_name,
            u.telegram_id,
            u.phone,
            ln.id as node_id,
            ln.stage,
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


@router.message(Command("profile"))
@router.message(F.text.in_(["👤 Profil va Sozlamalar", "👤 Profil va sozlamalar", "👤 Profil", "Profil va sozlamalar", "Profil"]))
async def handle_profile_menu(message: Message, user: User) -> None:
    conn = database.conn
    user_repo = UserRepository(conn)
    current_user = await user_repo.get_by_id(user.id) or user

    phone_display = current_user.phone or "Kiritilmagan"
    role_name = _ROLE_LABELS.get(current_user.role, "Talaba")
    name_display = current_user.full_name or "Noma'lum"

    inline_kb = get_profile_webapp_keyboard()

    await message.answer(
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"• <b>Ism:</b> {name_display}\n"
        f"• <b>Telegram ID:</b> <code>{current_user.telegram_id}</code>\n"
        f"• <b>Telefon:</b> <code>{phone_display}</code>\n"
        f"• <b>Rolingiz:</b> {role_name}",
        reply_markup=inline_kb,
    )


@router.message(Command("links"))
@router.message(Command("courses"))
@router.message(F.text.in_(["🔗 Kurs Havolalari (Referral)", "🔗 Kurs havolalari", "🔗 Kurslarim sotuv havolalari", "🔗 Taklif havolam", "🔗 Taklif havolalari"]))
async def handle_course_links(message: Message, user: User, bot: Bot) -> None:
    conn = database.conn
    is_mentor_or_admin = (
        user.role in ("mentor", "admin", "super_mentor")
        or message.from_user.id in settings.bot.admin_ids
    )

    # Check if user owns a license node
    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? ORDER BY id ASC LIMIT 1",
        (user.id,),
    )
    node_row = await cursor.fetchone()

    # Oddiy talabalar uchun sotuv havolalari ko'rinmasin
    if not is_mentor_or_admin and not node_row:
        inline_kb = get_catalog_webapp_keyboard()
        await message.answer(
            "📚 <b>Kurslar katalogi</b> orqali o'zingizga qiziq kurslarni tanlab, darslarni boshlashingiz mumkin 👇",
            reply_markup=inline_kb,
        )
        return

    node_id = node_row["id"] if node_row else 1
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "BilimGoUz_Bot"

    course_repo = CourseRepository(conn)
    courses = await course_repo.list_published()

    text_lines = [
        "🔗 <b>Sizning Shaxsiy Kurs Sotuv Havolalaringiz (Sizga birikadi):</b>\n",
        "O'quvchi ushbu havolalar orqali kirganida, <b>aynan sizning kabinetingizga shogird bo'lib birikadi</b> va unga faqat tanlangan kurs ochiladi:\n",
    ]

    for c in courses:
        ref_link = f"https://t.me/{bot_username}?start=node_{node_id}_course_{c.id}"
        text_lines.append(f"📌 <b>{c.title}</b>:")
        text_lines.append(f"👉 <code>{ref_link}</code>\n")

    general_link = f"https://t.me/{bot_username}?start=node_{node_id}"
    text_lines.append(f"🏢 <b>Umumiy Kabinetingizga taklif havolasi:</b>\n👉 <code>{general_link}</code>\n")
    text_lines.append("💡 <i>Nusxalash uchun istalgan havola ustiga bir marta bosing.</i>")

    await message.answer("\n".join(text_lines))


@router.message(F.text == "🔙 Bosh menyu")
async def handle_back_to_menu(message: Message, user: User) -> None:
    if not user.phone:
        await message.answer(
            "Iltimos, avval telefon raqamingizni yuboring 👇",
            reply_markup=PHONE_REQUEST_KEYBOARD,
        )
        return

    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
    else:
        keyboard = STUDENT_MENU

    await message.answer("Bosh menyudasiz 👇", reply_markup=keyboard)
