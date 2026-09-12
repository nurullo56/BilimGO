from __future__ import annotations

from db.repositories.base import BaseRepository


class LessonViewRepository(BaseRepository):
    async def start_view(
        self, user_id: int, lesson_id: int, delivery_token_id: int | None = None
    ) -> int:
        cursor = await self._conn.execute(
            """
            INSERT INTO lesson_views (user_id, lesson_id, delivery_token_id)
            VALUES (?, ?, ?)
            """,
            (user_id, lesson_id, delivery_token_id),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def update_progress(
        self, view_id: int, watch_duration_sec: int, completion_percent: int
    ) -> None:
        completed_at_clause = ", completed_at = COALESCE(completed_at, datetime('now'))" if completion_percent >= 90 else ""
        await self._conn.execute(
            f"""
            UPDATE lesson_views
            SET watch_duration_sec = MAX(watch_duration_sec, ?),
                completion_percent = MAX(completion_percent, ?){completed_at_clause}
            WHERE id = ?
            """,
            (watch_duration_sec, completion_percent, view_id),
        )
        await self._conn.commit()

    async def student_progress_for_course(self, user_id: int, course_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT l.id AS lesson_id, l.title,
                   COALESCE(MAX(lv.completion_percent), 0) AS completion_percent,
                   COALESCE(MAX(lv.watch_duration_sec), 0) AS watch_duration_sec,
                   MAX(lv.started_at) AS started_at
            FROM lessons l
            LEFT JOIN lesson_views lv ON lv.lesson_id = l.id AND lv.user_id = ?
            WHERE l.course_id = ?
            GROUP BY l.id, l.title, l.order_index
            ORDER BY l.order_index
            """,
            (user_id, course_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def mentor_students_activity(self, cabinet_id: int) -> list[dict]:
        cursor = await self._conn.execute(
            """
            SELECT u.id AS user_id, u.full_name, u.telegram_id,
                   COUNT(lv.id) AS lessons_watched,
                   MAX(lv.started_at) AS last_activity
            FROM cabinet_members cm
            JOIN users u ON u.id = cm.user_id
            LEFT JOIN lesson_views lv ON lv.user_id = u.id
            WHERE cm.cabinet_id = ? AND cm.role_in_cabinet = 'student'
            GROUP BY u.id
            ORDER BY last_activity DESC
            """,
            (cabinet_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
