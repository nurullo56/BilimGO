"""
/start va telefon kontakt handlerlari.
"""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import MenuButtonWebApp, Message, WebAppInfo

from bot.handlers.common._utils import (
    _ROLE_LABELS,
    _handle_student_mentor_binding,
    _notify_super_mentors_about_mentor_activation,
    _parse_payload,
)
from bot.keyboards.admin_kb import ADMIN_MENU, get_admin_inline_webapp
from bot.keyboards.common_kb import (
    get_catalog_webapp_keyboard,
    get_direct_course_keyboard,
    get_profile_webapp_keyboard,
)
from bot.keyboards.mentor_kb import MENTOR_MENU, get_mentor_inline_webapp
from bot.keyboards.student_kb import PHONE_REQUEST_KEYBOARD, STUDENT_MENU, get_student_inline_webapp
from core.config import settings
from db.database import database
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService

logger = logging.getLogger(__name__)
router = Router(name="registration")


@router.message(CommandStart())
async def handle_start(message: Message, user: User, command: CommandObject, bot: Bot, state: FSMContext) -> None:
    display_name = user.full_name or "do'stim"

    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="📱 BilimGo App",
                web_app=WebAppInfo(url=settings.webapp.base_url),
            ),
        )
    except Exception as exc:
        import logging
        logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    conn = database.conn
    course_repo = CourseRepository(conn)
    user_repo = UserRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)

    all_courses = await course_repo.list_published()
    payload = command.args

    # 1. Telefon raqami yo'q bo'lsa
    if not user.phone:
        if payload:
            await state.update_data(referral_payload=payload)
        await message.answer(
            f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
            "🎓 <b>BilimGo</b> adaptiv ta'lim platformasiga xush kelibsiz.\n\n"
            "Platformadagi barcha darslar, video player, guruh chatlari va AI Ustozdan to'liq foydalanish uchun, "
            "iltimos, pastdagi <b>«📱 Telefon raqamni yuborish»</b> tugmasini bosing 👇",
            reply_markup=PHONE_REQUEST_KEYBOARD,
        )
        return

    # 2. Payload ni tahlil qilish
    course_id, node_id, is_mentor_invite, mentor_target_id = _parse_payload(payload)
    mentor_info = ""

    # 3. Mentor onboarding
    if (is_mentor_invite or user.role == "mentor") and user.role != "admin":
        await user_repo.update_role(user.id, "mentor")
        user = await user_repo.get_by_id(user.id) or user

        cursor = await conn.execute(
            "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1", (user.id,)
        )
        existing_node = await cursor.fetchone()
        assigned_node_id = existing_node["id"] if existing_node else None

        if not assigned_node_id:
            target_cid = course_id or 1
            cur = await conn.execute(
                "INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status) "
                "VALUES (1, ?, ?, 20.0, 'limit', 'active')",
                (user.id, target_cid),
            )
            await conn.commit()
            assigned_node_id = cur.lastrowid

        cabinet_name = "Mentor Kabineti"
        if assigned_node_id:
            cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
            cab = await cabinet_service.get_or_create_for_node(assigned_node_id)
            cabinet_name = cab.display_name

        await _notify_super_mentors_about_mentor_activation(
            bot=bot, mentor=user,
            node_id=assigned_node_id or 1, cabinet_name=cabinet_name,
            from_tg_user=message.from_user,
        )

        await message.answer(
            f"👨‍🏫 <b>Xush kelibsiz, hurmatli Mentorimiz {display_name}!</b> 🎉\n\n"
            "Siz muvaffaqiyatli <b>Mentor</b> sifatida faollashtirildingiz.\n\n"
            "🔓 <b>Imtiyozlaringiz:</b>\n"
            f"• Platformadagi barcha <b>{len(all_courses)} ta kurs</b> siz uchun 100% ochildi!\n"
            "• Shaxsiy kabinetingiz va guruh chatingiz faol.\n"
            "• Har bir kursni shogirdlaringizga sotish uchun shaxsiy havolalaringiz tayyor.\n\n"
            "O'z shaxsiy kabinetingizga kirish uchun pastdagi tugmani bosing:",
            reply_markup=get_mentor_inline_webapp(),
        )
        await message.answer(
            "Boshqaruv menyusi faollashtirildi 👇\n"
            "O'z sotuv havolalaringizni olish uchun <b>«🔗 Kurslarim sotuv havolalari»</b> tugmasini bosing.",
            reply_markup=MENTOR_MENU,
        )
        return

    # 4. Talabani mentor kabinetiga biriktirish
    mentor_info, target_course = await _handle_student_mentor_binding(
        bot, user, payload, from_tg_user=message.from_user
    )

    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
        inline_kb = get_admin_inline_webapp()
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
        inline_kb = get_mentor_inline_webapp()
    else:
        keyboard = STUDENT_MENU
        inline_kb = get_student_inline_webapp()

    if target_course:
        await message.answer(
            f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
            f"🎉 <b>Tabriklaymiz!</b> Siz <b>«{target_course.title}»</b> kursiga muvaffaqiyatli qabul qilindingiz.\n\n"
            "🔓 Ushbu kursning barcha darslari, audio/video materiallari va AI tyutori siz uchun <b>to'liq ochildi!</b>\n"
            f"{mentor_info}\n"
            "Darslarni hoziroq boshlash uchun quyidagi tugmani bosing 👇",
            reply_markup=get_direct_course_keyboard(target_course.id),
        )
        await message.answer("Quyidagi menyu orqali tezkor boshqarishingiz mumkin 👇", reply_markup=keyboard)
        return

    await message.answer(
        f"✨ <b><u>𝑩𝒊𝒍𝒊𝒎𝑮𝒐</u></b> | Adaptiv Ta'lim Platformasi ✨\n\n"
        f"Assalomu alaykum, <b>{display_name}</b>!\n\n"
        f"👤 <b>Tizimdagi rolingiz:</b> {_ROLE_LABELS.get(user.role, 'Talaba')}\n"
        f"📱 <b>Telefon:</b> <code>{user.phone}</code>"
        f"{mentor_info}\n\n"
        "🚀 Barcha darslar, video player, AI yordamchi va guruh chatlariga kirish uchun quyidagi <b>«📱 BilimGo App»</b> tugmasini bosing:",
        reply_markup=inline_kb,
    )
    await message.answer("Boshqaruv menyusi 👇", reply_markup=keyboard)


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

    data = await state.get_data()
    referral_payload = data.get("referral_payload")
    await state.clear()

    mentor_info, target_course = await _handle_student_mentor_binding(
        bot, user, referral_payload, from_tg_user=message.from_user
    )

    if user.role == "mentor":
        cursor = await conn.execute(
            "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1", (user.id,)
        )
        node_row = await cursor.fetchone()
        node_id = node_row["id"] if node_row else 1
        cab_repo = CabinetRepository(conn)
        ch_repo = ChatRepository(conn)
        ln_repo = LicenseNodeRepository(conn)
        cabinet_service = CabinetService(cab_repo, ch_repo, ln_repo, user_repo)
        cab = await cabinet_service.get_or_create_for_node(node_id)
        await _notify_super_mentors_about_mentor_activation(
            bot=bot, mentor=user, node_id=node_id,
            cabinet_name=cab.display_name, from_tg_user=message.from_user,
        )

    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
    else:
        keyboard = STUDENT_MENU

    if target_course:
        await message.answer(
            f"✅ <b>Telefon raqamingiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Raqam: <code>{phone_number}</code>\n"
            f"🎉 <b>Tabriklaymiz!</b> Siz <b>«{target_course.title}»</b> kursiga muvaffaqiyatli qabul qilindingiz.\n\n"
            "🔓 Ushbu kursning barcha darslari, audio/video materiallari va AI tyutori siz uchun <b>to'liq ochildi!</b>\n"
            f"{mentor_info}\n"
            "Darslarni hoziroq boshlash uchun quyidagi tugmani bosing 👇",
            reply_markup=get_direct_course_keyboard(target_course.id),
        )
    else:
        await message.answer(
            f"✅ <b>Telefon raqamingiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Raqam: <code>{phone_number}</code>\n"
            "🔗 Ushbu raqam <b>BilimGo WebApp</b> profilingizga to'liq biriktirildi!\n"
            f"{mentor_info}\n"
            "Endi platformaning barcha imkoniyatlaridan to'liq foydalanishingiz mumkin 👇",
            reply_markup=get_profile_webapp_keyboard(),
        )
    await message.answer("Boshqaruv menyusi ochildi 👇", reply_markup=keyboard)


@router.message(F.text == "🔙 Bosh menyu")
async def handle_back_to_menu(message: Message, user: User) -> None:
    if not user.phone:
        await message.answer("Iltimos, avval telefon raqamingizni yuboring 👇", reply_markup=PHONE_REQUEST_KEYBOARD)
        return

    if user.role == "admin" or message.from_user.id in settings.bot.admin_ids:
        keyboard = ADMIN_MENU
    elif user.role == "mentor":
        keyboard = MENTOR_MENU
    else:
        keyboard = STUDENT_MENU

    await message.answer("Bosh menyudasiz 👇", reply_markup=keyboard)
