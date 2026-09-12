from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.student_kb import get_my_courses_progress_keyboard
from db.database import database
from db.repositories.user_repo import User

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

    text_lines = ["<b>🎓 Sizning faol kurslaringiz:</b>\n"]
    for row in rows:
        total = row["total_lessons"] or 0
        completed = row["completed_lessons"] or 0
        percent = int((completed / total * 100)) if total > 0 else 0
        text_lines.append(f"• <b>{row['title']}</b>: {completed}/{total} dars ({percent}%)")

    keyboard = get_my_courses_progress_keyboard(rows)
    await message.answer("\n".join(text_lines), reply_markup=keyboard)
