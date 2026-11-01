"""
Mentor arizalari va to'lov cheklarini tasdiqlash / rad etish handlerlari.
"""
from __future__ import annotations

import logging
import os

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from core.config import settings
from db.repositories.user_repo import User
from services.admin_notifier import AdminNotifier
from services.mentor_service import MentorService

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
    mentor_service = MentorService()
    app, target_user = await mentor_service.approve_mentor_application(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

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
    mentor_service = MentorService()
    app, target_user = await mentor_service.reject_mentor_application(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

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
    mentor_service = MentorService()
    res = await mentor_service.approve_mentor_receipt(app_id)
    if not res:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    app = res["app"]
    target_user = res["target_user"]
    cabinet = res["cabinet"]
    all_courses = res["all_courses"]

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
    mentor_service = MentorService()
    app, target_user = await mentor_service.reject_mentor_receipt(app_id)
    if not app:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

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
    mentor_service = MentorService()
    photo_id = message.photo[-1].file_id
    app = await mentor_service.submit_receipt_photo(user.id, photo_id)

    # Agar foydalanuvchida to'lov kutilayotgan ariza bo'lmasa
    if not app:
        return

    # Foydalanuvchiga tasdiq xabari
    await message.answer(
        "🧾 <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "Arizangiz ma'muriyatga yuborildi. To'lov tasdiqlanishi bilan hisobingiz va barcha darslar avtomatik ochiladi ⏳",
        parse_mode="HTML",
    )

    # Guruhdagi Topic 4 ga rasm va inline tugmalar bilan yuborish
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

    notifier = AdminNotifier(bot)
    await notifier.send_payment_receipt(photo_id, receipt_caption, reply_markup=kb)
