from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.student_kb import get_course_detail_keyboard, get_course_list_keyboard
from db.database import database
from db.repositories.course_repo import CourseRepository

router = Router(name="student_catalog")


@router.message(F.text == "📚 Kurslar katalogi")
async def show_catalog(message: Message) -> None:
    courses = await CourseRepository(database.conn).list_published()
    if not courses:
        await message.answer("Hozircha nashr qilingan kurslar yo'q.")
        return

    await message.answer("Mavjud kurslar:", reply_markup=get_course_list_keyboard(courses))


@router.callback_query(F.data.startswith("course:"))
async def show_course_detail(callback: CallbackQuery) -> None:
    course_id = int(callback.data.split(":")[1])
    course = await CourseRepository(database.conn).get_by_id(course_id)
    if course is None:
        await callback.answer("Kurs topilmadi", show_alert=True)
        return

    text = f"<b>{course.title}</b>\n\nNarxi: {course.base_price:,.0f} so'm"
    await callback.message.answer(text, reply_markup=get_course_detail_keyboard(course.id))
    await callback.answer()
