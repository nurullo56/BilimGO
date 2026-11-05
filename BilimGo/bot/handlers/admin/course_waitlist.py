from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.admin import (
    ADMIN_MENU,
    get_admin_courses_waitlist_keyboard,
    get_admin_panel_keyboard,
)
from core.config import settings
from services.course_service import CourseService

logger = logging.getLogger(__name__)
router = Router(name="admin_course_waitlist")


async def _render_waitlist_panel(event: Message | CallbackQuery) -> None:
    service = CourseService()
    courses = await service.list_published()

    text = (
        "⏳ <b>Kurslar Kutish Ro'yxati (Waitlist) Boshqaruvi</b>\n\n"
        "Quyidagi ro'yxatdan kerakli kurs ustiga bosib, uning holatini o'zgartirishingiz mumkin:\n\n"
        "• 🟢 <b>Sotuvda:</b> Talabalar to'lov qilib darslarga to'g'ridan-to'g'ri kirishadi.\n"
        "• ⏳ <b>Waitlist:</b> Talabalarga to'lov o'rniga «Navbatga yozilish» tugmasi ko'rinadi.\n\n"
        "<i>Kerakli kurs tugmasini bosing:</i>"
    )
    keyboard = get_admin_courses_waitlist_keyboard(courses)

    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("waitlist", "course_waitlist"))
@router.message(F.text.in_(["⏳ Kurslar Waitlist (Navbat)", "⏳ Kurslar Waitlist", "Kurslar Waitlist"]))
async def handle_waitlist_menu_command(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("⚠️ Sizda ushbu amalni bajarish huquqi yo'q.")
        return

    await state.clear()
    await _render_waitlist_panel(message)


@router.callback_query(F.data == "admin_action:waitlist")
async def handle_waitlist_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("⚠️ Ruxsatingiz yo'q!", show_alert=True)
        return

    await state.clear()
    await _render_waitlist_panel(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_waitlist:toggle:"))
async def handle_waitlist_toggle(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("⚠️ Ruxsatingiz yo'q!", show_alert=True)
        return

    try:
        course_id = int(callback.data.split(":")[2])
        service = CourseService()
        result = await service.toggle_waitlist(course_id)

        status_text = "⏳ Waitlist rejimiga o'tkazildi" if result["is_waitlist"] else "🟢 Sotuv rejimiga qaytarildi"
        await callback.answer(f"✅ {result['title']}: {status_text}!", show_alert=False)

        # Matn va klaviaturani yangilash
        await _render_waitlist_panel(callback)
    except Exception as exc:
        logger.exception("Waitlist holatini almashtirishda xatolik: %s", exc)
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@router.callback_query(F.data == "admin_action:back_to_menu")
async def handle_back_to_admin_menu(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in settings.bot.admin_ids:
        await callback.answer("⚠️ Ruxsatingiz yo'q!", show_alert=True)
        return

    txt = (
        "👑 <b>Admin Boshqaruv Markazi</b>\n\n"
        f"👤 <b>Admin:</b> {callback.from_user.full_name}\n\n"
        "Pastdagi menyu orqali kerakli bo'limni tanlang 👇"
    )
    try:
        await callback.message.edit_text(txt, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(txt, reply_markup=ADMIN_MENU, parse_mode="HTML")
    await callback.answer()

@router.message(Command("set_notice"))
async def handle_set_course_notice(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("⚠️ Sizda ushbu amalni bajarish huquqi yo'q.")
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "ℹ️ <b>Foydalanish:</b> <code>/set_notice &lt;course_id&gt; &lt;e'lon matni&gt;</code>\n"
            "<i>Masalan:</i> <code>/set_notice 7 🔥 Dastlabki 30 ta o'quvchiga 50% chegirmada qabul ochildi!</code>\n"
            "<i>Tozalash uchun:</i> <code>/set_notice 7 none</code>",
            parse_mode="HTML",
        )
        return

    try:
        course_id = int(parts[1])
        notice_text = parts[2].strip()
        if notice_text.lower() in ("none", "clear", "o'chirish", "ochirish"):
            notice_text = ""

        service = CourseService()
        result = await service.set_course_notice(course_id, notice_text)
        await message.answer(
            f"✅ <b>{result['title']}</b> kursi uchun e'lon matni yangilandi:\n\n"
            f"📝 <i>{notice_text or '(Tozalandi)'}</i>",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("E'lon matnini o'rnatishda xatolik: %s", exc)
        await message.answer(f"❌ Xatolik yuz berdi: {exc}")


@router.message(Command("set_image"))
async def handle_set_course_image(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in settings.bot.admin_ids:
        await message.answer("⚠️ Sizda ushbu amalni bajarish huquqi yo'q.")
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "ℹ️ <b>Foydalanish:</b> <code>/set_image &lt;course_id&gt; &lt;rasm_url&gt;</code>\n"
            "<i>Masalan:</i> <code>/set_image 7 https://example.com/banner.png</code>\n"
            "<i>Tozalash uchun:</i> <code>/set_image 7 none</code>",
            parse_mode="HTML",
        )
        return

    try:
        course_id = int(parts[1])
        image_url = parts[2].strip()
        if image_url.lower() in ("none", "clear", "o'chirish", "ochirish"):
            image_url = ""

        service = CourseService()
        result = await service.set_course_image(course_id, image_url)
        await message.answer(
            f"✅ <b>{result['title']}</b> kursi uchun rasm muvaffaqiyatli yangilandi:\n\n"
            f"🖼️ <code>{image_url or '(Tozalandi)'}</code>",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("Rasm URL o'rnatishda xatolik: %s", exc)
        await message.answer(f"❌ Xatolik yuz berdi: {exc}")
