"""
Mentor arizalari va to'lov cheklarini tasdiqlash / rad etish handlerlari.
"""
from __future__ import annotations

import logging
import os

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.config import settings
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.mentor_application_repo import MentorApplicationRepository
from db.repositories.user_repo import User, UserRepository
from services.cabinet_service import CabinetService

logger = logging.getLogger(__name__)
router = Router(name="mentor_approval")


async def _is_admin(callback: CallbackQuery, user: User, bot: Bot) -> bool:
    if (
        user.role == "admin"
        or callback.from_user.id in (settings.bot.admin_ids or ())
        or str(callback.from_user.id) in [str(a) for a in (settings.bot.admin_ids or ())]
    ):
        return True
    try:
        if callback.message and callback.message.chat:
            member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
            if member.status in ("creator", "administrator"):
                return True
    except Exception:
        pass
    return False


# 1. Mentorlik arizasini tasdiqlash (Topic 2)
@router.callback_query(F.data.startswith("mentor_app:approve:"))
async def handle_approve_mentor_application(callback: CallbackQuery, user: User, bot: Bot) -> None:
    if not await _is_admin(callback, user, bot):
        await callback.answer("Bu amal faqat administratorlar uchun!", show_alert=True)
        return

    app_id = int(callback.data.split(":")[-1])
    conn = database.conn
    app_repo = MentorApplicationRepository(conn)
    user_repo = UserRepository(conn)

    app = await app_repo.get_by_id(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    # Statusni payment_pending ga o'tkazish
    await app_repo.update_status(app_id, "payment_pending")

    admin_tag = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    original_text = callback.message.html_text or callback.message.text or ""

    # Guruhdagi xabarni yangilash (tugmalarni olib tashlash)
    try:
        await callback.message.edit_text(
            f"{original_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>ARIZA TASDIQLANDI!</b>\n"
            f"👤 <b>Tasdiqladi:</b> {admin_tag} (<code>{callback.from_user.id}</code>)\n"
            f"⏳ <i>Nomzodga to'lov ma'lumotlari yuborildi.</i>",
            parse_mode="HTML",
            reply_markup=None,
        )
    except Exception as ex:
        logger.warning("Guruh xabarini tahrirlashda xatolik: %s", ex)

    # Nomzodga bot orqali to'lov ma'lumotlarini yuborish
    target_user = await user_repo.get_by_id(app.user_id)
    if target_user and target_user.telegram_id:
        price = app.payment_amount or int(os.getenv("MENTOR_PRICE", "949000"))
        card_number = os.getenv("MENTOR_CARD_NUMBER", "8600 0000 0000 0000")
        card_holder = os.getenv("MENTOR_CARD_HOLDER", "Admin")

        user_text = (
            f"🎉 <b>Assalomu alaykum, {app.full_name}!</b>\n\n"
            f"Sizning <b>Super Mentorlik</b> arizangiz ma'qullandi! 🎓\n\n"
            f"Platformadagi barcha kurslar, o'quv kabinetingiz va mentorlik vositalarini to'liq faollashtirish uchun belgilangan xizmat to'lovini amalga oshiring:\n\n"
            f"💰 <b>To'lov summasi:</b> {price:,} so'm\n"
            f"💳 <b>Karta:</b> <code>{card_number}</code> ({card_holder})\n\n"
            f"📸 <i>To'lovni amalga oshirgach, to'lov cheki (skrinshot)ni to'g'ridan-to'g'ri shu botga rasm sifatida yuboring yoki ilova orqali yuklang 👇</i>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Profil / Chek yuklash",
                        web_app=WebAppInfo(url=f"{settings.webapp.base_url}?view=profile"),
                    )
                ]
            ]
        )
        try:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=user_text,
                reply_markup=kb,
                parse_mode="HTML",
            )
            logger.info("Nomzodga (%s) to'lov xabari muvaffaqiyatli yuborildi.", target_user.telegram_id)
        except Exception as ex:
            logger.warning("Nomzodga xabar yuborishda xatolik: %s", ex)

    await callback.answer("✅ Ariza tasdiqlandi va nomzodga to'lov ma'lumotlari yuborildi!")


# 2. Mentorlik arizasini rad etish (Topic 2)
@router.callback_query(F.data.startswith("mentor_app:reject:"))
async def handle_reject_mentor_application(callback: CallbackQuery, user: User, bot: Bot) -> None:
    if not await _is_admin(callback, user, bot):
        await callback.answer("Bu amal faqat administratorlar uchun!", show_alert=True)
        return

    app_id = int(callback.data.split(":")[-1])
    conn = database.conn
    app_repo = MentorApplicationRepository(conn)
    user_repo = UserRepository(conn)

    app = await app_repo.get_by_id(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    await app_repo.update_status(app_id, "rejected")

    admin_tag = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    original_text = callback.message.html_text or callback.message.text or ""

    try:
        await callback.message.edit_text(
            f"{original_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"❌ <b>ARIZA RAD ETILDI!</b>\n"
            f"👤 <b>Admin:</b> {admin_tag} (<code>{callback.from_user.id}</code>)",
            parse_mode="HTML",
            reply_markup=None,
        )
    except Exception as ex:
        logger.warning("Guruh xabarini tahrirlashda xatolik: %s", ex)

    target_user = await user_repo.get_by_id(app.user_id)
    if target_user and target_user.telegram_id:
        try:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=(
                    f"Hurmatli <b>{app.full_name}</b>,\n\n"
                    "Sizning <b>Super Mentorlik</b> arizangiz ma'muriyat tomonidan ko'rib chiqildi va afsuski rad etildi."
                ),
                parse_mode="HTML",
            )
        except Exception as ex:
            logger.warning("Nomzodga rad etish xabarini yuborishda xatolik: %s", ex)

    await callback.answer("❌ Ariza rad etildi.")


# 3. To'lov chekini tasdiqlash (Topic 4)
@router.callback_query(F.data.startswith("mentor_receipt:approve:"))
async def handle_approve_mentor_receipt(callback: CallbackQuery, user: User, bot: Bot) -> None:
    if not await _is_admin(callback, user, bot):
        await callback.answer("Bu amal faqat administratorlar uchun!", show_alert=True)
        return

    app_id = int(callback.data.split(":")[-1])
    conn = database.conn
    app_repo = MentorApplicationRepository(conn)
    user_repo = UserRepository(conn)
    course_repo = CourseRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)

    app = await app_repo.get_by_id(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    # 1. Statusni approved ga o'tkazish
    await app_repo.update_status(app_id, "approved")

    # 2. Foydalanuvchi rolini mentor ga o'tkazish
    await user_repo.update_role(app.user_id, "mentor")

    # 3. Litsenziya tugunini yaratish / faollashtirish
    cursor = await conn.execute(
        "SELECT id FROM license_nodes WHERE owner_user_id = ? LIMIT 1",
        (app.user_id,),
    )
    node_row = await cursor.fetchone()
    if not node_row:
        cur = await conn.execute(
            "INSERT INTO license_nodes (parent_id, owner_user_id, course_id, royalty_percent, stage, status) "
            "VALUES (1, ?, 1, 20.0, 'limit', 'active')",
            (app.user_id,),
        )
        await conn.commit()
        node_id = cur.lastrowid
    else:
        node_id = node_row["id"]
        await conn.execute(
            "UPDATE license_nodes SET status = 'active' WHERE id = ?",
            (node_id,),
        )
        await conn.commit()

    # 4. Kabinet yaratish
    cabinet_service = CabinetService(cabinet_repo, chat_repo, license_node_repo, user_repo)
    cabinet = await cabinet_service.get_or_create_for_node(node_id)

    # 5. BARCHA KURSLARGA CHEKSIZ RUXSAT BERISH (BEPUL)
    all_courses = await course_repo.list_published()
    for course in all_courses:
        try:
            await access_grant_repo.grant_course_access(
                user_id=app.user_id,
                course_id=course.id,
                granted_via_sale_id=0,
            )
        except Exception as c_ex:
            logger.warning("Kurs %s ga ruxsat berishda xatolik: %s", course.id, c_ex)

    admin_tag = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    original_text = callback.message.html_text or callback.message.text or ""

    # Guruhdagi xabarni yangilash
    try:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=(
                    f"{callback.message.caption}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ <b>TO'LOV CHEKI TASDIQLANDI!</b>\n"
                    f"👤 <b>Tasdiqladi:</b> {admin_tag} (<code>{callback.from_user.id}</code>)\n"
                    f"🎓 <b>Mentorlik faollashtirildi va barcha {len(all_courses)} ta kurs cheksiz ochildi!</b>"
                ),
                parse_mode="HTML",
                reply_markup=None,
            )
        else:
            await callback.message.edit_text(
                f"{original_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>TO'LOV CHEKI TASDIQLANDI!</b>\n"
                f"👤 <b>Tasdiqladi:</b> {admin_tag} (<code>{callback.from_user.id}</code>)\n"
                f"🎓 <b>Mentorlik faollashtirildi va barcha {len(all_courses)} ta kurs cheksiz ochildi!</b>",
                parse_mode="HTML",
                reply_markup=None,
            )
    except Exception as ex:
        logger.warning("Guruhdagi chek xabarini tahrirlashda xatolik: %s", ex)

    # Yangi Mentorga quvonchli xabar yuborish
    target_user = await user_repo.get_by_id(app.user_id)
    if target_user and target_user.telegram_id:
        mentor_text = (
            f"🎉 <b>TABRIKLAYMIZ, {app.full_name}!</b> 👑\n\n"
            f"To'lovingiz muvaffaqiyatli tasdiqlandi!\n\n"
            f"✅ <b>Siz endi rasmiy Mentorsiz!</b>\n"
            f"✅ <b>Platformadagi barcha {len(all_courses)} ta kurs siz uchun BEPUL va CHEKSIZ ochildi!</b>\n"
            f"✅ <b>Shaxsiy mentorlik kabinetingiz ({cabinet.display_name}) faollashtirildi.</b>\n\n"
            f"Ilovaga kirib barcha darslarni ko'rishingiz va o'quvchilaringiz bilan ishlashni boshlashingiz mumkin 👇"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Mini Appni ochish",
                        web_app=WebAppInfo(url=settings.webapp.base_url),
                    )
                ]
            ]
        )
        try:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=mentor_text,
                reply_markup=kb,
                parse_mode="HTML",
            )
            logger.info("Yangi mentor %s ga tabrik xabari yetkazildi.", target_user.telegram_id)
        except Exception as ex:
            logger.warning("Mentorga xabar yuborishda xatolik: %s", ex)

    await callback.answer("✅ To'lov cheki tasdiqlandi va barcha darslar mentorga cheksiz ochildi!")


# 4. To'lov chekini rad etish (Topic 4)
@router.callback_query(F.data.startswith("mentor_receipt:reject:"))
async def handle_reject_mentor_receipt(callback: CallbackQuery, user: User, bot: Bot) -> None:
    if not await _is_admin(callback, user, bot):
        await callback.answer("Bu amal faqat administratorlar uchun!", show_alert=True)
        return

    app_id = int(callback.data.split(":")[-1])
    conn = database.conn
    app_repo = MentorApplicationRepository(conn)
    user_repo = UserRepository(conn)

    app = await app_repo.get_by_id(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    await app_repo.update_status(app_id, "receipt_rejected")

    admin_tag = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    original_text = callback.message.html_text or callback.message.text or ""

    try:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=(
                    f"{callback.message.caption}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"❌ <b>TO'LOV CHEKI RAD ETILDI!</b>\n"
                    f"👤 <b>Admin:</b> {admin_tag} (<code>{callback.from_user.id}</code>)"
                ),
                parse_mode="HTML",
                reply_markup=None,
            )
        else:
            await callback.message.edit_text(
                f"{original_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>TO'LOV CHEKI RAD ETILDI!</b>\n"
                f"👤 <b>Admin:</b> {admin_tag} (<code>{callback.from_user.id}</code>)",
                parse_mode="HTML",
                reply_markup=None,
            )
    except Exception as ex:
        logger.warning("Guruhdagi chek xabarini tahrirlashda xatolik: %s", ex)

    target_user = await user_repo.get_by_id(app.user_id)
    if target_user and target_user.telegram_id:
        try:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=(
                    f"Hurmatli <b>{app.full_name}</b>,\n\n"
                    "⚠️ Siz yuborgan to'lov cheki ma'muriyat tomonidan tasdiqlanmadi.\n"
                    "Iltimos, to'lovni tasdiqlovchi to'g'ri chekni (skrinshotni) botga qaytadan yuboring."
                ),
                parse_mode="HTML",
            )
        except Exception as ex:
            logger.warning("Nomzodga rad etish xabarini yuborishda xatolik: %s", ex)

    await callback.answer("❌ To'lov cheki rad etildi.")


# 5. Nomzod botga to'g'ridan-to'g'ri chek (rasm) yuborganda uni ushlash
@router.message(F.photo)
async def handle_user_sent_receipt_photo(message: Message, user: User, bot: Bot) -> None:
    conn = database.conn
    app_repo = MentorApplicationRepository(conn)
    app = await app_repo.get_latest_by_user_id(user.id)

    # Agar foydalanuvchida to'lov kutilayotgan ariza bo'lsa
    if not app or app.status not in ("payment_pending", "receipt_rejected"):
        return

    photo_id = message.photo[-1].file_id

    # Bazada yangilash
    await conn.execute(
        "UPDATE mentor_applications SET receipt_photo_id = ?, status = 'receipt_submitted' WHERE id = ?",
        (photo_id, app.id),
    )
    await conn.commit()

    # Foydalanuvchiga tasdiq xabari
    await message.answer(
        "🧾 <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "Arizangiz ma'muriyatga yuborildi. To'lov tasdiqlanishi bilan hisobingiz va barcha darslar avtomatik ochiladi ⏳",
        parse_mode="HTML",
    )

    # Guruhdagi Topic 4 ga rasm va inline tugmalar bilan yuborish
    group_id = int(os.getenv("SUPER_MENTOR_GROUP_ID", "-1004369887420"))
    topic_id = int(os.getenv("PAYMENT_RECEIPTS_TOPIC_ID", "4"))
    receipt_caption = (
        f"🧾 <b>YANGI TO'LOV CHEKI YUBORILDI!</b>\n\n"
        f"🆔 <b>Ariza raqami:</b> #{app.id}\n"
        f"👤 <b>Nomzod:</b> <b>{app.full_name}</b>\n"
        f"📱 <b>Telefon:</b> <code>{app.phone}</code>\n"
        f"💬 <b>Telegram:</b> {app.telegram_username or f'ID: {user.telegram_id}'}\n"
        f"💰 <b>To'lov summasi:</b> {app.payment_amount:,} so'm\n\n"
        f"⚡️ <i>Iltimos, to'lovni tekshirib arizani tasdiqlang.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Chekni tasdiqlash", callback_data=f"mentor_receipt:approve:{app.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"mentor_receipt:reject:{app.id}"),
            ]
        ]
    )

    try:
        await bot.send_photo(
            chat_id=group_id,
            photo=photo_id,
            caption=receipt_caption,
            message_thread_id=topic_id,
            reply_markup=kb,
            parse_mode="HTML",
        )
        logger.info("Chek fotosi Topic %s ga inline tugmalar bilan yuborildi.", topic_id)
    except Exception as ex:
        logger.warning("Guruhga chek rasmini yuborishda xatolik: %s", ex)
