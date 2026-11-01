from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.student import get_my_courses_progress_keyboard
from db.repositories.user_repo import User
from services.course_service import CourseService

router = Router(name="student_progress")


@router.message(F.text == "🎓 Mening kurslarim")
async def show_my_courses(message: Message, user: User) -> None:
    course_service = CourseService()
    progress_info = await course_service.get_student_courses_progress(user.id)

    if not progress_info["courses"]:
        await message.answer("Siz hali birorta kursga ega emassiz. «📚 Kurslar katalogi» orqali tanlang!")
        return

    keyboard = get_my_courses_progress_keyboard(progress_info["courses"])
    await message.answer(progress_info["summary_text"], reply_markup=keyboard)
