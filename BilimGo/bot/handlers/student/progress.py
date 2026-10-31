from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.student import get_my_courses_progress_keyboard
from db.database import database
from db.repositories.user_repo import User
from services.course_service import CourseService

router = Router(name="student_progress")


@router.message(F.text == "🎓 Mening kurslarim")
async def show_my_courses(message: Message, user: User) -> None:
    cursor = await database.conn.execute(
        """
        SELECT c.id, c.title,
               COUNT(DISTINCT l.id) AS total_lessons,
               COUNT(DISTINCT CASE WHEN lv.completion_percent >= 90 THEN lv.lesson_id END) AS completed_lessons
        FROM access_grants ag
        JOIN courses c ON c.id = ag.course_id
        LEFT JOIN lessons l ON l.course_id = c.id
        LEFT JOIN lesson_views lv ON lv.lesson_id = l.id AND lv.user_id = ag.user_id
        WHERE ag.user_id = ? AND ag.status = 'active'
        GROUP BY c.id, c.title
        ORDER BY ag.id DESC
        """,
        (user.id,),
    )
    rows = await cursor.fetchall()

    if not rows:
        await message.answer("Siz hali birorta kursga ega emassiz. «📚 Kurslar katalogi» orqali tanlang!")
        return

    course_service = CourseService()
    text_lines = ["<b>🎓 Sizning faol kurslaringiz:</b>\n"]
    formatted_rows = []
    for row in rows:
        total = row["total_lessons"] or 0
        completed = row["completed_lessons"] or 0
        percent = int((completed / total * 100)) if total > 0 else 0

        course_obj = await course_service.get_by_id(row["id"])
        formatted_title = await course_service.get_formatted_title(course_obj, user_id=user.id) if course_obj else row["title"]

        text_lines.append(f"• <b>{formatted_title}</b>: {completed}/{total} dars ({percent}%)")
        row_dict = dict(row)
        row_dict["title"] = formatted_title
        formatted_rows.append(row_dict)

    keyboard = get_my_courses_progress_keyboard(formatted_rows)
    await message.answer("\n".join(text_lines), reply_markup=keyboard)
