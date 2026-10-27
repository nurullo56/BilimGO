from __future__ import annotations

from typing import Any
from db.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository):
    async def create_feedback(
        self,
        user_id: int,
        rating: int,
        comment: str,
        category: str = "general",
        course_id: int | None = None,
        lesson_id: int | None = None,
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO student_feedbacks (user_id, course_id, lesson_id, rating, category, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, course_id, lesson_id, rating, category, comment),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def list_feedbacks(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT sf.id, sf.user_id, u.telegram_id, u.full_name, sf.course_id,
                   c.title AS course_title, sf.lesson_id, l.title AS lesson_title,
                   sf.rating, sf.category, sf.comment, sf.created_at
            FROM student_feedbacks sf
            JOIN users u ON u.id = sf.user_id
            LEFT JOIN courses c ON c.id = sf.course_id
            LEFT JOIN lessons l ON l.id = sf.lesson_id
            ORDER BY sf.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_feedbacks(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT id, course_id, lesson_id, rating, category, comment, created_at
            FROM student_feedbacks
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
