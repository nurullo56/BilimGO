from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from bot.keyboards.student import get_course_detail_keyboard, get_course_list_keyboard
from core.config import settings
from db.database import database
from db.repositories.course_repo import Course
from db.repositories.user_repo import UserRepository
from db.repositories.waitlist_repo import WaitlistRepository
from services.course_service import CourseService

logger = logging.getLogger(__name__)

router = Router(name="student_catalog")


@router.message(F.text == "📚 Kurslar katalogi")
async def show_catalog(message: Message) -> None:
    course_service = CourseService()
    courses = await course_service.list_published()
    if not courses:
        await message.answer("Hozircha nashr qilingan kurslar yo'q.")
        return

    courses_with_cohort: list[Course] = []
    for c in courses:
        formatted_title = await course_service.get_formatted_title(c)
        courses_with_cohort.append(
            Course(
                id=c.id,
                title=formatted_title,
                owner_node_id=c.owner_node_id,
                base_price=c.base_price,
                status=c.status,
                description=c.description,
                created_at=c.created_at,
                is_waitlist=c.is_waitlist,
            )
        )

    await message.answer("Mavjud kurslar:", reply_markup=get_course_list_keyboard(courses_with_cohort))


@router.callback_query(F.data.startswith("course:"))
async def show_course_detail(callback: CallbackQuery) -> None:
    course_id = int(callback.data.split(":")[1])
    course_service = CourseService()
    course = await course_service.get_by_id(course_id)
    if course is None:
        await callback.answer("Kurs topilmadi", show_alert=True)
        return

    # Agar kurs kutish ro'yxatida (Waitlist) bo'lsa
    if course.is_waitlist:
        conn = database.conn
        user_repo = UserRepository(conn)
        user = await user_repo.get_or_create(telegram_id=callback.from_user.id)
        waitlist_repo = WaitlistRepository(conn)

        is_in = await waitlist_repo.is_in_waitlist(course.id, user.id)
        count = await waitlist_repo.get_count(course.id)

        webapp_url = f"{settings.webapp.base_url}/course/{course.id}?view=course&course_id={course.id}"

        if is_in:
            text = (
                f"🤖 <b>{course.title}</b>\n\n"
                f"✅ <b>Siz allaqachon kutish ro'yxatidasiz!</b>\n\n"
                f"📊 <b>Jami navbatda:</b> {count} kishi\n"
                f"⏳ <b>Holat:</b> Darslar yakuniy bosqichda va tez kunda e'lon qilinadi.\n\n"
                f"Kurs ochilishi bilan bot orqali sizga birinchi bo'lib maxsus taklif bilan xabar yuboramiz! 🚀"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📱 Dastur rejasi (Mini App)",
                            web_app=WebAppInfo(url=webapp_url),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="❌ Navbatdan chiqish",
                            callback_data=f"waitlist:leave:{course.id}",
                        )
                    ],
                ]
            )
        else:
            text = (
                f"🤖 <b>{course.title}</b>\n\n"
                f"⏳ <i>Ushbu amaliy kurs hozirda tayyorlanmoqda va tez kunda platformada e'lon qilinadi!</i>\n\n"
                f"📊 <b>Hozircha:</b> {count} kishi kutish ro'yxatiga yozilgan.\n\n"
                f"Kurs ochilishi bilan birinchilardan bo'lib xabardor bo'lish va maxsus imtiyozlarga ega bo'lish uchun "
                f"navbatga yoziling 👇"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏳ Navbatga yozilish (Waitlist)",
                            callback_data=f"waitlist:join:{course.id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📱 Dastur rejasi (Mini App)",
                            web_app=WebAppInfo(url=webapp_url),
                        )
                    ],
                ]
            )
        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()
        return

    # Oddiy sotuvdagi kurslar uchun
    formatted_title = await course_service.get_formatted_title(course)
    is_konkurs = course.id == 3 or "konkurs" in course.title.lower() or "aksiya" in course.title.lower()
    if is_konkurs:
        text = (
            f"<b>{formatted_title}</b>\n\n"
            f"Narxi: {course.base_price:,.0f} so'm\n\n"
            "⚠️ <b>DIQQAT: KONKURS KURSI VA BOTI SHARTI!</b> ⚠️\n"
            "1️⃣ Konkurs boti va barcha kirish huquqlari <b>aynan hozirgi Telegram akkauntingiz</b> uchun beriladi.\n"
            "2️⃣ Keyinchalik boshqa akkaunt yoki raqamga o'tkazib berish talablari <b>mutlaqo qabul qilinmaydi va tan olinmaydi!</b>\n"
            "3️⃣ Faqat o'zingiz doimiy ishlatadigan, faol akkauntingiz ekanligiga ishonch hosil qiling."
        )
    else:
        text = f"<b>{formatted_title}</b>\n\nNarxi: {course.base_price:,.0f} so'm"
    await callback.message.answer(text, reply_markup=get_course_detail_keyboard(course.id))
    await callback.answer()


@router.callback_query(F.data.startswith("waitlist:join:"))
async def handle_waitlist_join(callback: CallbackQuery) -> None:
    course_id = int(callback.data.split(":")[2])
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=callback.from_user.id)
    waitlist_repo = WaitlistRepository(conn)
    course_repo = CourseService(course_repo=None)

    course = await course_repo.get_by_id(course_id)
    course_title = course.title if course else "AI Kursi"

    await waitlist_repo.join_waitlist(course_id, user.id, user.phone)
    count = await waitlist_repo.get_count(course_id)

    webapp_url = f"{settings.webapp.base_url}/course/{course_id}?view=course&course_id={course_id}"
    updated_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Dastur rejasi (Mini App)",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Navbatdan chiqish",
                    callback_data=f"waitlist:leave:{course_id}",
                )
            ],
        ]
    )

    updated_text = (
        f"🤖 <b>{course_title}</b>\n\n"
        f"✅ <b>Tabriklaymiz, siz kutish ro'yxatiga qo'shildingiz!</b>\n\n"
        f"📊 <b>Sizning navbatingiz:</b> #{count}-o'rin\n"
        f"⏳ <b>Holat:</b> Darslar tez kunda e'lon qilinadi.\n\n"
        f"Kurs ochilishi bilan sizga bot orqali birinchi bo'lib xabar yuboramiz! 🚀"
    )

    try:
        await callback.message.edit_text(updated_text, reply_markup=updated_keyboard)
    except Exception:
        await callback.message.answer(updated_text, reply_markup=updated_keyboard)

    await callback.answer("✅ Navbatga muvaffaqiyatli yozildingiz!", show_alert=True)


@router.callback_query(F.data.startswith("waitlist:leave:"))
async def handle_waitlist_leave(callback: CallbackQuery) -> None:
    course_id = int(callback.data.split(":")[2])
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=callback.from_user.id)
    waitlist_repo = WaitlistRepository(conn)
    course_repo = CourseService(course_repo=None)

    course = await course_repo.get_by_id(course_id)
    course_title = course.title if course else "AI Kursi"

    await waitlist_repo.leave_waitlist(course_id, user.id)
    count = await waitlist_repo.get_count(course_id)

    webapp_url = f"{settings.webapp.base_url}/course/{course_id}?view=course&course_id={course_id}"
    rejoin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏳ Navbatga yozilish (Waitlist)",
                    callback_data=f"waitlist:join:{course_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📱 Dastur rejasi (Mini App)",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ],
        ]
    )

    rejoin_text = (
        f"🤖 <b>{course_title}</b>\n\n"
        f"ℹ️ <i>Siz kutish ro'yxatidan chiqdingiz.</i>\n\n"
        f"📊 <b>Hozircha:</b> {count} kishi navbatda turibdi.\n\n"
        f"Istalgan vaqtda qayta navbatga yozilishingiz mumkin 👇"
    )

    try:
        await callback.message.edit_text(rejoin_text, reply_markup=rejoin_keyboard)
    except Exception:
        await callback.message.answer(rejoin_text, reply_markup=rejoin_keyboard)

    await callback.answer("Navbatdan chiqildi.", show_alert=False)
