from __future__ import annotations

from db.repositories.base import BaseRepository


class AccessGrantRepository(BaseRepository):
    async def grant_course_access(
        self, user_id: int, course_id: int, granted_via_sale_id: int
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO access_grants (user_id, course_id, granted_via_sale_id, status)
            VALUES (?, ?, ?, 'active')
            """,
            (user_id, course_id, granted_via_sale_id),
        )
        await self._conn.commit()

    async def has_active_access(self, user_id: int, lesson_id: int, course_id: int) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT 1 FROM access_grants
            WHERE user_id = ?
              AND status = 'active'
              AND (
                  course_id = ?
                  OR (lesson_id IS NOT NULL AND lesson_id = ?)
              )
              AND (expires_at IS NULL OR expires_at > datetime('now'))
            LIMIT 1
            """,
            (user_id, course_id, lesson_id),
        )
        row = await cursor.fetchone()
        return row is not None

    async def count_active_courses(self, user_id: int) -> int:
        """Foydalanuvchining faol ruxsat berilgan kurslari sonini oladi."""
        cursor = await self._conn.execute(
            "SELECT COUNT(DISTINCT course_id) as cnt FROM access_grants WHERE user_id = ? AND status = 'active'",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0

    async def get_latest_active_course_title(self, user_id: int) -> str | None:
        """Foydalanuvchining eng oxirgi faol o'qiyotgan kursi nomini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT c.title
            FROM access_grants ag
            JOIN courses c ON c.id = ag.course_id
            WHERE ag.user_id = ? AND ag.status = 'active'
            ORDER BY ag.id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return row["title"] if row else None

    async def count_cohort_students(self, course_id: int) -> int:
        """Kursning joriy oyidagi talabalar sonini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT COUNT(*) as cnt FROM access_grants 
            WHERE course_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            """,
            (course_id,),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 1

    async def get_user_course_enrollment_time(self, user_id: int, course_id: int) -> str | None:
        """Foydalanuvchining kursga yozilgan vaqtini oladi."""
        cursor = await self._conn.execute(
            "SELECT created_at FROM access_grants WHERE user_id = ? AND course_id = ? LIMIT 1",
            (user_id, course_id),
        )
        row = await cursor.fetchone()
        return row["created_at"] if row else None

    async def get_student_courses_with_progress(self, user_id: int) -> list[dict]:
        """Talabaning barcha faol kurslari va darslar progressini oladi."""
        cursor = await self._conn.execute(
            """
            SELECT c.id, c.title, c.owner_node_id, c.base_price, c.status, c.description, c.created_at, c.is_waitlist,
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
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


